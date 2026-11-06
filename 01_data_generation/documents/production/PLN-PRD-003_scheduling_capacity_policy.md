# Production Scheduling & Capacity Planning Policy

| Field | Value |
|---|---|
| Document ID | PLN-PRD-003 |
| Title | Production Scheduling & Capacity Planning Policy |
| Revision | Rev B |
| Effective Date | 2026-02-16 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Priya Nair, Director of Supply Chain & Logistics |
| Classification | Internal |

## 1. Purpose

This policy sets out how KK's Parts plans capacity and schedules production orders (manufacturing orders, "MOs") so that plants load lines realistically, protect customer commitments and respond consistently to disruptions such as machine breakdowns and material shortages.

## 2. Scope

All 15 production lines across CLB, GVL, MTY, WRO and PNQ. It covers the weekly and daily schedule, capacity calculation, the frozen zone and material-shortage handling.

## 3. Planning calendar

- Shifts: A 06:00-14:00, B 14:00-22:00, C 22:00-06:00. Monday to Friday run three shifts, Saturday runs A and B, and Sunday is dark. That is 17 shifts per standard week.
- Planned production time is 450 minutes per shift (480 minus a 30-minute break), so a standard week offers 7,650 planned minutes per line.
- Scheduled planned maintenance windows and company holidays are loaded into the calendar before orders are sequenced.

## 4. Ideal cycle times

Ideal cycle time is the fastest sustainable time per unit when the line runs without stops, in seconds per finished unit at the line's rate-setting work center. Scheduling uses these values; actual performance is measured against them (SOP-PRD-001).

| Line | Name | Ideal cycle time (s/unit) |
|---|---|---|
| CLB-L1 | Valve Body Machining | 102.81 |
| CLB-L2 | Pump Assembly | 99.84 |
| CLB-L3 | Cylinder Fabrication | 96.63 |
| GVL-L1 | Gear Hobbing | 150.86 |
| GVL-L2 | Heat Treat | 119.91 |
| GVL-L3 | Gearbox Assembly | 156.52 |
| MTY-L1 | Casting Finishing | 174.47 |
| MTY-L2 | Housing Machining | 173.21 |
| MTY-L3 | Paint & Coat | 165.78 |
| WRO-L1 | Wire Cut & Crimp | 25.35 |
| WRO-L2 | Harness Assembly | 29.40 |
| WRO-L3 | Control Module Assembly | 29.11 |
| PNQ-L1 | Cold Heading | 3.25 |
| PNQ-L2 | Stamping | 3.39 |
| PNQ-L3 | Plating & Finishing | 2.82 |

The GVL-L3 value of 156.52 s/unit (156.5 rounded) is the reference line used in training examples.

## 5. How capacity is computed

1. **Theoretical capacity per shift** = planned minutes x 60 ÷ ideal cycle time. For GVL-L3 this is 450 x 60 ÷ 156.5 = 27,000 ÷ 156.5, about 172 units per shift.
2. **Effective (planning) capacity** = theoretical capacity x planning OEE. The planning OEE is the trailing three-month line OEE, but never above the corporate 85% target.
3. **Weekly capacity** = effective capacity per shift x scheduled shifts in the week (17 for a full week).
4. Changeover time (SOP-PRD-014) is not deducted separately when planning OEE is used, because changeover loss is already inside Availability. When a schedule has a high number of changeovers, planners may apply the line-family target minutes explicitly and use a planning OEE that excludes changeover loss.

### 5.1 Worked example for GVL-L3

| Case | OEE used | Units per shift | Units per full week (17 shifts) |
|---|---|---|---|
| Corporate target | 85% | about 146 | about 2,490 |
| Normal state (March 2026) | 84% | about 145 | about 2,460 |
| August 2026 actual | 58% | about 100 | about 1,700 |

When OEE falls, planners must reduce the committed load. Loading GVL-L3 at target OEE in a month it runs near 58% creates a backlog of roughly 790 units a week.

## 6. Scheduling rules

1. Orders are sequenced by customer-requested date, then by changeover family to minimize changeovers.
2. The bottleneck (criticality A) work center sets the schedule for the line. Never release more work than the bottleneck can process.
3. Each shift schedule is published 24 hours ahead by the planner and acknowledged by the shift supervisor.
4. Strategic customers (for example CUST-2001 Apex Agricultural Equipment) have priority on allocation conflicts, then orders with the earliest requested date.

## 7. Frozen zone rules

| Horizon | Status | Who can change it |
|---|---|---|
| 0-48 hours | Frozen | Plant manager only; requires reason documented in MES |
| 48 hours-7 days | Slushy | Planner may move orders with supervisor agreement and without extra changeovers |
| Beyond 7 days | Free | Planner |

Material shortages, a machine down for more than 120 minutes, or a quality hold are valid reasons to break the frozen zone. Customer requests alone are not, unless approved by the VP Operations.

## 8. Material shortage handling

1. Material shortage is detected by the kitting check 24 hours before release and by MES downtime coded **Material Shortage**.
2. The planner checks open purchase orders and in-transit receipts. If receipt is expected within the shift, the order stays sequenced; otherwise it is deferred.
3. The planner pulls forward the next order whose materials are complete, preferring one in the same changeover family.
4. Shortages above 120 minutes are escalated per SOP-PRD-020 to the Director of Supply Chain & Logistics (Priya Nair), who may authorize expediting or air freight.
5. For supplier-driven shortages the Supplier Quality Engineer is informed. Example: the Brightline Castings (SUP-1007) situation, SCAR-2026-014 / CAPA-2026-101, and the line stop report LSR-MTY-2026-011.
6. Plants must not run on unreleased or non-conforming material to avoid a shortage code.
7. Alternate-source approvals (for example Keystone Foundry SUP-1002) require quality approval and PPAP; planners may not substitute materials.

## 9. Disruption response for a capacity loss

When a bottleneck machine's OEE drops more than 10 points below plan for two consecutive weeks (for example GVL-L3-WC01):

1. The planner recalculates effective capacity using the actual OEE.
2. The plant manager and VP Operations review customer orders at risk and agree on reallocation to other lines or overtime on Saturday A and B shifts.
3. The Director of Reliability & Maintenance is engaged for recovery actions.

## 10. Roles

| Role | Responsibility |
|---|---|
| Planners | Compute capacity, sequence orders, manage the frozen zone. |
| Plant managers | Approve changes inside the frozen zone. |
| Director of Supply Chain & Logistics | Material availability and supplier expediting. |
| VP Operations | Overall policy and cross-plant allocation. |

## 11. Related documents

SOP-PRD-001, SOP-PRD-014, SOP-PRD-020, GLS-PRD-001, PFD-ALL-001.
