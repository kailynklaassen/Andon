# KK's Parts PM Procedure — CNC Machining Centers (30-Day)

| Field | Value |
|---|---|
| Document ID | PM-CNC-030 |
| Title | Preventive Maintenance Procedure, CNC Machining Centers (30-Day) |
| Revision | Rev C |
| Effective date | 2019-04-15 |
| Owner | Corporate Reliability & Maintenance (Marcus Okafor, Director) |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |
| Status | Active. **Not revised since 2019.** Revision proposed under MOC-2026-031 (pending) |

## 1. Purpose

This procedure defines the monthly (30-day) preventive maintenance tasks for CNC machining centers at all KK's Parts plants. It is executed as a Preventive work order (see POL-MNT-001) and recorded in the CMMS.

## 2. Scope

Applies to CNC horizontal and vertical machining centers, including Hartwell Machine Tools machines (GVL-L3-WC01, MTY-L2-WC01, MTY-L2-WC02, CLB-L1-WC01) and machines from other OEMs such as Sato Precision (for example GVL-L3-WC02). Lathes and other CNC machine types are covered by separate procedures.

## 3. Safety

1. Apply lockout/tagout before any task requiring guard removal. Spindle vibration measurement is performed with guards closed.
2. Wear safety glasses and cut-resistant gloves when handling tooling.
3. Confirm the machine is cool before opening the way covers.

## 4. Tools and Materials

Handheld vibration meter (mm/s RMS), grease gun and approved grease, lint-free wipes, coolant refractometer, torque wrench, PM checklist form (Appendix A).

## 5. Procedure

| Step | Task | Acceptance criterion | Est. time |
|---|---|---|---|
| 5.1 | Clean chip conveyor, way covers and chip trays | No chip buildup | 20 min |
| 5.2 | Check way lubrication reservoir; top off | Level above minimum mark | 5 min |
| 5.3 | Check coolant concentration and level; skim tramp oil | Concentration 7 to 9% | 10 min |
| 5.4 | Inspect and clean tool changer arm and magazine pockets | No debris, smooth indexing | 15 min |
| 5.5 | Check pallet changer clamp function and pallet seating | Clamp confirmation, no leaks | 10 min |
| 5.6 | Check hydraulic unit level and pressure | Within nameplate range | 5 min |
| 5.7 | Inspect air filter/regulator; drain moisture | Pressure 5.5 to 6.5 bar | 5 min |
| 5.8 | Vibration check at spindle (see Section 6) | Below action limit | 10 min |
| 5.9 | Inspect electrical cabinet filters and cooling fans | Clean, fans running | 10 min |
| 5.10 | Run warm-up program and verify no alarms | No alarms | 10 min |

Total estimated duration: approximately 100 minutes of machine downtime.

## 6. Vibration Check

1. Run the spindle unloaded at 6,000 rpm for 20 minutes.
2. With the handheld meter, measure overall velocity (mm/s RMS) at the spindle housing in the radial direction.
3. Record the reading on the checklist.
4. Compare against the action limit below.

| Reading (mm/s RMS) | Action |
|---|---|
| Below 7.1 | Within PM-CNC-030 limit. Record and continue. |
| **7.1 or above** | **Action limit reached. Raise a Corrective work order to inspect and replace the spindle bearings.** |

Note: the action limit of 7.1 mm/s was set in 2019 from historical field experience across the older machine fleet and is applied uniformly to all CNC machining centers regardless of OEM.

## 7. Record-Keeping

1. Complete Appendix A on the day of the PM and attach it to the work order.
2. Record the vibration value in the CMMS reading field; the work order status becomes Completed when all steps are signed off.
3. Retain PM records for a minimum of five years.
4. A PM that is not performed by its due date must be deferred under POL-MNT-001; the deferral reason is recorded on the work order.

## 8. Responsibilities

| Role | Responsibility |
|---|---|
| Maintenance technician | Perform and record the PM |
| Maintenance manager (plant) | Ensure completion by due date; approve deferrals as per POL-MNT-001 |
| Reliability engineer | Review vibration trends quarterly |

## 9. Document Control

| Rev | Date | Description |
|---|---|---|
| A | 2013-06-03 | Initial issue |
| B | 2016-09-12 | Added pallet changer check |
| C | 2019-04-15 | Added vibration check at 7.1 mm/s; reformatted checklist |

**Review status:** This procedure was due for periodic review in 2021 and has not been revised since Rev C (2019). It has not been reconciled with the OEM service manuals issued since 2019, including Hartwell OEM-HMT-HMC-SM7 Rev 9. A change request to align the vibration limit with the OEM value was submitted as MOC-2026-031 in July 2026 and is awaiting engineering approval.
