# Distribution Center Receiving, Put-away and Shipping SOP

| Field | Value |
|---|---|
| Document ID | SOP-WMS-002 |
| Title | Distribution Center Receiving, Put-away and Shipping |
| Revision | Rev C |
| Effective date | 2026-02-02 |
| Applies to | DC-MEM (Memphis), DC-RNO (Reno), DC-RTM (Rotterdam) |
| Owner | Brian Wilson, Logistics Manager, Memphis DC |
| Approver | Priya Nair, Director of Supply Chain & Logistics |
| Classification | Internal |

## 1. Purpose and Scope

This procedure defines how finished goods are received, put away, counted and shipped at KK's Parts' three distribution centers, and how shipment, tracking and carrier-due-date data are recorded in the Warehouse Management System (WMS). Plant warehouses (WH-CLB, WH-GVL, WH-MTY, WH-WRO, WH-PNQ) follow local work instructions aligned to this SOP.

## 2. Definitions

| Term | Meaning |
|---|---|
| Receipt | Inbound transfer of finished goods from a KK's Parts plant warehouse into a DC |
| Put-away | Moving received goods from the dock to a storage location |
| Ship date | Date the carrier takes possession at the outbound dock |
| Planned transit days | Agreed lane transit time in the carrier agreement (for example CTA-RF-2024-07) |
| Carrier due date | Ship date plus planned transit days |
| Tracking number | Carrier-assigned identifier (for LTL, the PRO number) |

## 3. Receiving

3.1 Check the inbound advance ship notice (ASN) against the dock appointment before unloading.

3.2 Inspect each pallet for visible damage; note exceptions on the delivery receipt and photograph damage before signing.

3.3 Scan the pallet label to confirm item, lot and quantity against the ASN. Variances greater than 1% of quantity or any lot mismatch are placed in the **Receiving Hold** location and raised to the Logistics Manager.

3.4 Post the receipt in the WMS on the day of arrival, no later than the end of the shift. Receipts not posted within 24 hours are escalated.

3.5 Goods with a quality concern are tagged and referred to Quality using the relevant NCR number (for example NCR numbers raised by the plant); they are not put away to pickable stock.

## 4. Put-away

4.1 The WMS directs put-away to a slot based on item velocity: fast movers in pick-face locations, slow movers in reserve racking.

4.2 Operators confirm the destination location scan. Put-away must be completed within 4 hours of receipt for standard items and 2 hours for items with open customer backorders.

4.3 Stock is allocated to customer orders when the order is released. Allocated quantity is held against the order and is not available for other orders. A stockout condition exists when on-hand is less than allocated (see POL-INV-001).

## 5. Cycle Counting

5.1 Locations are counted on an ABC schedule:

| Class | Basis | Count frequency |
|---|---|---|
| A | Top 20% of items by annual value | Monthly |
| B | Next 30% | Quarterly |
| C | Remaining 50% | Twice a year |

5.2 Count variances are recounted when above 2% of quantity or USD 500 in value. A second recount by a different operator is required before an adjustment is posted.

5.3 Inventory accuracy target is 99.0% by location. Adjustments above USD 5,000 require Logistics Manager approval.

## 6. Shipping and Shipment Records

6.1 Pick, pack and stage orders by the carrier cutoff. Cutoff for same-day pickup is 15:00 local time.

6.2 At pickup the shipper records one shipment record per bill of lading in the WMS with the following mandatory fields:

| Field | Rule |
|---|---|
| Shipment ID | Unique, system-generated |
| Order and customer ID | Linked to the sales order (for example CUST-2001) |
| Carrier ID | CAR-01 through CAR-08 |
| Ship date | Date of pickup |
| Planned transit days | Looked up from the lane table; never entered manually |
| Carrier due date | Ship date plus planned transit days; calculated by the WMS |
| Tracking number | Entered or scanned at pickup; must be present before the shipment is closed |
| Weight, pieces, freight cost | From the bill of lading and carrier rate |

6.3 Delivered date is populated only from carrier delivery events (EDI 214) or signed proof of delivery. Warehouse staff do not manually enter a delivered date.

6.4 A shipment is **on time to carrier** if delivered on or before the carrier due date. The customer's requested date is tracked separately for OTIF reporting and does not change the carrier due date.

6.5 Orders for Strategic customers with a delivery risk (carrier due date within one day of the customer-requested date) are flagged to the Logistics Manager before release. At DC-MEM this flag is applied to CUST-2001 shipments (see ESC-APEX-2026-08).

## 7. EDI Messages and Duplicate Handling

7.1 Carriers send status events by EDI. Carriers occasionally resend messages (for example after a connection timeout), which creates duplicate rows for the same event.

7.2 A duplicate is a message with the same shipment ID (or tracking number), event type and event timestamp as one already stored. Duplicates are **not** separate events and must not be counted as additional shipments, deliveries or late events.

7.3 Rules:

1. The WMS integration keeps the **first** copy received and discards later identical copies, logging each discard.
2. Where a resend carries a changed value (for example a corrected delivered timestamp), the **latest** message supersedes the earlier one, and both are retained in the audit log.
3. Reports on carrier on-time must be calculated on de-duplicated shipments, one row per shipment ID.
4. The Logistics Manager reviews the duplicate-discard log weekly. A duplicate rate above 2% of messages for a carrier is raised to the carrier at the next QBR.

## 8. Returns and Exceptions

8.1 Customer returns are received into a Returns location, inspected, and released or scrapped within 5 business days.

8.2 Shipping exceptions (missed pickup, carrier no-show, damage) are logged the same day and reported in the weekly carrier review (CPR-MEM-2026-08 for Memphis).

## 9. Records and Training

Records are retained for 7 years. Operators complete SOP training before unsupervised work and annually thereafter; the Logistics Manager at each DC maintains the training matrix.

## 10. Revision History

| Rev | Date | Change |
|---|---|---|
| A | 2023-04-10 | Initial release |
| B | 2024-09-16 | Added carrier due date calculation |
| C | 2026-02-02 | Added EDI duplicate handling and strategic customer flag |
