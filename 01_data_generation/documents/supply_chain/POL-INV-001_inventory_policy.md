# Inventory Policy

| Field | Value |
|---|---|
| Document ID | POL-INV-001 |
| Title | Inventory Policy – Safety Stock, Reorder Points and Days-of-Supply Targets |
| Revision | Rev D |
| Effective date | 2026-01-05 |
| Owner | Priya Nair, Director of Supply Chain & Logistics |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose and Scope

This policy sets inventory targets and replenishment rules for KK's Parts. It covers finished goods held at the distribution centers DC-MEM (Memphis), DC-RNO (Reno) and DC-RTM (Rotterdam), and raw materials held at the plant warehouses WH-CLB, WH-GVL, WH-MTY, WH-WRO and WH-PNQ.

## 2. Definitions

| Term | Definition |
|---|---|
| On-hand | Physical quantity in stock |
| Allocated | Quantity committed to released customer or production orders |
| Available | On-hand minus allocated |
| Average daily demand | Rolling 90-day average of daily consumption or shipments |
| Days of supply | On-hand divided by average daily demand |
| Stockout | A condition in which **on-hand is less than allocated** |
| Lead time | Days from purchase order or transfer order release to receipt |

## 3. Safety Stock

3.1 Safety stock protects against demand variation and supplier lead-time variation. It is expressed as days of supply and converted to units using average daily demand.

3.2 Targets by item type and location:

| Item type | Location | Safety stock (days) | Target days of supply | Maximum days of supply |
|---|---|---|---|---|
| Finished Good | DC-MEM, DC-RNO, DC-RTM | 10 | 30 | 45 |
| Raw Material – castings (MAT-5001 to MAT-5005) | WH-CLB, WH-GVL, WH-MTY | 14 | 35 | 50 |
| Raw Material – other | WH-CLB, WH-GVL, WH-MTY, WH-WRO, WH-PNQ | 10 | 28 | 42 |

3.3 Safety stock for a material sourced from a supplier rated Red on the supplier scorecard (currently SUP-1007 Brightline Castings, see SCR-2026-Q3) is temporarily increased to **21 days** until the supplier has three consecutive months at or above the on-time target. The increase is funded as working capital and reviewed monthly by the Director of Supply Chain & Logistics.

## 4. Reorder Point

4.1 Reorder point (ROP) = (average daily demand x supplier lead time in days) + safety stock units.

4.2 Example: average daily demand of 200 units, lead time of 42 days (6 weeks) and 14 days of safety stock gives ROP = 200 x 42 + 200 x 14 = 11,200 units.

4.3 An order is raised when available stock plus open inbound orders falls to or below the ROP. Order quantity targets the item's target days of supply, rounded to the supplier's lot size.

4.4 Planners review ROP and safety stock parameters quarterly, and sooner when a supplier's on-time delivery changes by more than 10 points or when a lead time changes.

## 5. Stockout Management

5.1 A stockout is recorded for any item-location where on-hand is less than allocated at the daily snapshot. Zero on-hand with no allocation is not a stockout.

5.2 The stockout rate for a location is the number of stocked-out item-days divided by total item-days. The target for finished goods at DCs is below 2%.

5.3 Every stockout on a Strategic customer item is reviewed within 1 business day by the DC Logistics Manager.

## 6. Days-of-Supply Exceptions

| Condition | Action |
|---|---|
| Days of supply below safety stock days | Immediate expedite review; notify the Director of Supply Chain & Logistics |
| Days of supply below half of safety stock days | Treat as a critical shortage; consider premium freight and production resequencing |
| Days of supply above maximum | Stop replenishment; review for excess and obsolescence |

## 7. Expedite and Premium Freight Rules

7.1 Premium freight is any air, team-driver or expedited LTL/FTL freight used to recover a delivery that standard transport would not meet.

7.2 Approval thresholds:

| Premium freight cost per shipment | Approver |
|---|---|
| Up to USD 2,500 | DC or plant Logistics Manager (for example Brian Wilson for DC-MEM) |
| USD 2,501 to USD 10,000 | Director of Supply Chain & Logistics (Priya Nair) |
| Above USD 10,000 | VP Operations (Dana Whitfield) |

7.3 Every premium freight shipment must record a reason code: Supplier Late, Production Shortage, Customer Escalation, Carrier Failure or Demand Spike.

7.4 Where the cause is a supplier's late delivery, the cost is charged back to the supplier under the supply agreement (for Brightline, MSA-BLC-2023 clause 4.2). Where the cause is a carrier failure, the cost is claimed from the carrier.

7.5 Expedite of production orders to cover a material shortage must be agreed between the plant manager and Supply Chain, and the associated downtime is recorded in the MES with reason code "Material Shortage".

## 8. Excess and Obsolete

Items with no demand for 12 months, or days of supply above 180, are reviewed quarterly for reserve, disposal or rework.

## 9. Governance

The policy is reviewed annually. Exceptions require written approval from the Director of Supply Chain & Logistics. Monthly inventory health (days of supply, stockout rate, excess) is presented at the S&OP meeting (see SOP-MIN-2026-08).

## 10. Revision History

| Rev | Date | Change |
|---|---|---|
| C | 2025-01-06 | Added premium freight thresholds |
| D | 2026-01-05 | Added red-supplier safety stock uplift and casting targets |
