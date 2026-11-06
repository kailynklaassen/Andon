# Supplier Corrective Action Request: Casting Porosity

| Field | Value |
|---|---|
| Document ID | SCAR-2026-014 |
| Title | Supplier Corrective Action Request, Brightline Castings (SUP-1007), Casting Porosity |
| Revision | Rev 1 (issued 2026-05-25; status update 2026-09-22) |
| Issue Date | 2026-05-25 |
| Owner | Rosa Martinez, Supplier Quality Engineer (castings) |
| Approver | Elena Ramirez, Director of Quality |
| Classification | Internal |

## 1. Header

| Item | Detail |
|---|---|
| Supplier | Brightline Castings, Saltillo, Mexico (SUP-1007) |
| Supplier contact | Hector Salinas, Quality Manager |
| Governing agreement | SQA-BLC-2023 (500 PPM limit; 95% on-time; SCAR response 10 business days; 8D in 30 days) |
| Affected parts | MAT-5001 Valve Body Casting, MAT-5002 Pump Housing Casting, MAT-5004 Manifold Casting, MAT-5005 Bearing Cap Casting |
| Receiving plants | CLB, MTY, with some castings to GVL |
| Linked record | CAPA-2026-101, "SCAR: casting porosity from Brightline Castings" |
| Escalation level at issue | Level 1 (SCAR) per SQA-BLC-2023 Section 6 |

## 2. Problem Description

Beginning 2026-05-01, castings received from Brightline show a sharp increase in subsurface and sealing-face porosity, found at incoming inspection (QP-7.4), during machining on MTY-L1, MTY-L2 and CLB-L1, and at leak test. The timing coincides with Brightline's move of production to a new furnace line and a change of sand supplier, which was not notified to KK's Parts as required by SQA-BLC-2023 Section 3.

## 3. Supporting Data

Figures are cumulative from 2026-05-01 through the 2026-09-22 status update unless stated.

| Metric | Before 2026-05-01 | After 2026-05-01 | Requirement |
|---|---|---|---|
| Incoming PPM (Brightline) | 237 PPM | 2,726 PPM | 500 PPM maximum |
| On-time delivery | 92% | 44% | 95% minimum |
| Average lateness of late receipts | not applicable | 9.3 days | n/a |
| Porosity NCRs (QP-8.7) | background level | 380 | n/a |
| Cost of poor quality attributed to porosity | n/a | approximately USD 1.68M | n/a |

At issue on 2026-05-25 the May-to-date PPM already stood above 2,000 PPM, over four times the contractual limit. The COPQ figure includes scrap value of machined castings found porous after machining, rework and sorting, and handling (COPQ per QP-8.7). Consuming lines also logged 218 material-shortage downtime events (see supply chain documents), which are not included in COPQ.

Dominant defect code is Porosity at MTY and Leak at test at CLB. Defects are concentrated in MAT-5001 and MAT-5002, located at pressure-containing walls and port bosses, which fail the SQA-BLC-2023 Section 4 criteria for critical zones.

## 4. Requested Actions

Brightline is requested to provide:

1. **Containment (within 10 business days of issue, due 2026-06-08):**
   - Segregate and 100% inspect all Brightline-held and in-transit stock of the four part numbers, using radiographic or pressure test as defined in SQA-BLC-2023 Section 4.
   - Mark all containment-inspected shipments with a "CI" label and identify them on the certificate of conformance.
   - Quarantine product from the new furnace line pending approval.
2. **Root cause analysis:** evidence on the effect of the furnace change and the sand supplier change on gas and shrinkage porosity (sand permeability, moisture, binder gas evolution, pouring temperature, degassing, gating).
3. **Permanent corrective action 8D** (due 2026-06-24, 30 days from issue).
4. **PPAP resubmission** of all four part numbers for the changed process, level 3.
5. **Weekly status** to the Supplier Quality Engineer until closure.

## 5. Response Status (as of 2026-09-22)

| Deliverable | Due | Received | Assessment |
|---|---|---|---|
| Containment plan | 2026-06-08 | 2026-06-19 | Late by 7 business days; covers finished castings only, not work-in-process or in-transit stock |
| Initial root cause | 2026-06-08 | Not provided | Open |
| 8D report | 2026-06-24 | 2026-07-02 (partial) | Late and incomplete: D1 to D3 only (containment); no verified root cause (D4) and no permanent corrective action (D5 to D7) |
| PPAP resubmission | n/a | Not received | Open |
| Weekly status | weekly | Irregular | Four of the last 16 weeks received |

KK's Parts' evaluation: Brightline's response does not satisfy SQA-BLC-2023. Containment alone has not reduced the defect rate, and Brightline's own inspection data differ from KK's Parts' incoming findings. The 8D has not been accepted by the Director of Quality.

## 6. CAPA Tracking

SCAR-2026-014 is tracked internally as **CAPA-2026-101**, opened 2026-05-25 and due 2026-07-24 (Complex category, 60 days, QP-10.2). The due date passed with no accepted 8D and no approved extension. The CAPA status is therefore **Overdue**. It remains in the weekly overdue review and the monthly Quality Management Review (QR-2026-Q3).

## 7. Recommended Escalation

Under SQA-BLC-2023 Section 6, a SCAR response that is late or incomplete is the trigger for Level 2. The Supplier Quality Engineer recommends:

1. **Escalate to Level 2: Controlled Shipping** effective on approval, requiring independent 100% inspection of castings before shipment at Brightline's expense, with inspection records sent with each lot.
2. Conduct an on-site audit at Saltillo within 30 days, focusing on the furnace line, sand management and radiographic capability.
3. Invoice chargebacks for NCR costs and sorting labor under Section 5 of the agreement.
4. Hold an executive review with Brightline weekly until PPM is under 500 for three consecutive months.
5. Proceed in parallel with the resourcing evaluation (alternate sources under review by Supply Chain). Level 3 (new-business hold) is to be applied if Level 2 conditions are not met within 60 days.

| Decision | Name | Date |
|---|---|---|
| Recommended by | Rosa Martinez | 2026-09-22 |
| Approval of Level 2 | Elena Ramirez / Priya Nair | Pending |

## 8. Closure Criteria

This SCAR will be closed when Brightline has an accepted 8D with verified root cause, PPAP is approved for the changed process, and three consecutive months show PPM at or below 500 and on-time delivery of at least 95%, as verified under QP-10.2 Section 6.
