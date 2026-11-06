# Supply Chain Glossary and KPI Dictionary

| Field | Value |
|---|---|
| Document ID | GLS-SCM-001 |
| Title | Supply Chain Glossary and KPI Dictionary |
| Revision | Rev B |
| Effective date | 2026-03-02 |
| Owner | Priya Nair, Director of Supply Chain & Logistics |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

This glossary defines the supply chain, warehousing and logistics terms used in KK's Parts reports, dashboards and the Supply Chain Genie space. Where a definition matches a data-model metric, the definition here is the authoritative business meaning.

## 1. KPI Definitions

| Term | Definition | Formula / rule | Target |
|---|---|---|---|
| Supplier OTD (on-time delivery) | Share of supplier receipts that arrive on or before the promised date | Receipts with days late = 0 / total receipts | 95% (contract target, for example SUP-1007 under MSA-BLC-2023) |
| Days late | Calendar days a receipt arrives after the promised date | Receipt date minus promised date, minimum 0 | 0 |
| Average days late (when late) | Mean days late across late receipts only | Sum of days late / number of late receipts | n/a |
| PPM (supplier parts per million) | Incoming defect rate | Rejected qty / received qty x 1,000,000 | Per supplier agreement; 500 for Brightline and Keystone, 250 for Silesia |
| Lead time | Days from purchase order release to receipt at the warehouse | Receipt date minus order date | Per agreement |
| Days of supply | How long current stock lasts at current demand | On-hand / average daily demand | See POL-INV-001 |
| Stockout | On-hand is less than allocated | On-hand < allocated | Stockout rate below 2% for DC finished goods |
| Safety stock | Buffer held against variability | Days of supply converted to units | See POL-INV-001 |
| Reorder point | Stock level that triggers replenishment | Demand x lead time + safety stock | n/a |
| Carrier on-time | Share of shipments delivered on or before the carrier due date | Delivered date <= carrier due date | 95% (SLA, CTA-RF-2024-07) |
| Carrier due date | Date the carrier is obliged to deliver | Ship date + planned transit days | n/a |
| Customer OTIF (on-time, in-full) | Share of orders delivered on or before the customer-requested date and in full quantity | Delivered date <= requested date AND delivered qty >= ordered qty | 95% for Strategic customers such as CUST-2001 |
| Freight cost per shipment | Average transportation cost per shipment | Total freight cost / number of de-duplicated shipments | Tracked by carrier and lane |
| Premium freight | Air, team-driver or expedited freight used to recover a delivery | Freight with a premium reason code | Minimize; see POL-INV-001 section 7 |
| Service credit | Contractual credit from a carrier for missed on-time performance | 2% of monthly freight spend per point below 92% (Ridgeway) | n/a |

## 2. Important Distinctions

2.1 **Carrier on-time versus customer OTIF.** Carrier on-time compares delivery to the carrier due date (ship date plus planned transit days). Customer OTIF compares delivery to the date the customer requested and also requires the full quantity. A shipment can be on time to the carrier and still late to the customer, and the reverse.

2.2 **Supplier OTD** is measured at receipt, against the promised date, not the original requested date.

2.3 **Stockout versus zero stock.** Zero on-hand with no allocation is not a stockout. A stockout requires on-hand to be below allocated.

2.4 **De-duplication.** Carrier EDI resends may create duplicate rows; reports use one row per shipment ID (see SOP-WMS-002).

2.5 **Related quality metrics** such as NCR counts, COPQ and SCAR/CAPA status are defined by the Quality function and referenced by ID only (for example SCAR-2026-014, CAPA-2026-101).

## 3. Warehouse Reference

| Warehouse ID | Name | City | Type |
|---|---|---|---|
| WH-CLB | Columbus plant warehouse | Columbus, OH, USA | Plant warehouse (raw materials) |
| WH-GVL | Greenville plant warehouse | Greenville, SC, USA | Plant warehouse (raw materials) |
| WH-MTY | Monterrey plant warehouse | Monterrey, NL, Mexico | Plant warehouse (raw materials) |
| WH-WRO | Wroclaw plant warehouse | Wroclaw, Poland | Plant warehouse (raw materials) |
| WH-PNQ | Pune plant warehouse | Pune, MH, India | Plant warehouse (raw materials) |
| DC-MEM | Memphis Distribution Center | Memphis, TN, USA | Distribution center (finished goods) |
| DC-RNO | Reno Distribution Center | Reno, NV, USA | Distribution center (finished goods) |
| DC-RTM | Rotterdam Distribution Center | Rotterdam, Netherlands | Distribution center (finished goods) |

## 4. Carrier Reference

| Carrier ID | Carrier | Mode |
|---|---|---|
| CAR-01 | Summit Logistics | LTL |
| CAR-02 | BlueLine Express | Parcel |
| CAR-03 | TransAmerica Truckload | FTL |
| CAR-04 | Ridgeway Freight | LTL |
| CAR-05 | Coastal Intermodal | Intermodal |
| CAR-06 | Rhine-Maas Transport | FTL |
| CAR-07 | EuroSprint Cargo | LTL |
| CAR-08 | Pacific Rim Forwarding | Ocean/Air |

Note: LTL = less than truckload; FTL = full truckload.

## 5. Supplier Reference (castings)

| Supplier ID | Supplier | Location | Notes |
|---|---|---|---|
| SUP-1007 | Brightline Castings | Saltillo, Mexico | MAT-5001, 5002, 5004, 5005; PPM limit 500; on-time target 95% |
| SUP-1002 | Keystone Foundry | Erie, USA | MAT-5003; PPM limit 500 |
| SUP-1003 | Silesia Metalworks | Katowice, Poland | PPM limit 250 |

## 6. Customer Reference

CUST-2001 Apex Agricultural Equipment is a Strategic account served from DC-MEM and requires 95% OTIF.

## 7. Fiscal Calendar

Fiscal year 2026 runs from 2025-10-01 to 2026-09-30. Q1 is October to December, Q2 January to March, Q3 April to June, Q4 July to September.

## 8. Related Documents

MSA-BLC-2023, CTA-RF-2024-07, SCR-2026-Q3, POL-INV-001, SOP-WMS-002.
