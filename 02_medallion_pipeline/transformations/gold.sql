-- =============================================================================
-- GOLD · business-ready materialized views (what Genie and the app read)
-- =============================================================================
-- Design rules for an AGENT-ready gold layer:
--   1. Denormalize the dimensions people filter by (plant, line, machine, supplier,
--      customer, carrier) onto each fact. Genie writes better SQL with fewer joins.
--   2. Pre-compute the flags and components behind every KPI (is_on_time, run
--      minutes, ideal minutes...) so the metric views only SUM/COUNT. Ratios are then
--      re-aggregated correctly at any grain (never average a percentage).
--   3. Add the fiscal calendar (FY starts Oct 1) — "Q3" means Apr-Jun at KK's Parts.
--   4. Comment every table. Comments flow into Unity Catalog and into Genie.
-- One fact table per KPI group; each one becomes the single source of one metric view.
-- =============================================================================

-- ---------------------------------------------------------------- dimensions
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_plant
COMMENT 'Plant dimension: location (lat/long for maps), region, product family, PM compliance target.'
AS SELECT * FROM ${catalog}.${silver_schema}.plants;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_production_line
COMMENT 'Production line dimension with its plant. Physical hierarchy: plant -> line -> work center.'
AS SELECT l.line_id, l.line_name, l.line_sequence, l.work_center_count, l.ideal_cycle_time_s, l.commissioned_year,
          p.plant_id, p.plant_name, p.region, p.product_family
FROM ${catalog}.${silver_schema}.production_lines l JOIN ${catalog}.${silver_schema}.plants p USING (plant_id);

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_work_center
COMMENT 'Machine / work center dimension in process-flow order (process_step) with line and plant. criticality A = bottleneck, no redundancy.'
AS SELECT w.machine_id, w.machine_name, w.machine_type, w.process_step, w.oem, w.model, w.serial_number, w.install_date,
          w.criticality, w.pm_interval_days, l.line_id, l.line_name, p.plant_id, p.plant_name, p.region,
          p.latitude, p.longitude
FROM ${catalog}.${silver_schema}.work_centers w
JOIN ${catalog}.${silver_schema}.production_lines l USING (line_id)
JOIN ${catalog}.${silver_schema}.plants p ON w.plant_id = p.plant_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_part
COMMENT 'Manufactured part (finished good) dimension with producing line and plant.'
AS SELECT pt.*, l.line_name, p.plant_name
FROM ${catalog}.${silver_schema}.parts pt
JOIN ${catalog}.${silver_schema}.production_lines l USING (line_id)
JOIN ${catalog}.${silver_schema}.plants p ON pt.plant_id = p.plant_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_supplier
COMMENT 'Supplier dimension with contractual PPM limit and on-time target.'
AS SELECT * FROM ${catalog}.${silver_schema}.suppliers;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_material
COMMENT 'Purchased material dimension with primary supplier name.'
AS SELECT m.*, s.supplier_name AS primary_supplier_name
FROM ${catalog}.${silver_schema}.materials m LEFT JOIN ${catalog}.${silver_schema}.suppliers s ON m.primary_supplier_id = s.supplier_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_warehouse
COMMENT 'Warehouse dimension: plant warehouses (WH-*) and distribution centers (DC-*), with lat/long.'
AS SELECT * FROM ${catalog}.${silver_schema}.warehouses;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_customer
COMMENT 'Customer dimension: industry, region, tier (Strategic / Key / Standard), serving DC, OTIF target.'
AS SELECT * FROM ${catalog}.${silver_schema}.customers;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.dim_carrier
COMMENT 'Carrier dimension with contracted on-time SLA.'
AS SELECT * FROM ${catalog}.${silver_schema}.carriers;

-- ---------------------------------------------------------------- PRODUCTION domain
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_shift_production
COMMENT 'Grain: one line x one shift x one day. OEE components: availability = run/planned minutes; performance = ideal_minutes/run_minutes; quality = good/total units. OEE = availability x performance x quality. Downtime minutes split by MES reason code.'
CLUSTER BY (production_date, line_id)
AS SELECT
  s.shift_result_id, s.production_date,
  DATE_TRUNC('MONTH', s.production_date) AS production_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(s.production_date, 3)) AS STRING), 2)) AS fiscal_year,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(s.production_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(s.production_date, 3))) AS fiscal_quarter,
  s.shift, l.plant_id, l.plant_name, l.region, l.product_family, s.line_id, l.line_name,
  s.production_order_id, s.part_number, pt.part_name,
  s.planned_minutes, s.run_minutes, s.downtime_minutes,
  s.total_units * s.ideal_cycle_time_s / 60.0 AS ideal_minutes,       -- time the units "should" have taken
  s.total_units, s.good_units, s.scrap_units, s.rework_units,
  s.dt_equipment_failure_min, s.dt_planned_maintenance_min, s.dt_changeover_min,
  s.dt_material_shortage_min, s.dt_quality_hold_min, s.dt_no_operator_min,
  CAST(s.good_units AS DOUBLE) * pt.standard_cost_usd AS good_output_value_usd,
  CAST(s.scrap_units AS DOUBLE) * pt.standard_cost_usd AS scrap_cost_usd
FROM ${catalog}.${silver_schema}.shift_production s
JOIN ${catalog}.${gold_schema}.dim_production_line l ON s.line_id = l.line_id
LEFT JOIN ${catalog}.${silver_schema}.parts pt ON s.part_number = pt.part_number;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_downtime_event
COMMENT 'Grain: one downtime event. reason_category is one of: Equipment Failure, Planned Maintenance, Changeover, Material Shortage, Quality Hold, No Operator. Unplanned = everything except Planned Maintenance and Changeover.'
AS SELECT d.downtime_event_id, d.start_ts, d.end_ts, CAST(d.start_ts AS DATE) AS event_date,
  DATE_TRUNC('MONTH', d.start_ts) AS event_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(d.start_ts, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(d.start_ts, 3))) AS fiscal_quarter,
  d.shift, d.event_scope, d.plant_id, w.plant_name, d.line_id, w.line_name, d.machine_id, w.machine_name, w.machine_type, w.criticality,
  d.reason_category, d.reason_detail,
  d.reason_category NOT IN ('Planned Maintenance', 'Changeover') AS is_unplanned,
  d.duration_minutes, d.duration_minutes / 60.0 AS duration_hours,
  d.related_work_order_id, d.related_po_number, d.related_ncr_id, d.reported_by
FROM ${catalog}.${silver_schema}.downtime_events d
LEFT JOIN ${catalog}.${gold_schema}.dim_work_center w ON d.machine_id = w.machine_id;

-- ---------------------------------------------------------------- QUALITY domain
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_quality_inspection
COMMENT 'Grain: one in-process inspection (one per line per shift). defect_rate = defects_found / sample_size. cpk = min(USL-mean, mean-LSL) / (3*std_dev); Cpk < 1.33 = not capable.'
AS SELECT i.inspection_id, i.inspection_ts, CAST(i.inspection_ts AS DATE) AS inspection_date,
  DATE_TRUNC('MONTH', i.inspection_ts) AS inspection_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(i.inspection_ts, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(i.inspection_ts, 3))) AS fiscal_quarter,
  i.shift, i.plant_id, l.plant_name, i.line_id, l.line_name, i.part_number, i.inspector_id,
  i.sample_size, i.defects_found, i.primary_defect_code, i.result, i.result = 'PASS' AS is_pass,
  i.characteristic, i.characteristic_uom, i.nominal, i.lower_spec_limit, i.upper_spec_limit, i.measured_mean, i.measured_std_dev,
  LEAST(i.upper_spec_limit - i.measured_mean, i.measured_mean - i.lower_spec_limit) / NULLIF(3 * i.measured_std_dev, 0) AS cpk
FROM ${catalog}.${silver_schema}.inspections i
JOIN ${catalog}.${gold_schema}.dim_production_line l ON i.line_id = l.line_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_nonconformance
COMMENT 'Grain: one NCR. source: In-Process | Incoming Inspection | Customer Complaint. COPQ = cost_of_poor_quality_usd. Linked to its CAPA (if any) and the CAPA status.'
AS SELECT n.ncr_id, n.opened_date, DATE_TRUNC('MONTH', n.opened_date) AS opened_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(n.opened_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(n.opened_date, 3))) AS fiscal_quarter,
  n.source, n.plant_id, p.plant_name, n.line_id, n.machine_id, n.part_number, n.material_id, m.material_name,
  n.supplier_id, s.supplier_name, n.defect_code, n.severity, n.qty_affected, n.disposition, n.cost_of_poor_quality_usd,
  n.status AS ncr_status, n.capa_id, c.title AS capa_title, c.status AS capa_status, c.due_date AS capa_due_date
FROM ${catalog}.${silver_schema}.nonconformances n
JOIN ${catalog}.${silver_schema}.plants p ON n.plant_id = p.plant_id
LEFT JOIN ${catalog}.${silver_schema}.materials m ON n.material_id = m.material_id
LEFT JOIN ${catalog}.${silver_schema}.suppliers s ON n.supplier_id = s.supplier_id
LEFT JOIN ${catalog}.${silver_schema}.capa c ON n.capa_id = c.capa_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_capa
COMMENT 'Grain: one CAPA (corrective / preventive action, incl. supplier SCARs). Status: Open | In Progress | Overdue | Closed. linked_ncr_count / linked_copq_usd roll up the NCRs that point to it.'
AS SELECT c.*, p.plant_name, s.supplier_name,
  COALESCE(n.linked_ncr_count, 0) AS linked_ncr_count, COALESCE(n.linked_copq_usd, 0) AS linked_copq_usd
FROM ${catalog}.${silver_schema}.capa c
JOIN ${catalog}.${silver_schema}.plants p ON c.plant_id = p.plant_id
LEFT JOIN ${catalog}.${silver_schema}.suppliers s ON c.supplier_id = s.supplier_id
LEFT JOIN (SELECT capa_id, COUNT(*) AS linked_ncr_count, SUM(cost_of_poor_quality_usd) AS linked_copq_usd
           FROM ${catalog}.${silver_schema}.nonconformances WHERE capa_id IS NOT NULL GROUP BY capa_id) n
  ON c.capa_id = n.capa_id;

-- ---------------------------------------------------------------- MAINTENANCE domain
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_maintenance_work_order
COMMENT 'Grain: one CMMS work order. Types: Preventive | Corrective | Emergency. is_breakdown = Corrective or Emergency. PM compliance = completed preventive / all preventive due. repair_hours = completed_ts - created_ts.'
AS SELECT wo.work_order_id, wo.created_ts, CAST(wo.created_ts AS DATE) AS created_date, DATE_TRUNC('MONTH', wo.created_ts) AS created_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(wo.created_ts, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(wo.created_ts, 3))) AS fiscal_quarter,
  wo.plant_id, w.plant_name, wo.line_id, w.line_name, wo.machine_id, w.machine_name, w.machine_type, w.oem, w.criticality,
  wo.work_order_type, wo.priority, wo.failure_mode, wo.description, wo.status, wo.pm_due_date,
  wo.work_order_type = 'Preventive' AS is_preventive,
  wo.work_order_type IN ('Corrective', 'Emergency') AS is_breakdown,
  wo.work_order_type = 'Preventive' AND wo.status = 'Completed' AS is_pm_completed,
  wo.work_order_type = 'Preventive' AND wo.status = 'Deferred' AS is_pm_deferred,
  wo.started_ts, wo.completed_ts,
  (UNIX_TIMESTAMP(wo.completed_ts) - UNIX_TIMESTAMP(wo.created_ts)) / 3600.0 AS repair_hours,
  wo.technician_id, wo.labor_hours, wo.parts_cost_usd, wo.contractor_cost_usd,
  wo.parts_cost_usd + wo.contractor_cost_usd AS total_cost_usd
FROM ${catalog}.${silver_schema}.maintenance_work_orders wo
JOIN ${catalog}.${gold_schema}.dim_work_center w ON wo.machine_id = w.machine_id;

-- Daily condition-monitoring roll-up per machine (what a reliability engineer trends).
-- 4.5 mm/s = ISO 10816 zone C/D boundary for this machine class AND the OEM spindle limit
-- in the Hartwell manual — hours above it are the early-warning signal.
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_machine_health_daily
COMMENT 'Grain: one machine x one day. Running-only sensor averages, hours above 4.5 mm/s vibration (OEM / ISO 10816 zone C-D limit), hours by machine_state, and breakdowns started that day.'
CLUSTER BY (reading_date, machine_id)
AS WITH t AS (
  SELECT machine_id, CAST(reading_ts AS DATE) AS reading_date,
    AVG(vibration_mm_s) FILTER (WHERE machine_state = 'RUNNING') AS avg_vibration_mm_s,
    MAX(vibration_mm_s) FILTER (WHERE machine_state = 'RUNNING') AS max_vibration_mm_s,
    AVG(temperature_c)  FILTER (WHERE machine_state = 'RUNNING') AS avg_temperature_c,
    MAX(temperature_c)  FILTER (WHERE machine_state = 'RUNNING') AS max_temperature_c,
    AVG(motor_load_pct) FILTER (WHERE machine_state = 'RUNNING') AS avg_motor_load_pct,
    SUM(power_kw) AS energy_kwh,
    COUNT_IF(machine_state = 'RUNNING') AS running_hours,
    COUNT_IF(machine_state = 'DOWN')    AS down_hours,
    COUNT_IF(machine_state = 'STOPPED') AS stopped_hours,
    COUNT_IF(machine_state = 'IDLE')    AS idle_hours,
    COUNT_IF(machine_state = 'RUNNING' AND vibration_mm_s > 4.5) AS hours_above_4_5_mm_s
  FROM ${catalog}.${silver_schema}.machine_telemetry
  GROUP BY machine_id, CAST(reading_ts AS DATE)
), b AS (
  SELECT machine_id, CAST(created_ts AS DATE) AS d, COUNT(*) AS breakdowns
  FROM ${catalog}.${silver_schema}.maintenance_work_orders
  WHERE work_order_type IN ('Corrective', 'Emergency') GROUP BY ALL
)
SELECT t.reading_date, DATE_TRUNC('MONTH', t.reading_date) AS reading_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(t.reading_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(t.reading_date, 3))) AS fiscal_quarter,
  w.plant_id, w.plant_name, w.line_id, w.line_name, t.machine_id, w.machine_name, w.machine_type, w.oem, w.criticality,
  t.avg_vibration_mm_s, t.max_vibration_mm_s, t.avg_temperature_c, t.max_temperature_c, t.avg_motor_load_pct, t.energy_kwh,
  t.running_hours, t.down_hours, t.stopped_hours, t.idle_hours, t.hours_above_4_5_mm_s,
  COALESCE(b.breakdowns, 0) AS breakdowns
FROM t JOIN ${catalog}.${gold_schema}.dim_work_center w ON t.machine_id = w.machine_id
LEFT JOIN b ON t.machine_id = b.machine_id AND t.reading_date = b.d;

-- ---------------------------------------------------------------- SUPPLY CHAIN domain
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_supplier_receipt
COMMENT 'Grain: one PO line with its goods receipt. is_on_time = days_late = 0. Supplier PPM = SUM(rejected_qty) / SUM(received_qty) * 1e6. Open POs (not yet received) have NULL receipt columns.'
AS SELECT po.po_number, po.order_date, po.promised_date, r.receipt_date,
  DATE_TRUNC('MONTH', po.promised_date) AS promised_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(po.promised_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(po.promised_date, 3))) AS fiscal_quarter,
  po.supplier_id, s.supplier_name, s.country AS supplier_country, s.category AS supplier_category,
  s.quality_agreement_ppm_limit, po.material_id, m.material_name, po.ship_to_plant_id AS plant_id, p.plant_name,
  po.order_qty, po.unit_price_usd, po.order_qty * po.unit_price_usd AS po_value_usd, po.po_status,
  r.received_qty, r.inspected_qty, r.rejected_qty, r.days_late, r.inspection_result,
  r.receipt_id IS NOT NULL AS is_received, r.days_late = 0 AS is_on_time
FROM ${catalog}.${silver_schema}.purchase_orders po
JOIN ${catalog}.${silver_schema}.suppliers s ON po.supplier_id = s.supplier_id
JOIN ${catalog}.${silver_schema}.materials m ON po.material_id = m.material_id
JOIN ${catalog}.${silver_schema}.plants p ON po.ship_to_plant_id = p.plant_id
LEFT JOIN ${catalog}.${silver_schema}.goods_receipts r ON po.po_number = r.po_number;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_inventory_daily
COMMENT 'Grain: one warehouse x one item x one day. is_stockout = on_hand < allocated. is_below_safety_stock = on_hand < safety_stock. inventory_value_usd = on_hand x unit cost.'
CLUSTER BY (snapshot_date, warehouse_id)
AS SELECT i.snapshot_date, DATE_TRUNC('MONTH', i.snapshot_date) AS snapshot_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(i.snapshot_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(i.snapshot_date, 3))) AS fiscal_quarter,
  i.warehouse_id, w.warehouse_name, w.warehouse_type, w.region, i.item_id, i.item_type,
  COALESCE(pt.part_name, m.material_name) AS item_name, COALESCE(pt.product_family, m.category) AS item_category,
  m.primary_supplier_id AS supplier_id,
  i.on_hand_qty, i.allocated_qty, i.safety_stock_qty, i.unit_cost_usd, i.on_hand_qty * i.unit_cost_usd AS inventory_value_usd,
  i.on_hand_qty < i.allocated_qty AS is_stockout, i.on_hand_qty < i.safety_stock_qty AS is_below_safety_stock
FROM ${catalog}.${silver_schema}.inventory_snapshots i
JOIN ${catalog}.${silver_schema}.warehouses w ON i.warehouse_id = w.warehouse_id
LEFT JOIN ${catalog}.${silver_schema}.parts pt ON i.item_id = pt.part_number
LEFT JOIN ${catalog}.${silver_schema}.materials m ON i.item_id = m.material_id;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.fact_shipment
COMMENT 'Grain: one outbound shipment with its sales order line. is_carrier_on_time = delivered by carrier_due_date (carrier SLA). is_on_time_to_customer = delivered by customer requested date. is_otif = on time AND full quantity. In-transit shipments have NULL delivered_date and NULL flags.'
AS SELECT sh.shipment_id, sh.sales_order_id, so.order_date, sh.ship_date, sh.carrier_due_date, sh.promised_delivery_date, sh.delivered_date,
  DATE_TRUNC('MONTH', sh.ship_date) AS ship_month,
  CONCAT('FY', RIGHT(CAST(YEAR(ADD_MONTHS(sh.ship_date, 3)) AS STRING), 2), ' Q', QUARTER(ADD_MONTHS(sh.ship_date, 3))) AS fiscal_quarter,
  sh.ship_from_warehouse_id AS warehouse_id, w.warehouse_name, sh.carrier_id, c.carrier_name, c.mode AS carrier_mode, c.sla_on_time_target,
  so.customer_id, cu.customer_name, cu.tier AS customer_tier, cu.industry AS customer_industry, cu.region AS customer_region,
  so.part_number, pt.part_name, pt.product_family, pt.plant_id AS producing_plant_id,
  so.order_qty, sh.shipped_qty, so.order_qty * so.unit_price_usd AS order_value_usd, sh.freight_cost_usd,
  sh.planned_transit_days, DATEDIFF(sh.delivered_date, sh.ship_date) AS actual_transit_days,
  DATEDIFF(sh.ship_date, so.order_date) AS order_to_ship_days,
  sh.shipment_status,
  CASE WHEN sh.delivered_date IS NOT NULL THEN sh.delivered_date <= sh.carrier_due_date END AS is_carrier_on_time,
  CASE WHEN sh.delivered_date IS NOT NULL THEN sh.delivered_date <= sh.promised_delivery_date END AS is_on_time_to_customer,
  sh.shipped_qty >= so.order_qty AS is_in_full,
  CASE WHEN sh.delivered_date IS NOT NULL THEN sh.delivered_date <= sh.promised_delivery_date AND sh.shipped_qty >= so.order_qty END AS is_otif
FROM ${catalog}.${silver_schema}.shipments sh
JOIN ${catalog}.${silver_schema}.sales_orders so ON sh.sales_order_id = so.sales_order_id
JOIN ${catalog}.${silver_schema}.customers cu ON so.customer_id = cu.customer_id
JOIN ${catalog}.${silver_schema}.carriers c ON sh.carrier_id = c.carrier_id
JOIN ${catalog}.${silver_schema}.warehouses w ON sh.ship_from_warehouse_id = w.warehouse_id
LEFT JOIN ${catalog}.${silver_schema}.parts pt ON so.part_number = pt.part_number;
