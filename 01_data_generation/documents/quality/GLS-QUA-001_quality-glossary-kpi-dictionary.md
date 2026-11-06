# Quality Glossary and KPI Dictionary

| Field | Value |
|---|---|
| Document ID | GLS-QUA-001 |
| Title | Quality Glossary & KPI Dictionary |
| Revision | Rev 3 |
| Effective Date | 2026-04-01 |
| Owner | Elena Ramirez, Director of Quality |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose

This glossary defines the quality terms and KPIs used at KK's Parts and in the quality reports and metric views, so that numbers mean the same thing at every plant. Definitions of calculated KPIs match the gold metric views.

## 2. KPI Definitions

| KPI | Definition | Formula | Notes |
|---|---|---|---|
| First Pass Yield (FPY) | Share of units that are good the first time through the process | Good units / total units | Scrap and rework both count as not first pass |
| PPM (supplier) | Defective parts per million received | Rejected quantity / received quantity x 1,000,000 | Calculated monthly per supplier (QP-7.4) |
| COPQ | Cost of poor quality from NCRs | Scrap value + rework cost + handling cost | Reported by plant, line, defect code and supplier (QP-8.7) |
| Cpk | Process capability index relative to the nearest specification limit | min(USL - mean, mean - LSL) / (3 x sigma) | Target at least 1.33 for critical characteristics |
| Supplier OTD | Supplier on-time delivery | Receipts with days_late = 0 / receipts | Contract targets, for example 95% for Brightline |
| In-process defect rate | Defective units found in process | Defective units / units produced | Reported by shift, for example crimp height on WRO-L1-WC02 |

## 3. Terms

| Term | Definition |
|---|---|
| NCR | Nonconformance Report. Record of a nonconforming lot or unit with source (In-Process, Incoming Inspection, Customer Complaint), severity (Major or Minor), defect code, disposition and cost |
| Disposition | Decision on nonconforming product. Valid values: Scrap, Rework, Use As Is, Sort & Rework, Return to Vendor |
| Quality Hold | Stoppage of a line or lot pending quality release. Logged in the MES as downtime with reason code "Quality Hold" |
| CAPA | Corrective and Preventive Action. Tracked with statuses Open, In Progress, Overdue and Closed; due in 30, 45 or 60 days (QP-10.2) |
| SCAR | Supplier Corrective Action Request. Formal request to a supplier for containment, root cause and permanent corrective action |
| 8D | Eight-discipline problem-solving report (D1 team through D8 closure) |
| PPAP | Production Part Approval Process. Supplier evidence that the process can consistently meet requirements; resubmitted after process changes |
| Control plan | Document describing the characteristics, measurement methods, sampling frequency, control methods and reaction plans for a process (for example CP-WRO-L1, CP-CLB-L1) |
| Critical characteristic (CC) | Characteristic whose failure affects safety, regulatory compliance or function; requires a stop-and-contain reaction |
| AQL | Acceptable Quality Level. The maximum percent defective that is considered satisfactory as a process average for sampling inspection (ANSI/ASQ Z1.4) |
| Controlled shipping | Supplier escalation Level 2 requiring independent inspection before shipment |
| Chargeback | Invoice to a supplier for the cost of its nonconforming product |
| ACCEPT / ACCEPT WITH DEVIATION / REJECT | Incoming inspection lot outcomes (QP-7.4) |

## 4. Severity and Source Values

| Attribute | Allowed values |
|---|---|
| NCR source | In-Process, Incoming Inspection, Customer Complaint |
| NCR severity | Major, Minor |
| CAPA status | Open, In Progress, Overdue, Closed |
| MES downtime reasons | Equipment Failure, Planned Maintenance, Changeover, Material Shortage, Quality Hold, No Operator |

## 5. Defect Codes by Plant

Each NCR carries one defect code from the list for its plant.

| Plant | Defect codes |
|---|---|
| CLB, Columbus Hydraulics Plant | Bore out of tolerance; Porosity; Surface finish; Leak at test; Weld undercut; Damage in transit; Dimensional |
| GVL, Greenville Drivetrain Plant | Tooth profile error; Bore out of tolerance; Hardness out of spec; Noise at test; Burr; Porosity |
| MTY, Monterrey Machining Plant | Porosity; Bore out of tolerance; Coating thickness; Leak at test; Casting inclusion |
| WRO, Wroclaw Electrical Plant | Crimp height out of spec; Wrong terminal; Open circuit; Solder bridge; Insulation damage; Damage in transit; Documentation |
| PNQ, Pune Fastener Plant | Thread defect; Head crack; Plating thickness; Burr; Dimensional - length; Damage in transit |

## 6. Reference Limits

| Item | Value |
|---|---|
| Brightline Castings (SUP-1007) PPM limit | 500 (SQA-BLC-2023) |
| Keystone Foundry (SUP-1002) PPM limit | 500 |
| Silesia Metalworks (SUP-1003) PPM limit | 250 |
| Crimp height (CP-WRO-L1 Rev F) | 1.650 mm +/- 0.050 mm |
| Bore diameter (CP-CLB-L1 Rev C) | 25.000 mm +/- 0.015 mm |
| Cpk target, critical characteristics | At least 1.33 |

## 7. Related Documents

QP-8.7, QP-10.2, QP-7.4, SQA-BLC-2023, CP-WRO-L1, CP-CLB-L1, QR-2026-Q3.
