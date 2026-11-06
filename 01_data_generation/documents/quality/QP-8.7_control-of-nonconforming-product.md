# Control of Nonconforming Product

| Field | Value |
|---|---|
| Document ID | QP-8.7 |
| Title | Control of Nonconforming Product (NCR Procedure) |
| Revision | Rev 5 |
| Effective Date | 2026-02-02 |
| Owner | Elena Ramirez, Director of Quality |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose and Scope

This procedure defines how KK's Parts identifies, records, segregates, evaluates and dispositions nonconforming product at all five plants (CLB, GVL, MTY, WRO, PNQ). It applies to purchased material, work in process and finished goods, and to product returned by customers. It supports the IATF 16949 and ISO 9001 requirement to prevent unintended use or delivery of nonconforming product.

## 2. Definitions

- **Nonconformance Report (NCR):** the record created for every nonconforming lot, batch or unit. Each NCR carries a defect code (see GLS-QUA-001), quantity, plant, line, work center, shift and cost.
- **Nonconforming product:** any item that fails a drawing, specification, control plan characteristic (for example CP-WRO-L1 or CP-CLB-L1) or customer requirement.
- **COPQ:** cost of poor quality, as defined in Section 9.

## 3. NCR Sources

Every NCR is classified by one of three sources.

| Source | Typical trigger | Raised by |
|---|---|---|
| In-Process | Failure at an in-line gauge, test stand, pull tester, leak tester or operator check | Operator, line inspector or quality technician |
| Incoming Inspection | Receiving inspection reject under QP-7.4 | Receiving inspector |
| Customer Complaint | Return, claim or scorecard defect reported by an OEM | Customer quality liaison |

An NCR must be opened within the same shift in which the nonconformance is detected. Customer Complaint NCRs must be opened within one business day of receipt of the complaint.

## 4. Severity Classification

| Severity | Criteria | Examples |
|---|---|---|
| Major | Affects safety, regulatory compliance, form, fit or function; could reach the customer; repeat occurrence of the same defect code on the same work center within 5 working days; or more than 2% of a lot is affected | Casting porosity that leaks at pressure test; crimp height out of specification; bearing bore out of tolerance |
| Minor | Cosmetic or non-functional deviation with no effect on fit, form or function | Light surface finish marks outside a non-sealing area |

Severity is assigned by the originator and confirmed by the plant quality engineer within 24 hours. Quality may upgrade, but not downgrade, a severity without the approval of the plant quality manager.

## 5. Identification and Segregation

1. Nonconforming product is tagged with a red NCR tag and moved to the marked red-bin or cage for the line within the shift.
2. Product on quality hold must never be mixed with conforming product. Locations in the ERP are blocked from picking until disposition.
3. Suspect product upstream and downstream of the detection point is also contained (see Section 7).

## 6. Dispositions

Only the following five dispositions are valid in the NCR system. Free-text dispositions are not permitted.

| Disposition | Meaning | Approval required |
|---|---|---|
| Scrap | Product is destroyed or returned to scrap stream; scrap value is booked | Quality technician for Minor under USD 1,000; plant quality engineer otherwise |
| Rework | Product is reprocessed to meet the original requirement using an approved rework instruction | Plant quality engineer; plant quality manager for Major |
| Use As Is | Product is accepted with a documented deviation; no reprocessing | Plant quality manager; customer approval where the customer drawing requires it |
| Sort & Rework | 100% sorting of the lot to separate good from bad, with rework of salvageable units | Plant quality engineer; plant quality manager for Major |
| Return to Vendor | Purchased material is returned to the supplier for credit or replacement; a SCAR may be issued | Supplier quality engineer (for castings, Rosa Martinez) |

Use As Is on any Major NCR requires the additional signature of the Director of Quality, Elena Ramirez. A disposition of Use As Is is never applied to a safety characteristic.

## 7. Quality Hold Rules

A Major NCR may trigger a line **Quality Hold**. The plant quality engineer or shift supervisor decides, using these rules.

1. A Quality Hold is required when a Major NCR indicates the process is out of control or when containment cannot be assured by sorting alone.
2. The hold is logged in the MES as a downtime event with reason code **"Quality Hold"** (one of the six MES downtime reason codes). The start time is the moment production stops and the end time is the moment the quality engineer releases the line.
3. Restart requires documented containment, a first-piece approval and a quality engineer signature.
4. Holds exceeding 4 hours are escalated to the plant manager and reported in the next daily production meeting.
5. Product produced since the last confirmed good check is held and sorted.

## 8. Roles

| Role | Responsibility |
|---|---|
| Operator / inspector | Detect, tag, segregate, raise NCR |
| Plant quality engineer | Confirm severity, recommend disposition, lead containment (for example Tomasz Wisniewski at WRO) |
| Plant quality manager | Approve Major dispositions (for example Guadalupe Flores at MTY) |
| Supplier quality engineer | Own supplier-related NCRs, SCARs and returns |
| Director of Quality | Approve Use As Is on Major NCRs; chair monthly NCR review |

## 9. COPQ Calculation

COPQ is the cost of poor quality captured on NCRs and equals:

COPQ = scrap value + rework cost + handling cost

- **Scrap value** = scrapped quantity x standard cost per unit, less any recovered scrap credit.
- **Rework cost** = rework labor hours x plant burdened labor rate, plus rework materials.
- **Handling cost** = sorting, tagging, transport, re-inspection and disposal cost recorded against the NCR.

Return to Vendor NCRs record handling cost and, where the supplier agreement allows, a chargeback is raised separately (see SQA-BLC-2023). Downtime costs and expedited freight are tracked outside COPQ. COPQ is reported monthly by plant, line, defect code and supplier, and rolled up into the Quality Management Review (QR-2026-Q3).

## 10. NCR Closure and Linkage to CAPA

An NCR is closed when the disposition is executed and the cost fields are complete. Where the criteria of QP-10.2 are met (for example repeat Major NCRs for the same defect code), the NCR is linked to a CAPA. Supplier NCRs that breach the PPM limit in the supplier quality agreement are linked to a SCAR.

## 11. Records

NCR records are retained for 10 years or the life of the product plus one year, whichever is longer.

## 12. Revision History

| Rev | Date | Change |
|---|---|---|
| 4 | 2024-09-16 | Added Sort & Rework disposition |
| 5 | 2026-02-02 | Aligned Quality Hold logging to the six MES reason codes; added COPQ formula |
