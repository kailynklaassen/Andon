# Line Stop Report - MTY-L1 Casting Finishing Material Shortage

| Field | Value |
|---|---|
| Document ID | LSR-MTY-2026-011 |
| Title | Line Stop Report: MTY-L1 Casting Finishing Material Shortages (Brightline Castings), June 2026 |
| Revision | Rev 1 |
| Report Date | 2026-07-06 |
| Event Dates | 2026-06-03 to 2026-06-30 (five Material Shortage events) |
| Owner | Alejandro Reyes, Monterrey Plant Manager |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Summary

During June 2026 the Monterrey Casting Finishing line (MTY-L1) recorded five Material Shortage downtime events totalling **1,102 minutes**, all caused by late castings from **SUP-1007 Brightline Castings** in Saltillo: two events (394 minutes) waiting for **MAT-5005 Bearing Cap Casting** on PO-700360, and three events (708 minutes) waiting for **MAT-5002 Pump Housing Casting** on PO-700123. The line coded the downtime under the reason code **Material Shortage** (SOP-PRD-001). The incident is one of a series of shortage events on castings-fed lines since the supplier changed production to a new furnace line and sand supplier on 2026-05-01.

## 2. Scope and linked records

| Item | Value |
|---|---|
| Plant / Line | MTY / MTY-L1 Casting Finishing (ideal cycle time 174.47 s/unit) |
| Affected materials | MAT-5005 Bearing Cap Casting; MAT-5002 Pump Housing Casting |
| Supplier | SUP-1007 Brightline Castings (Saltillo, Mexico) |
| Purchase orders | PO-700360 (MAT-5005, promised 2026-05-28); PO-700123 (MAT-5002, promised 2026-06-22) |
| Related records | SCAR-2026-014, CAPA-2026-101, SQA-BLC-2023 |
| Work centers affected | MTY-L1-WC01 Automatic Band Saw #1 to MTY-L1-WC04 Coordinate Measuring Machine #4 (the first step, WC01, is starved and the rest of the serial line follows) |

## 3. Events and timeline

All times local to Monterrey.

| Event ID | Start | End | Minutes | Shift at start | Material | PO | PO promised |
|---|---|---|---|---|---|---|---|
| DT-1001643 | 2026-06-03 07:00 | 2026-06-03 08:58 | 118 | A | Bearing Cap Casting (MAT-5005) | PO-700360 | 2026-05-28 |
| DT-1001663 | 2026-06-05 16:00 | 2026-06-05 20:36 | 276 | B | Bearing Cap Casting (MAT-5005) | PO-700360 | 2026-05-28 |
| DT-1001876 | 2026-06-27 17:00 | 2026-06-27 21:58 | 298 | B | Pump Housing Casting (MAT-5002) | PO-700123 | 2026-06-22 |
| DT-1001890 | 2026-06-29 09:00 | 2026-06-29 14:20 | 320 | A | Pump Housing Casting (MAT-5002) | PO-700123 | 2026-06-22 |
| DT-1001900 | 2026-06-30 07:00 | 2026-06-30 08:30 | 90 | A | Pump Housing Casting (MAT-5002) | PO-700123 | 2026-06-22 |

Escalation under SOP-PRD-020:

- DT-1001643 (118 minutes) reached the 60-minute Plant Supply Chain Lead step and ended just short of the 120-minute step.
- DT-1001663, DT-1001876 and DT-1001890 each passed 120 minutes. The Plant Manager (Alejandro Reyes) and Priya Nair (Director of Supply Chain & Logistics) were notified and an expedite was requested.
- PO-700360 was already 6 days past its promised date at the first event and 8 days at the second; PO-700123 was 5 days past promise at the first event on 2026-06-27 and 8 days past at the last on 2026-06-30.

## 4. Impact

| Measure | Result |
|---|---|
| Total Material Shortage downtime on MTY-L1, June 2026 | 1,102 minutes across five events (118 + 276 + 298 + 320 + 90) |
| By material | MAT-5005: 394 minutes; MAT-5002: 708 minutes |
| Share of planned time lost | 1,102 of 33,300 planned minutes (74 June shifts x 450) = 3.3% |
| Lost output (1,102 minutes x 60 / 174.47 s/unit ideal cycle) | about 379 units |
| Downstream | Starved MTY-L2 Housing Machining of finished castings; delayed housing shipments to OEM customers |

Additional notes:

- Castings that did arrive were also affected by porosity, so effective receipts were smaller than shipped quantities (see SCAR-2026-014).
- Because shortages of this kind hit multiple lines at once (GVL-L3, MTY-L3, CLB-L2 and MTY-L1), the plant was not able to reassign operators productively; some time was recoded **No Operator** and corrected under the 24-hour supervisor review.

## 5. Root cause

1. **Direct cause:** Late delivery of MAT-5005 and MAT-5002 castings from Brightline Castings. Brightline on-time delivery has averaged 44% since 2026-05-01 (92% before), with late deliveries averaging 9.3 days.
2. **Contributing cause 1:** Safety stock for both materials was set for a 92% on-time supplier.
3. **Contributing cause 2:** Porosity at the supplier forced rejection of part of every lot, shrinking effective receipts. Incoming quality has moved from 237 PPM to 2,726 PPM against the 500 PPM contract limit.
4. **Systemic cause:** Brightline's 8D response to SCAR-2026-014 (issued 2026-05-25) was late and addressed containment only. CAPA-2026-101 is due 2026-07-24.

## 6. Containment and corrective actions

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Raise MAT-5002 and MAT-5005 safety stock to 3 days of supply at WH-MTY | Priya Nair | 2026-07-17 |
| 2 | 100% receiving inspection on Brightline lots for porosity until further notice | Guadalupe Flores | In place |
| 3 | Daily call with Hector Salinas (Brightline quality manager) on shipments | Rosa Martinez | Ongoing |
| 4 | Demand permanent corrective action in the 8D under SCAR-2026-014 / CAPA-2026-101 | Rosa Martinez | 2026-07-24 |
| 5 | Evaluate alternate source Keystone Foundry (SUP-1002) for MAT-5002; PPAP about 12 weeks, +6% piece price | Priya Nair | 2026-08-31 |
| 6 | Re-sequence MTY-L1 and MTY-L2 schedules using weekly confirmed receipts, per PLN-PRD-003 section 8 | MTY planning lead | 2026-07-17 |
| 7 | Train supervisors on reason-code selection (Material Shortage vs No Operator) | Alejandro Reyes | 2026-07-24 |

## 7. Lessons learned

- Escalation worked: the 120-minute escalation reached supply chain leadership within the matrix.
- Safety stock rules must be based on actual supplier performance, not contract targets.
- Material shortage and quality rejection are linked in this case; they should be viewed together.
