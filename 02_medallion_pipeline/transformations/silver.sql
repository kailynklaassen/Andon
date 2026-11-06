-- =============================================================================
-- SILVER · cleaned, typed, de-duplicated, conformed
-- =============================================================================
-- What changes between bronze and silver:
--   * explicit types (dates, timestamps, decimals) instead of inferred strings
--   * de-duplication (historian packet resends, EDI shipment resends)
--   * normalized codes (CMMS status arrives as 'Completed', 'COMPLETED', 'completed ')
--   * data-quality EXPECTATIONS: rows that violate a rule are dropped and counted in
--     the pipeline event log — that's your audit trail for "why is this row missing?"
--   * app corrections: tables a person can correct in the app keep the LATEST version of each record
--     (ROW_NUMBER over the key; an approved app correction outranks the source-system row) and carry
--     altered_in_app + app_action_id, so any silver/gold value can be traced to the human decision behind it.
-- Silver datasets are MATERIALIZED VIEWS (batch reads of bronze). On serverless they
-- refresh incrementally when the bronze tables only append.
-- =============================================================================

-- ---------------------------------------------------------------- master data
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.plants
COMMENT 'Manufacturing plants (one row per plant).'
AS SELECT plant_id, plant_name, city, state_country, region,
          CAST(latitude AS DOUBLE) AS latitude, CAST(longitude AS DOUBLE) AS longitude,
          product_family, CAST(pm_compliance_target AS DOUBLE) AS pm_compliance_target,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_plants) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.production_lines
COMMENT 'Production lines per plant with ideal cycle time (seconds per unit).'
AS SELECT line_id, plant_id, line_name, CAST(line_sequence AS INT) AS line_sequence,
          CAST(work_center_count AS INT) AS work_center_count, CAST(ideal_cycle_time_s AS DOUBLE) AS ideal_cycle_time_s,
          CAST(commissioned_year AS INT) AS commissioned_year,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY line_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_production_lines) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.work_centers
COMMENT 'Machines / work centers in process-flow order (process_step 1 = first operation on the line).'
AS SELECT machine_id, line_id, plant_id, CAST(process_step AS INT) AS process_step, machine_type, machine_name,
          oem, model, serial_number, TO_DATE(SUBSTR(install_date, 1, 10)) AS install_date, criticality,
          CAST(pm_interval_days AS INT) AS pm_interval_days,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY machine_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_work_centers) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.warehouses
COMMENT 'Plant warehouses (WH-*) and distribution centers (DC-*).'
AS SELECT warehouse_id, warehouse_name, warehouse_type, plant_id, city, state_country, region,
          CAST(latitude AS DOUBLE) AS latitude, CAST(longitude AS DOUBLE) AS longitude, CAST(capacity_pallets AS INT) AS capacity_pallets,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY warehouse_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_warehouses) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.parts
COMMENT 'Manufactured part master. Each part is produced on exactly one line.'
AS SELECT part_number, part_name, product_family, plant_id, line_id, unit_of_measure,
          CAST(standard_cost_usd AS DECIMAL(12,4)) AS standard_cost_usd, CAST(list_price_usd AS DECIMAL(12,4)) AS list_price_usd,
          CAST(weight_kg AS DOUBLE) AS weight_kg, lifecycle_status
FROM bronze_parts;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.suppliers
COMMENT 'Approved supplier list with contractual quality (PPM) and on-time targets.'
AS SELECT supplier_id, supplier_name, city, country, category, payment_terms,
          CAST(quality_agreement_ppm_limit AS INT) AS quality_agreement_ppm_limit, CAST(on_time_target AS DOUBLE) AS on_time_target,
          CAST(approved_since AS INT) AS approved_since,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY supplier_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_suppliers) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.materials
COMMENT 'Purchased materials and their primary supplier.'
AS SELECT material_id, material_name, category, unit_of_measure, CAST(standard_cost_usd AS DECIMAL(12,4)) AS standard_cost_usd,
          primary_supplier_id, CAST(lead_time_days AS INT) AS lead_time_days,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY material_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_materials) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.bill_of_materials
COMMENT 'Materials consumed per manufactured part.'
AS SELECT part_number, material_id, CAST(quantity_per AS DOUBLE) AS quantity_per FROM bronze_bill_of_materials;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.customers
COMMENT 'Customer master; serving_dc is the distribution center that ships to the customer.'
AS SELECT customer_id, customer_name, industry, region, serving_dc, tier, CAST(otif_target AS DOUBLE) AS otif_target,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_customers) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.carriers
COMMENT 'Freight carriers and their contracted on-time SLA.'
AS SELECT carrier_id, carrier_name, mode, CAST(sla_on_time_target AS DOUBLE) AS sla_on_time_target,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY carrier_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_carriers) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.employees
COMMENT 'Plant workforce (operators, technicians, inspectors, supervisors, planners, warehouse).'
AS SELECT employee_id, employee_name, plant_id, role, shift, certification_level, CAST(hire_date AS DATE) AS hire_date
FROM bronze_employees;

-- ---------------------------------------------------------------- purchasing
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.purchase_orders (
  CONSTRAINT valid_qty EXPECT (order_qty > 0) ON VIOLATION DROP ROW
)
COMMENT 'Purchase order lines to suppliers.'
AS SELECT po_number, CAST(po_line AS INT) AS po_line, supplier_id, material_id, ship_to_plant_id,
          CAST(order_date AS DATE) AS order_date, CAST(promised_date AS DATE) AS promised_date, CAST(order_qty AS INT) AS order_qty,
          CAST(unit_price_usd AS DECIMAL(12,4)) AS unit_price_usd, currency, buyer_id, po_status
FROM bronze_purchase_orders;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.goods_receipts (
  CONSTRAINT rejected_not_above_received EXPECT (rejected_qty <= received_qty) ON VIOLATION DROP ROW
)
COMMENT 'Goods receipts with incoming-inspection outcome. days_late = receipt_date - promised_date (0 if on time).'
AS SELECT receipt_id, po_number, CAST(receipt_date AS DATE) AS receipt_date, CAST(received_qty AS INT) AS received_qty,
          CAST(inspected_qty AS INT) AS inspected_qty, CAST(rejected_qty AS INT) AS rejected_qty, CAST(days_late AS INT) AS days_late,
          inspection_result,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY receipt_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_goods_receipts) WHERE _version = 1;   -- latest version per record (app corrections win)

-- ---------------------------------------------------------------- production (MES / ERP)
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.production_orders
COMMENT 'Manufacturing orders (MO) per line.'
AS SELECT production_order_id, line_id, plant_id, part_number, CAST(scheduled_start AS DATE) AS scheduled_start,
          CAST(scheduled_end AS DATE) AS scheduled_end, CAST(planned_qty AS INT) AS planned_qty,
          CAST(completed_qty AS INT) AS completed_qty, CAST(scrap_qty AS INT) AS scrap_qty, order_status
FROM bronze_production_orders;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.shift_production (
  CONSTRAINT run_within_planned EXPECT (run_minutes BETWEEN 0 AND planned_minutes) ON VIOLATION DROP ROW,
  CONSTRAINT units_balance EXPECT (good_units + scrap_units + rework_units = total_units)
)
COMMENT 'One row per line per shift: planned/run/downtime minutes and unit counts — the inputs to OEE.'
AS SELECT shift_result_id, TO_DATE(SUBSTR(production_date, 1, 10)) AS production_date, shift, plant_id, line_id,
          production_order_id, part_number, CAST(planned_minutes AS DOUBLE) AS planned_minutes,
          CAST(downtime_minutes AS DOUBLE) AS downtime_minutes, CAST(run_minutes AS DOUBLE) AS run_minutes,
          CAST(ideal_cycle_time_s AS DOUBLE) AS ideal_cycle_time_s, CAST(total_units AS BIGINT) AS total_units,
          CAST(scrap_units AS BIGINT) AS scrap_units, CAST(rework_units AS BIGINT) AS rework_units, CAST(good_units AS BIGINT) AS good_units,
          CAST(dt_equipment_failure_min AS DOUBLE) AS dt_equipment_failure_min, CAST(dt_planned_maintenance_min AS DOUBLE) AS dt_planned_maintenance_min,
          CAST(dt_changeover_min AS DOUBLE) AS dt_changeover_min, CAST(dt_material_shortage_min AS DOUBLE) AS dt_material_shortage_min,
          CAST(dt_quality_hold_min AS DOUBLE) AS dt_quality_hold_min, CAST(dt_no_operator_min AS DOUBLE) AS dt_no_operator_min,
          supervisor_id
FROM bronze_shift_production;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.downtime_events (
  CONSTRAINT end_after_start EXPECT (end_ts > start_ts) ON VIOLATION DROP ROW
)
COMMENT 'Downtime events logged in MES. event_scope = Machine (one work center down) or Line (whole line stopped).'
AS SELECT downtime_event_id, plant_id, line_id, machine_id, event_scope, shift,
          CAST(start_ts AS TIMESTAMP) AS start_ts, CAST(end_ts AS TIMESTAMP) AS end_ts, CAST(duration_minutes AS DOUBLE) AS duration_minutes,
          reason_category, reason_detail, related_po_number, related_work_order_id, related_ncr_id, reported_by
FROM bronze_downtime_events;

-- ---------------------------------------------------------------- maintenance (CMMS)
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.maintenance_work_orders
COMMENT 'Preventive / Corrective / Emergency work orders. status normalized to Completed / Deferred.'
AS SELECT work_order_id, machine_id, line_id, plant_id, work_order_type, priority, failure_mode, description,
          CAST(pm_due_date AS DATE) AS pm_due_date, CAST(created_ts AS TIMESTAMP) AS created_ts,
          CAST(started_ts AS TIMESTAMP) AS started_ts, CAST(completed_ts AS TIMESTAMP) AS completed_ts,
          INITCAP(TRIM(status)) AS status,                       -- 'COMPLETED', 'completed ' -> 'Completed'
          technician_id, CAST(labor_hours AS DOUBLE) AS labor_hours,
          CAST(parts_cost_usd AS DECIMAL(12,2)) AS parts_cost_usd, CAST(contractor_cost_usd AS DECIMAL(12,2)) AS contractor_cost_usd,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY work_order_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_maintenance_work_orders) WHERE _version = 1;   -- latest version per record (app corrections win)

-- ---------------------------------------------------------------- quality (QMS)
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.inspections (
  CONSTRAINT defects_within_sample EXPECT (defects_found <= sample_size) ON VIOLATION DROP ROW
)
COMMENT 'In-process inspections per line per shift, with SPC measurement of the line''s critical characteristic.'
AS SELECT inspection_id, inspection_type, CAST(inspection_ts AS TIMESTAMP) AS inspection_ts, plant_id, line_id, shift,
          production_order_part AS part_number, inspector_id, CAST(sample_size AS INT) AS sample_size,
          CAST(defects_found AS INT) AS defects_found, primary_defect_code, characteristic, characteristic_uom,
          CAST(nominal AS DOUBLE) AS nominal, CAST(lower_spec_limit AS DOUBLE) AS lower_spec_limit,
          CAST(upper_spec_limit AS DOUBLE) AS upper_spec_limit, CAST(measured_mean AS DOUBLE) AS measured_mean,
          CAST(measured_std_dev AS DOUBLE) AS measured_std_dev, result
FROM bronze_inspections;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.nonconformances
COMMENT 'Nonconformance reports (NCRs) from in-process inspection, incoming inspection, and customers.'
AS SELECT ncr_id, CAST(opened_date AS DATE) AS opened_date, source, plant_id, line_id, machine_id, part_number, material_id,
          supplier_id, defect_code, severity, CAST(qty_affected AS INT) AS qty_affected, disposition,
          CAST(cost_of_poor_quality_usd AS DECIMAL(14,2)) AS cost_of_poor_quality_usd, inspection_id, capa_id, status,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY ncr_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_nonconformances) WHERE _version = 1;   -- latest version per record (app corrections win)

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.capa
COMMENT 'Corrective and preventive actions (CAPA), including supplier SCARs.'
AS SELECT capa_id, title, root_cause_category, plant_id, supplier_id, CAST(opened_date AS DATE) AS opened_date,
          CAST(due_date AS DATE) AS due_date, CAST(closed_date AS DATE) AS closed_date, status, owner_id,
          CAST(effectiveness_verified AS BOOLEAN) AS effectiveness_verified,
          COALESCE(_altered_in_app, false) AS altered_in_app, _app_action_id AS app_action_id
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY capa_id ORDER BY _app_approved_ts DESC NULLS LAST, _ingested_at DESC) AS _version
      FROM bronze_capa) WHERE _version = 1;   -- latest version per record (app corrections win)

-- ---------------------------------------------------------------- IoT historian
-- The historian resends ~0.4% of packets and drops ~0.2% of vibration values.
-- De-duplicate on (machine_id, reading_ts) and drop readings with no vibration.
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.machine_telemetry (
  CONSTRAINT vibration_present EXPECT (vibration_mm_s IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT vibration_physical EXPECT (vibration_mm_s BETWEEN 0 AND 50) ON VIOLATION DROP ROW
)
COMMENT 'Hourly machine sensor readings, de-duplicated. machine_state: RUNNING, IDLE (not scheduled), STOPPED (line stopped), DOWN (machine failed / in maintenance).'
CLUSTER BY (machine_id, reading_ts)
AS SELECT machine_id, reading_ts, machine_state, temperature_c, vibration_mm_s, motor_load_pct, power_kw
FROM (
  SELECT machine_id, CAST(reading_ts AS TIMESTAMP) AS reading_ts, machine_state,
         CAST(temperature_c AS DOUBLE) AS temperature_c, CAST(vibration_mm_s AS DOUBLE) AS vibration_mm_s,
         CAST(motor_load_pct AS DOUBLE) AS motor_load_pct, CAST(power_kw AS DOUBLE) AS power_kw,
         ROW_NUMBER() OVER (PARTITION BY machine_id, reading_ts ORDER BY _ingested_at DESC) AS rn
  FROM bronze_machine_telemetry
) WHERE rn = 1;

-- ---------------------------------------------------------------- warehousing & fulfillment (WMS / ERP)
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.inventory_snapshots
COMMENT 'Daily on-hand inventory by warehouse and item (finished goods at DCs, raw materials at plant warehouses).'
AS SELECT CAST(snapshot_date AS DATE) AS snapshot_date, warehouse_id, item_id, item_type,
          CAST(on_hand_qty AS DOUBLE) AS on_hand_qty, CAST(allocated_qty AS DOUBLE) AS allocated_qty,
          CAST(safety_stock_qty AS DOUBLE) AS safety_stock_qty, CAST(unit_cost_usd AS DOUBLE) AS unit_cost_usd
FROM bronze_inventory_snapshots;

CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.sales_orders
COMMENT 'Customer sales order lines.'
AS SELECT sales_order_id, CAST(order_line AS INT) AS order_line, CAST(order_date AS DATE) AS order_date, customer_id, part_number,
          CAST(order_qty AS INT) AS order_qty, CAST(unit_price_usd AS DECIMAL(12,4)) AS unit_price_usd,
          CAST(requested_delivery_date AS DATE) AS requested_delivery_date, fulfillment_dc, order_channel
FROM bronze_sales_orders;

-- EDI resends create duplicate shipment rows — keep one per shipment_id.
CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${silver_schema}.shipments
COMMENT 'Outbound customer shipments, de-duplicated. carrier_due_date = ship_date + planned_transit_days.'
AS SELECT shipment_id, sales_order_id, ship_from_warehouse_id, carrier_id, ship_date, planned_transit_days, carrier_due_date,
          promised_delivery_date, delivered_date, shipped_qty, freight_cost_usd, tracking_number, shipment_status
FROM (
  SELECT shipment_id, sales_order_id, ship_from_warehouse_id, carrier_id, CAST(ship_date AS DATE) AS ship_date,
         CAST(planned_transit_days AS INT) AS planned_transit_days, CAST(carrier_due_date AS DATE) AS carrier_due_date,
         CAST(promised_delivery_date AS DATE) AS promised_delivery_date, CAST(delivered_date AS DATE) AS delivered_date,
         CAST(shipped_qty AS INT) AS shipped_qty, CAST(freight_cost_usd AS DECIMAL(12,2)) AS freight_cost_usd,
         CAST(tracking_number AS STRING) AS tracking_number, shipment_status,
         ROW_NUMBER() OVER (PARTITION BY shipment_id ORDER BY _ingested_at DESC) AS rn
  FROM bronze_shipments
) WHERE rn = 1;
