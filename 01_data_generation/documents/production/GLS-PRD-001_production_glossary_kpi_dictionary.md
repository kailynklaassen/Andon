# Production Glossary & KPI Dictionary

| Field | Value |
|---|---|
| Document ID | GLS-PRD-001 |
| Title | Production Glossary & KPI Dictionary |
| Revision | Rev C |
| Effective Date | 2026-01-12 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Elena Ramirez, Director of Quality |
| Classification | Internal |

## 1. Purpose

This glossary gives one definition for each production term and KPI used at KK's Parts. It matches the gold metric views and the OEE standard (SOP-PRD-001). When a report and this glossary differ, this glossary prevails.

## 2. Core KPI definitions

| Term | Definition | Formula |
|---|---|---|
| OEE | Overall Equipment Effectiveness. | Availability x Performance x Quality |
| Availability | Share of planned time the equipment was running. | Run minutes ÷ planned minutes |
| Performance | How fast the equipment ran compared to its ideal speed. | (Total units x ideal cycle time) ÷ run time |
| Quality | Share of units that were good. | Good units ÷ total units |
| First Pass Yield (FPY) | Share of units right the first time. Scrap and rework both count as not-first-pass. | Good units ÷ total units |
| Planned production time | Scheduled time per shift available for production. | 450 minutes (480 minus 30-minute break) |
| Run time / run minutes | Planned minutes minus coded downtime minutes. | Planned minutes - downtime minutes |
| Ideal cycle time | Fastest sustainable time to produce one unit at the line's rate-setting step, in seconds. Example: GVL-L3 is 156.5 s/unit. | Defined in master data |
| Takt time | Available production time divided by customer demand. Used to set the pace needed to meet demand. | Available seconds ÷ demanded units |
| Scrap | Units that cannot be sold or reworked and are discarded. Recorded with a scrap reason on the shift result. | Count and value |
| Rework | Units that fail first pass but are repaired and re-inspected. Counts against FPY, not as scrap. | Count and labor cost |
| Changeover | Time from the last good part of one product to the first good part of the next (SOP-PRD-014). | End time - start time |
| MO (manufacturing order / production order) | A released instruction to produce a quantity of a product on a line. | n/a |
| Shift result | The record of units produced, good units, scrap, rework and downtime for a work center on one shift. | n/a |

## 3. Downtime reason codes

| Code | Meaning |
|---|---|
| Equipment Failure | Unplanned stop due to machine fault. |
| Planned Maintenance | Scheduled preventive or condition-based maintenance. |
| Changeover | Product, tooling or program change. |
| Material Shortage | Material not available at the work center. |
| Quality Hold | Production stopped pending quality disposition. |
| No Operator | Machine available but no qualified operator. |

These are the only six codes accepted by MES.

## 4. Maintenance and reliability terms

| Term | Definition |
|---|---|
| PM compliance | Completed preventive work orders ÷ preventive work orders due. Corporate policy target is 95%; plant targets: CLB 97%, GVL 84%, MTY 90%, WRO 92%, PNQ 91%. |
| MTBF | Mean time between failures = run hours ÷ failure count. |
| MTTR | Mean time to repair = repair hours ÷ failure count. |
| Criticality A / B / C | A = bottleneck or no redundancy; B = important with partial redundancy; C = low impact. |
| Emergency / Corrective WO | Unplanned work order raised after a failure. |
| OEM limit | The condition limit published by the equipment manufacturer. |
| MOC | Management of Change (for example MOC-2026-031). |

## 5. Quality and supplier terms

| Term | Definition |
|---|---|
| NCR | Non-conformance report. |
| CAPA | Corrective and preventive action record (for example CAPA-2026-101). |
| SCAR | Supplier corrective action request (for example SCAR-2026-014). |
| 8D | Eight-discipline problem-solving report. |
| PPM (supplier) | Rejected quantity ÷ received quantity x 1,000,000. |
| COPQ | Cost of poor quality from NCRs: scrap value, rework cost and handling. |
| Supplier OTD | Receipts with days late = 0 ÷ receipts. |
| Cpk | Process capability index; KK's Parts target is at least 1.33 for critical characteristics. |

## 6. Logistics terms

| Term | Definition |
|---|---|
| Carrier on-time | Delivered on or before the carrier due date (ship date plus planned transit). |
| Customer OTIF | Delivered on or before the customer-requested date and in full quantity. |
| Days of supply | On-hand ÷ average daily demand. |
| Stockout | On-hand quantity is below allocated quantity. |

## 7. Identifier conventions

| Type | Pattern | Example |
|---|---|---|
| Plant | 3 letters | CLB, GVL, MTY, WRO, PNQ |
| Line | `<PLANT>-L<n>` | GVL-L3 |
| Work center / machine | `<LINE>-WC<nn>` | GVL-L3-WC01 |
| Material | MAT-#### | MAT-5002 |
| Supplier | SUP-#### | SUP-1007 |
| Carrier | CAR-## | CAR-04 |
| Customer | CUST-#### | CUST-2001 |
| Warehouse | WH-<plant>, DC-<code> | WH-GVL, DC-MEM |

## 8. Shifts

| Shift | Hours |
|---|---|
| A | 06:00-14:00 |
| B | 14:00-22:00 |
| C | 22:00-06:00 |

Monday to Friday: three shifts. Saturday: A and B. Sunday: dark.

## 9. Targets

| KPI | Target |
|---|---|
| OEE | 85% corporate (world-class) |
| PM compliance | 95% corporate policy; plant targets above |
| Supplier PPM | 500 (SQA-BLC-2023 limit for Brightline Castings, Keystone Foundry 500, Silesia Metalworks 250) |
| Carrier on-time | 95% SLA (Ridgeway Freight, CTA-RF-2024-07) |

## 10. Common misreadings

1. OEE is not run time ÷ planned time. That is Availability only.
2. Rework is not scrap, but both reduce FPY and Quality.
3. Changeover loss is already inside Availability; do not subtract it twice.
4. Short stops under one minute and slow running appear in Performance, not downtime.

## 11. Related documents

SOP-PRD-001, SOP-PRD-014, SOP-PRD-020, PLN-PRD-003, PFD-ALL-001.
