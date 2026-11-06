import os, yaml
# Dev helper: regenerates metric_views/*.yaml. Edit the definitions here or edit the YAML directly.
PCT={"type":"percentage","decimal_places":{"type":"max","places":1}}
USD={"type":"currency","currency_code":"USD","decimal_places":{"type":"max","places":0}}
def D(name, expr, comment, syn=None, dn=None):
    d={"name":name,"expr":expr,"comment":comment,"display_name":dn or name}
    if syn: d["synonyms"]=syn
    return d
def M(name, expr, comment, syn=None, fmt=None, dn=None):
    d={"name":name,"expr":expr,"comment":comment,"display_name":dn or name}
    if syn: d["synonyms"]=syn
    if fmt: d["format"]=fmt
    return d
def time_dims(date_col, month_col, label):
    return [D(f"{label} Date", date_col, f"Calendar date of the {label.lower()}.", [f"{label.lower()} day","date"]),
            D(f"{label} Month", month_col, f"First day of the calendar month of the {label.lower()}.", ["month"]),
            D("Fiscal Quarter","fiscal_quarter","KK's Parts fiscal quarter, e.g. 'FY26 Q3'. Fiscal year starts Oct 1: Q1 Oct-Dec, Q2 Jan-Mar, Q3 Apr-Jun, Q4 Jul-Sep.",["quarter","fiscal period","FQ"])]
PLANT=[D("Plant ID","plant_id","Plant code: CLB Columbus, GVL Greenville, MTY Monterrey, WRO Wroclaw, PNQ Pune.",["site code","plant code"]),
       D("Plant Name","plant_name","Plant name, e.g. 'Greenville Drivetrain Plant'.",["plant","site","factory","facility"])]
LINE=[D("Line ID","line_id","Production line code, e.g. GVL-L3.",["line code"]),
      D("Line Name","line_name","Production line name, e.g. 'Gearbox Assembly'.",["line","production line","cell"])]
MACH=[D("Machine ID","machine_id","Work center / machine code '<LINE>-WC<nn>', e.g. GVL-L3-WC01.",["work center","asset","asset id","equipment id"]),
      D("Machine Name","machine_name","Machine name, e.g. 'CNC Horizontal Machining Center #1'.",["machine","equipment","asset name"]),
      D("Machine Type","machine_type","Machine type code, e.g. CNC_MACHINING_CENTER, CRIMP_PRESS.",["equipment type","asset class"]),
      D("Criticality","criticality","Asset criticality: A = bottleneck/no redundancy, B, C.",["asset criticality","criticality class"])]
views={}
G="{catalog}.{gold_schema}"
views["production_oee_metrics"]=dict(version=1.1, source=f"{G}.fact_shift_production",
 comment="Production & OEE KPIs at line-shift grain for KK's Parts. OEE = Availability x Performance x Quality. Use for output, OEE, scrap, and downtime-minutes-by-reason questions by plant, line, shift, part, and period.",
 dimensions=time_dims("production_date","production_month","Production")+[D("Shift","shift","Shift: A 06:00-14:00, B 14:00-22:00, C 22:00-06:00 (night).",["crew","shift code"])]+PLANT+[
   D("Region","region","Plant region: North America, Europe, Asia Pacific.",["geography"]),
   D("Product Family","product_family","Product family made at the plant, e.g. 'Gears & Drivetrain'.",["product line","family"])]+LINE+[
   D("Part Number","part_number","Finished-good part number being produced.",["part","SKU","item"]),
   D("Part Name","part_name","Finished-good part description.",["product","part description"])],
 measures=[
   M("Shifts Run","COUNT(1)","Number of line-shifts scheduled.",["shift count"]),
   M("Planned Minutes","SUM(planned_minutes)","Planned production time in minutes (450 per shift)."),
   M("Run Minutes","SUM(run_minutes)","Minutes the line actually ran (planned minus downtime).",["uptime minutes","operating time"]),
   M("Downtime Minutes","SUM(downtime_minutes)","Minutes the line was stopped for any reason.",["lost minutes"]),
   M("Downtime Hours","SUM(downtime_minutes) / 60.0","Hours the line was stopped for any reason.",["lost hours","stoppage hours"]),
   M("Ideal Minutes","SUM(ideal_minutes)","Minutes the produced units would take at ideal cycle time."),
   M("Total Units","SUM(total_units)","All units produced (good + scrap + rework).",["output","units produced","throughput"]),
   M("Good Units","SUM(good_units)","Units that passed first time.",["good output","good parts"]),
   M("Scrap Units","SUM(scrap_units)","Units scrapped.",["scrap","rejects"]),
   M("Rework Units","SUM(rework_units)","Units sent to rework."),
   M("Availability","MEASURE(`Run Minutes`) / MEASURE(`Planned Minutes`)","OEE availability = run minutes / planned minutes.",["uptime %","availability rate"],PCT),
   M("Performance","MEASURE(`Ideal Minutes`) / MEASURE(`Run Minutes`)","OEE performance = ideal minutes / run minutes (speed losses, minor stops).",["performance rate","speed efficiency"],PCT),
   M("Quality Rate","MEASURE(`Good Units`) / MEASURE(`Total Units`)","OEE quality = good units / total units. Same as first pass yield (FPY).",["first pass yield","FPY","yield"],PCT),
   M("OEE","MEASURE(`Availability`) * MEASURE(`Performance`) * MEASURE(`Quality Rate`)","Overall Equipment Effectiveness = Availability x Performance x Quality. Corporate target 85%.",["overall equipment effectiveness","line efficiency"],PCT),
   M("Scrap Rate","MEASURE(`Scrap Units`) / MEASURE(`Total Units`)","Scrap units / total units.",["scrap %"],PCT),
   M("Scrap Cost USD","SUM(scrap_cost_usd)","Scrapped units valued at standard cost, USD.",["cost of scrap"],USD),
   M("Good Output Value USD","SUM(good_output_value_usd)","Good units valued at standard cost, USD.",["production value"],USD),
   M("Equipment Failure Downtime Hours","SUM(dt_equipment_failure_min) / 60.0","Downtime hours coded Equipment Failure (breakdowns).",["breakdown hours","unplanned maintenance hours"]),
   M("Planned Maintenance Downtime Hours","SUM(dt_planned_maintenance_min) / 60.0","Downtime hours coded Planned Maintenance (PMs).",["PM hours"]),
   M("Changeover Downtime Hours","SUM(dt_changeover_min) / 60.0","Downtime hours coded Changeover.",["setup hours","changeover hours"]),
   M("Material Shortage Downtime Hours","SUM(dt_material_shortage_min) / 60.0","Downtime hours coded Material Shortage (line starved of parts).",["starved hours","shortage hours"]),
   M("Quality Hold Downtime Hours","SUM(dt_quality_hold_min) / 60.0","Downtime hours coded Quality Hold (containment).",["quality hold hours"]),
   M("No Operator Downtime Hours","SUM(dt_no_operator_min) / 60.0","Downtime hours coded No Operator (staffing).",["staffing downtime"]),
 ])
views["production_downtime_metrics"]=dict(version=1.1, source=f"{G}.fact_downtime_event",
 comment="Downtime event KPIs (one row per MES downtime event) for KK's Parts. Use to count and rank stoppages by reason code, machine, line, plant, and shift.",
 dimensions=time_dims("event_date","event_month","Event")+[D("Shift","shift","Shift the event started in: A, B, C (night).",["crew"]),
   D("Event Scope","event_scope","Machine = one work center down; Line = whole line stopped.",["scope"])]+PLANT+LINE+MACH+[
   D("Reason Category","reason_category","MES downtime reason code: Equipment Failure, Planned Maintenance, Changeover, Material Shortage, Quality Hold, No Operator.",["downtime reason","reason code","stop reason","cause"]),
   D("Reason Detail","reason_detail","Free-text detail: failure mode, material awaited, or changeover target.",["failure mode","detail"]),
   D("Is Unplanned","is_unplanned","True for unplanned stops (everything except Planned Maintenance and Changeover).",["unplanned"])],
 measures=[
   M("Downtime Events","COUNT(1)","Number of downtime events.",["stoppages","stops","events"]),
   M("Downtime Hours","SUM(duration_hours)","Total event duration in hours.",["lost hours"]),
   M("Average Event Minutes","AVG(duration_minutes)","Average event duration in minutes.",["mean stop duration"]),
   M("Unplanned Downtime Hours","SUM(duration_hours) FILTER (WHERE is_unplanned)","Hours of unplanned downtime.",["unplanned hours"]),
   M("Equipment Failure Events","COUNT(1) FILTER (WHERE reason_category = 'Equipment Failure')","Number of breakdown events.",["breakdowns","failures"]),
   M("Material Shortage Events","COUNT(1) FILTER (WHERE reason_category = 'Material Shortage')","Number of line stops waiting on material.",["shortages"]),
 ])
views["quality_inspection_metrics"]=dict(version=1.1, source=f"{G}.fact_quality_inspection",
 comment="In-process inspection and SPC KPIs (one inspection per line per shift). Use for defect rate, inspection pass/fail, and process capability (Cpk) by line, shift, defect code, and period.",
 dimensions=time_dims("inspection_date","inspection_month","Inspection")+[D("Shift","shift","Shift: A, B, C (night 22:00-06:00).",["crew"])]+PLANT+LINE+[
   D("Part Number","part_number","Part being produced when inspected.",["part","SKU"]),
   D("Defect Code","primary_defect_code","Primary defect found, e.g. 'Crimp height out of spec', 'Porosity', 'Bore out of tolerance'.",["defect","defect type","failure code"]),
   D("Inspection Result","result","PASS or FAIL (FAIL = more than 2 defects in the sample).",["result","pass fail"]),
   D("Characteristic","characteristic","Critical-to-quality characteristic measured, e.g. 'Crimp height'.",["CTQ","measurement"])],
 measures=[
   M("Inspections","COUNT(1)","Number of inspections.",["inspection count"]),
   M("Failed Inspections","COUNT(1) FILTER (WHERE NOT is_pass)","Inspections with result FAIL.",["failures"]),
   M("Inspection Fail Rate","MEASURE(`Failed Inspections`) / MEASURE(`Inspections`)","Failed / total inspections.",["fail rate"],PCT),
   M("Units Sampled","SUM(sample_size)","Units inspected in samples.",["sample size"]),
   M("Defects Found","SUM(defects_found)","Defective units found in samples.",["defects"]),
   M("Defect Rate","MEASURE(`Defects Found`) / MEASURE(`Units Sampled`)","Defects found / units sampled.",["defect %","reject rate"],PCT),
   M("Defect PPM","MEASURE(`Defects Found`) * 1000000.0 / MEASURE(`Units Sampled`)","Defective parts per million sampled.",["PPM","parts per million"]),
   M("Average Cpk","AVG(cpk)","Average process capability index. Below 1.33 = not capable.",["Cpk","process capability","capability"]),
   M("Average Measured Value","AVG(measured_mean)","Average measured value of the characteristic (in its unit of measure).",["mean measurement"]),
   M("Low Capability Inspections","COUNT(1) FILTER (WHERE cpk < 1.33)","Inspections where Cpk < 1.33.",["incapable samples"]),
 ])
views["quality_ncr_metrics"]=dict(version=1.1, source=f"{G}.fact_nonconformance",
 comment="Nonconformance (NCR) and cost-of-poor-quality KPIs, with linked CAPA status. Use for NCR counts, COPQ, supplier quality escapes, and defect Pareto by plant, line, supplier, and period.",
 dimensions=time_dims("opened_date","opened_month","Opened")+[
   D("NCR Source","source","Where the NCR came from: In-Process, Incoming Inspection, Customer Complaint.",["source","origin"])]+PLANT+[
   D("Line ID","line_id","Line where the nonconformance was found (null for incoming).",["line"]),
   D("Machine ID","machine_id","Machine implicated, when known.",["machine","work center"]),
   D("Part Number","part_number","Part affected (in-process NCRs).",["part"]),
   D("Material Name","material_name","Purchased material affected (incoming NCRs).",["material","casting"]),
   D("Supplier Name","supplier_name","Supplier responsible (incoming NCRs), e.g. 'Brightline Castings'.",["supplier","vendor"]),
   D("Defect Code","defect_code","Defect code, e.g. Porosity, 'Crimp height out of spec', 'Bore out of tolerance'.",["defect","defect type"]),
   D("Severity","severity","Major or Minor.",["severity level"]),
   D("Disposition","disposition","Scrap, Rework, Use As Is, Sort & Rework, Return to Vendor.",["MRB decision"]),
   D("NCR Status","ncr_status","Open, Open - CAPA Pending, Closed.",["status"]),
   D("CAPA ID","capa_id","Linked CAPA, e.g. CAPA-2026-101.",["CAPA","corrective action"]),
   D("CAPA Status","capa_status","Status of the linked CAPA: Open, In Progress, Overdue, Closed.",["corrective action status"])],
 measures=[
   M("NCR Count","COUNT(1)","Number of nonconformance reports.",["NCRs","nonconformances","quality incidents"]),
   M("Major NCRs","COUNT(1) FILTER (WHERE severity = 'Major')","Number of Major NCRs.",["major nonconformances"]),
   M("Open NCRs","COUNT(1) FILTER (WHERE ncr_status <> 'Closed')","NCRs not yet closed.",["open nonconformances"]),
   M("Quantity Affected","SUM(qty_affected)","Units affected by NCRs.",["affected units","nonconforming quantity"]),
   M("COPQ USD","SUM(cost_of_poor_quality_usd)","Cost of poor quality from NCRs, USD.",["cost of poor quality","quality cost","scrap and rework cost"],USD),
   M("Average COPQ per NCR","MEASURE(`COPQ USD`) / MEASURE(`NCR Count`)","Average COPQ per NCR, USD.",["COPQ per NCR"],USD),
   M("Supplier NCRs","COUNT(1) FILTER (WHERE source = 'Incoming Inspection')","NCRs raised at incoming inspection against suppliers.",["supplier escapes","incoming NCRs"]),
 ])
views["maintenance_work_order_metrics"]=dict(version=1.1, source=f"{G}.fact_maintenance_work_order",
 comment="Maintenance work order KPIs from the CMMS: PM compliance, breakdowns, MTTR, and maintenance cost by plant, line, machine, OEM, failure mode, and period.",
 dimensions=time_dims("created_date","created_month","Created")+PLANT+LINE+MACH+[
   D("OEM","oem","Machine manufacturer, e.g. 'Hartwell Machine Tools'.",["manufacturer","vendor","machine builder"]),
   D("Work Order Type","work_order_type","Preventive, Corrective, or Emergency.",["WO type","maintenance type"]),
   D("Priority","priority","Medium, High, Critical.",["urgency"]),
   D("Failure Mode","failure_mode","Failure mode for breakdowns, e.g. 'spindle bearing wear'.",["failure","cause","fault"]),
   D("Status","status","Completed or Deferred (PMs can be deferred).",["WO status"])],
 measures=[
   M("Work Orders","COUNT(1)","Number of work orders.",["WOs","jobs"]),
   M("PMs Due","COUNT(1) FILTER (WHERE is_preventive)","Preventive maintenance work orders due.",["preventive maintenance due"]),
   M("PMs Completed","COUNT(1) FILTER (WHERE is_pm_completed)","Preventive maintenance completed.",["PMs done"]),
   M("PMs Deferred","COUNT(1) FILTER (WHERE is_pm_deferred)","Preventive maintenance deferred/skipped.",["skipped PMs","missed PMs"]),
   M("PM Compliance","MEASURE(`PMs Completed`) / MEASURE(`PMs Due`)","Completed PMs / PMs due. Corporate target 95%.",["preventive maintenance compliance","PM completion rate"],PCT),
   M("Breakdowns","COUNT(1) FILTER (WHERE is_breakdown)","Corrective + Emergency work orders (unplanned failures).",["failures","breakdown count","unplanned work orders"]),
   M("Emergency Work Orders","COUNT(1) FILTER (WHERE work_order_type = 'Emergency')","Emergency work orders.",["emergencies"]),
   M("Repair Hours","SUM(repair_hours) FILTER (WHERE is_breakdown)","Elapsed hours from breakdown to repair completion.",["time to repair"]),
   M("MTTR Hours","MEASURE(`Repair Hours`) / MEASURE(`Breakdowns`)","Mean time to repair, hours.",["mean time to repair","MTTR"]),
   M("Labor Hours","SUM(labor_hours)","Technician labor hours.",["wrench time","man hours"]),
   M("Parts Cost USD","SUM(parts_cost_usd)","Spare parts cost, USD.",["parts spend"],USD),
   M("Contractor Cost USD","SUM(contractor_cost_usd)","OEM field service / contractor cost, USD.",["field service cost","vendor service cost"],USD),
   M("Total Maintenance Cost USD","SUM(total_cost_usd)","Parts + contractor cost, USD.",["maintenance cost","maintenance spend"],USD),
   M("Reactive Maintenance Ratio","MEASURE(`Breakdowns`) / MEASURE(`Work Orders`)","Share of work orders that are reactive (breakdowns).",["reactive ratio"],PCT),
 ])
views["maintenance_asset_health_metrics"]=dict(version=1.1, source=f"{G}.fact_machine_health_daily",
 comment="Condition-monitoring KPIs per machine per day from the IoT historian: vibration, temperature, running/down hours, hours above the 4.5 mm/s OEM/ISO 10816 limit, breakdowns and MTBF.",
 dimensions=time_dims("reading_date","reading_month","Reading")+PLANT+LINE+MACH+[
   D("OEM","oem","Machine manufacturer.",["manufacturer","machine builder"])],
 measures=[
   M("Average Vibration mm/s","SUM(avg_vibration_mm_s * running_hours) / NULLIF(SUM(running_hours), 0)","Average running vibration velocity (RMS, mm/s). Hartwell OEM limit for spindle bearing replacement is 4.5 mm/s.",["vibration","avg vibration","vibration level"]),
   M("Max Vibration mm/s","MAX(max_vibration_mm_s)","Peak running vibration, mm/s.",["peak vibration"]),
   M("Average Temperature C","SUM(avg_temperature_c * running_hours) / NULLIF(SUM(running_hours), 0)","Average running temperature, deg C.",["temperature","avg temp"]),
   M("Max Temperature C","MAX(max_temperature_c)","Peak running temperature, deg C.",["peak temperature"]),
   M("Running Hours","SUM(running_hours)","Hours the machine was running.",["run hours","operating hours"]),
   M("Down Hours","SUM(down_hours)","Hours the machine was down (failed or in maintenance).",["machine downtime hours"]),
   M("Hours Above 4.5 mm/s","SUM(hours_above_4_5_mm_s)","Running hours with vibration above 4.5 mm/s (OEM replace limit / ISO 10816 zone C-D).",["hours over vibration limit","vibration exceedance hours","alarm hours"]),
   M("Breakdowns","SUM(breakdowns)","Breakdowns (corrective/emergency WOs) started.",["failures"]),
   M("MTBF Hours","MEASURE(`Running Hours`) / NULLIF(MEASURE(`Breakdowns`), 0)","Mean time between failures = running hours / breakdowns.",["mean time between failures","MTBF"]),
   M("Machine Availability","MEASURE(`Running Hours`) / NULLIF(MEASURE(`Running Hours`) + MEASURE(`Down Hours`), 0)","Running / (running + down) hours.",["asset availability","uptime"],PCT),
   M("Energy kWh","SUM(energy_kwh)","Energy consumed, kWh.",["power consumption","electricity"]),
 ])
views["supply_supplier_performance_metrics"]=dict(version=1.1, source=f"{G}.fact_supplier_receipt",
 comment="Supplier delivery and incoming-quality KPIs per PO line: on-time delivery (OTD), days late, PPM vs the supplier quality agreement limit, and spend, by supplier, material, plant and period.",
 dimensions=[D("Promised Month","promised_month","Month the supplier promised delivery.",["month","delivery month"]),
   D("Fiscal Quarter","fiscal_quarter","Fiscal quarter of the promised date, e.g. 'FY26 Q3' (FY starts Oct 1).",["quarter"]),
   D("Order Date","order_date","PO order date.",["PO date"]), D("Receipt Date","receipt_date","Goods receipt date.",["received date"]),
   D("Supplier ID","supplier_id","Supplier code, e.g. SUP-1007.",["vendor id"]),
   D("Supplier Name","supplier_name","Supplier name, e.g. 'Brightline Castings'.",["supplier","vendor"]),
   D("Supplier Country","supplier_country","Supplier country.",["country"]),
   D("Supplier Category","supplier_category","Commodity category, e.g. Castings, Bearings.",["commodity","category"]),
   D("PPM Limit","quality_agreement_ppm_limit","Contractual PPM limit in the supplier quality agreement.",["contract PPM"]),
   D("Material Name","material_name","Purchased material.",["material","item"]),
   D("Plant Name","plant_name","Receiving plant.",["plant","site"]),
   D("Inspection Result","inspection_result","ACCEPT, ACCEPT WITH DEVIATION, REJECT.",["incoming result"])],
 measures=[
   M("PO Lines","COUNT(1)","Purchase order lines.",["purchase orders","POs"]),
   M("Receipts","COUNT(1) FILTER (WHERE is_received)","PO lines received.",["deliveries"]),
   M("On-Time Receipts","COUNT(1) FILTER (WHERE is_on_time)","Receipts on or before the promised date.",["on time deliveries"]),
   M("Supplier OTD","MEASURE(`On-Time Receipts`) / MEASURE(`Receipts`)","Supplier on-time delivery = on-time receipts / receipts. Target 95%.",["on-time delivery","OTD","delivery performance"],PCT),
   M("Average Days Late","AVG(days_late) FILTER (WHERE days_late > 0)","Average days late, for late receipts only.",["lateness","days late"]),
   M("Received Qty","SUM(received_qty)","Units received.",["quantity received"]),
   M("Rejected Qty","SUM(rejected_qty)","Units rejected at incoming inspection.",["rejects"]),
   M("Supplier PPM","MEASURE(`Rejected Qty`) * 1000000.0 / MEASURE(`Received Qty`)","Rejected parts per million received.",["PPM","defect PPM","quality PPM"]),
   M("PO Spend USD","SUM(po_value_usd)","Purchase order value, USD.",["spend","purchase spend"],USD),
   M("Open PO Lines","COUNT(1) FILTER (WHERE NOT is_received)","PO lines not yet received.",["open POs"]),
 ])
views["supply_inventory_metrics"]=dict(version=1.1, source=f"{G}.fact_inventory_daily",
 comment="Daily inventory KPIs by warehouse and item. Inventory is a snapshot: for CURRENT inventory filter Snapshot Date to the latest date (2026-09-30); the 'Average Daily' measures are safe across date ranges.",
 dimensions=time_dims("snapshot_date","snapshot_month","Snapshot")+[
   D("Warehouse ID","warehouse_id","WH-<plant> plant warehouses; DC-MEM Memphis, DC-RNO Reno, DC-RTM Rotterdam distribution centers.",["DC","location code"]),
   D("Warehouse Name","warehouse_name","Warehouse name.",["warehouse","distribution center"]),
   D("Warehouse Type","warehouse_type","Plant or Distribution Center.",["location type"]),
   D("Region","region","Warehouse region.",["geography"]),
   D("Item ID","item_id","Part number (finished good) or MAT-xxxx (raw material).",["SKU","item"]),
   D("Item Type","item_type","Finished Good or Raw Material.",["inventory type"]),
   D("Item Name","item_name","Item description.",["item description","product","material"]),
   D("Item Category","item_category","Product family (FG) or material category (RM).",["category"]),
   D("Supplier ID","supplier_id","Primary supplier for raw materials.",["vendor"])],
 measures=[
   M("Item Days","COUNT(1)","Warehouse-item-day snapshots."),
   M("Average Daily On-Hand Qty","SUM(on_hand_qty) / COUNT(DISTINCT snapshot_date)","Average on-hand quantity per day over the selected dates.",["on hand","inventory level","stock on hand"]),
   M("Average Daily Inventory Value USD","SUM(inventory_value_usd) / COUNT(DISTINCT snapshot_date)","Average inventory value per day, USD.",["inventory value","stock value"],USD),
   M("Stockout Item Days","COUNT(1) FILTER (WHERE is_stockout)","Item-days where on-hand < allocated (stockout).",["stockouts","stock-outs"]),
   M("Stockout Rate","MEASURE(`Stockout Item Days`) / MEASURE(`Item Days`)","Share of item-days in stockout.",["stockout %"],PCT),
   M("Below Safety Stock Item Days","COUNT(1) FILTER (WHERE is_below_safety_stock)","Item-days below safety stock.",["below safety stock"]),
 ])
views["supply_shipment_metrics"]=dict(version=1.1, source=f"{G}.fact_shipment",
 comment="Outbound logistics KPIs per shipment: carrier on-time vs SLA, customer on-time and OTIF, freight cost, transit time, by carrier, DC, customer, product and period.",
 dimensions=time_dims("ship_date","ship_month","Ship")+[
   D("Warehouse ID","warehouse_id","Shipping DC: DC-MEM Memphis, DC-RNO Reno, DC-RTM Rotterdam.",["DC","origin","lane origin"]),
   D("Warehouse Name","warehouse_name","Shipping DC name.",["distribution center"]),
   D("Carrier ID","carrier_id","Carrier code, e.g. CAR-04.",["carrier code"]),
   D("Carrier Name","carrier_name","Carrier, e.g. 'Ridgeway Freight'.",["carrier","freight carrier","trucking company","3PL"]),
   D("Carrier Mode","carrier_mode","LTL, FTL, Parcel, Intermodal, Ocean/Air.",["mode"]),
   D("Customer Name","customer_name","Customer, e.g. 'Apex Agricultural Equipment'.",["customer","account"]),
   D("Customer Tier","customer_tier","Strategic, Key, Standard.",["tier","segment"]),
   D("Customer Industry","customer_industry","Customer industry.",["industry"]),
   D("Customer Region","customer_region","Customer region.",["region"]),
   D("Part Number","part_number","Part shipped.",["SKU"]),
   D("Product Family","product_family","Product family shipped.",["product line"]),
   D("Producing Plant","producing_plant_id","Plant that makes the part.",["source plant"]),
   D("Shipment Status","shipment_status","Delivered or In Transit.",["status"])],
 measures=[
   M("Shipments","COUNT(1)","Number of shipments.",["deliveries","loads"]),
   M("Delivered Shipments","COUNT(1) FILTER (WHERE delivered_date IS NOT NULL)","Shipments delivered."),
   M("Carrier On-Time Rate","COUNT_IF(is_carrier_on_time) / COUNT_IF(is_carrier_on_time IS NOT NULL)","Delivered by carrier due date (ship date + planned transit) / delivered. Contract SLA 95%.",["carrier on-time","on-time %","carrier performance","OTP"],PCT),
   M("Customer On-Time Rate","COUNT_IF(is_on_time_to_customer) / COUNT_IF(is_on_time_to_customer IS NOT NULL)","Delivered by customer requested date / delivered.",["on time to customer"],PCT),
   M("OTIF","COUNT_IF(is_otif) / COUNT_IF(is_otif IS NOT NULL)","On time (to customer requested date) and in full / delivered. Customer target 95%.",["on time in full","OTIF %","delivery performance"],PCT),
   M("In-Full Rate","COUNT_IF(is_in_full) / COUNT(1)","Shipped quantity >= ordered quantity.",["fill rate"],PCT),
   M("Late Carrier Shipments","COUNT_IF(NOT is_carrier_on_time)","Delivered after the carrier due date.",["late deliveries"]),
   M("Freight Cost USD","SUM(freight_cost_usd)","Freight spend, USD.",["freight spend","shipping cost"],USD),
   M("Freight Cost per Shipment","MEASURE(`Freight Cost USD`) / MEASURE(`Shipments`)","Average freight cost per shipment, USD.",["cost per shipment"],USD),
   M("Order Value USD","SUM(order_value_usd)","Order value of shipped lines, USD.",["revenue","sales value"],USD),
   M("Average Transit Days","AVG(actual_transit_days)","Average actual transit days (delivered shipments).",["transit time","lead time"]),
 ])
domain={"production":["production_oee_metrics","production_downtime_metrics"],"quality":["quality_inspection_metrics","quality_ncr_metrics"],
        "maintenance":["maintenance_work_order_metrics","maintenance_asset_health_metrics"],"supply_chain":["supply_supplier_performance_metrics","supply_inventory_metrics","supply_shipment_metrics"]}
for name,v in views.items():
    dom=[d for d,l in domain.items() if name in l][0]
    hdr=f"# Metric view: {name}   (Genie space: {dom})\n# Deployed by 02_create_metric_views as {{catalog}}.{{gold_schema}}.{name}\n# {{catalog}} / {{gold_schema}} are filled in from config/demo_config.yml.\n"
    class NoAlias(yaml.SafeDumper):
        def ignore_aliases(self, data): return True
    open(f"{os.path.dirname(os.path.abspath(__file__))}/metric_views/{name}.yaml","w").write(hdr+yaml.dump(v, Dumper=NoAlias, sort_keys=False, width=200, allow_unicode=True))
print("wrote", len(views))
