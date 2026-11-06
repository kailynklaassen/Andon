# Incoming Inspection and Sampling Procedure

| Field | Value |
|---|---|
| Document ID | QP-7.4 |
| Title | Incoming Inspection & Sampling Procedure |
| Revision | Rev 6 |
| Effective Date | 2025-12-01 |
| Owner | Elena Ramirez, Director of Quality |
| Approver | Priya Nair, Director of Supply Chain & Logistics |
| Classification | Internal |

## 1. Purpose and Scope

This procedure governs how purchased material is inspected on receipt at all KK's Parts plants, how results are recorded, how lot outcomes are decided and how supplier PPM is calculated. It applies to raw materials, castings, components and packaging.

## 2. Receiving Flow

1. The receipt is posted against the purchase order and the material is placed in the inspection (blocked) location.
2. The inspector reviews the certificate of conformance (and material or test certificates where required) and checks identification and quantity.
3. The inspection plan for the material is retrieved; the inspector determines lot size, sampling plan and tests.
4. Sampling and tests are done; results are recorded in the receiving inspection record.
5. The lot outcome is decided (Section 5) and the stock is released, released with deviation, or rejected.

## 3. AQL-Based Sampling

Sampling follows ANSI/ASQ Z1.4 (ISO 2859-1), general inspection level II, single sampling, with the AQL set by characteristic class.

| Class | AQL | Examples |
|---|---|---|
| Critical (CC) | 0.065 (effectively 0 accepted for safety items; see below) | Porosity at pressure walls, bore diameter |
| Major | 0.65 | Dimensions affecting fit or function |
| Minor | 2.5 | Cosmetic, packaging |

For critical characteristics the accept number is 0: a single defective sampled unit rejects the lot or triggers 100% sorting.

Indicative single-sampling plan, normal inspection, level II:

| Lot size | Code letter | Sample size | Ac / Re at AQL 0.65 | Ac / Re at AQL 2.5 |
|---|---|---|---|---|
| 151 to 280 | G | 32 | 0 / 1 | 2 / 3 |
| 281 to 500 | H | 50 | 1 / 2 | 3 / 4 |
| 501 to 1,200 | J | 80 | 1 / 2 | 5 / 6 |
| 1,201 to 3,200 | K | 125 | 2 / 3 | 7 / 8 |

### 3.1 Switching rules

- **Tightened inspection** applies after 2 of 5 consecutive lots rejected, or when the supplier is under a SCAR (SCAR-2026-014 for Brightline Castings, SUP-1007).
- **Reduced inspection** may be used after 10 consecutive accepted lots with monthly PPM within the limit and no open SCAR, approved by the supplier quality engineer.
- Return to normal inspection after a reduced lot is rejected or when production is irregular.

## 4. Recording Inspected and Rejected Quantities

Each receiving inspection record carries these quantities:

| Field | Definition |
|---|---|
| received_qty | Total quantity received on the lot |
| inspected_qty | Number of pieces actually examined. For sampled lots, this is the sample size; for a 100% sort, it is the full lot quantity |
| rejected_qty | Quantity of rejected units. For a sampled lot that is accepted, it is the number of defective pieces found in the sample; for a rejected lot, it is the **whole lot quantity** returned or scrapped, and for a sorted lot, it is the number of defective pieces found during the sort |

Rules:
1. Defective pieces found in the sample of an accepted lot are removed and counted in rejected_qty.
2. A lot rejected on the sample counts the entire lot in rejected_qty, because the PPM calculation reflects the quantity not accepted.
3. Each rejected unit is assigned a defect code from GLS-QUA-001 and an NCR (QP-8.7) with source "Incoming Inspection" is opened for any rejected quantity.
4. Records are entered on the same shift. Inspector, date, supplier, material and PO are mandatory.

## 5. Lot Outcomes

| Outcome | When used | Consequence |
|---|---|---|
| ACCEPT | Defects found are at or below the accept number, no critical defects | Lot released to stock |
| ACCEPT WITH DEVIATION | Lot fails the plan, but is used under a documented deviation approved by the plant quality manager (and the customer if required) for a limited quantity, for example to avoid a line stoppage after containment sorting | Lot released with a deviation number; an NCR with the disposition Use As Is or Sort & Rework is opened; the supplier is notified |
| REJECT | Defects exceed the reject number, or any critical defect is found | Lot stays blocked; NCR disposition Return to Vendor, Scrap or Sort & Rework; supplier is notified |

ACCEPT WITH DEVIATION is never permitted for a characteristic with a safety or regulatory requirement.

## 6. Supplier PPM Calculation

Supplier PPM = rejected quantity / received quantity x 1,000,000

PPM is calculated monthly per supplier using rejected_qty and received_qty summed across all lots received in the month. It is reported against the supplier's limit.

Worked example: A supplier ships 10,000 pieces in a month and 5 are rejected, so PPM = 5 / 10,000 x 1,000,000 = 500 PPM. 

Reference limits: SUP-1007 Brightline Castings 500 PPM; SUP-1002 Keystone Foundry 500 PPM; SUP-1003 Silesia Metalworks 250 PPM. Brightline's PPM was 237 before May 2026 and 2,726 after (see SCAR-2026-014).

## 7. Supplier Notification and Escalation

- A single rejected lot: the supplier is notified in 2 business days.
- Monthly PPM above the limit: supplier quality engineer opens a SCAR (QP-10.2, supplier agreement escalation levels).
- Two consecutive months above the limit after a SCAR: escalate per the supplier quality agreement (for Brightline, Level 2 controlled shipping).

## 8. Records

Inspection records are kept for 10 years. Calibration status of every gauge used is verified before inspection.

## 9. Revision History

| Rev | Date | Change |
|---|---|---|
| 5 | 2024-08-26 | Added tightened inspection for suppliers under SCAR |
| 6 | 2025-12-01 | Clarified inspected_qty and rejected_qty recording for rejected lots; added ACCEPT WITH DEVIATION rules |
