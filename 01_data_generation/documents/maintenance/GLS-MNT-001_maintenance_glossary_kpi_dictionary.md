# Maintenance Glossary and KPI Dictionary

| Field | Value |
|---|---|
| Document ID | GLS-MNT-001 |
| Title | Maintenance Glossary and KPI Dictionary |
| Revision | Rev 2 |
| Effective date | 2025-10-01 |
| Owner | Marcus Okafor, Director of Reliability & Maintenance |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose

This glossary standardizes maintenance terms and KPI formulas so that dashboards, Genie spaces and reports calculate them the same way. Formulas match the gold metric views.

## 2. KPI Definitions

| KPI | Definition / formula | Unit | Notes |
|---|---|---|---|
| PM compliance | Completed Preventive work orders divided by Preventive work orders due | % | Corporate target 95%; see POL-MNT-001 |
| MTBF (mean time between failures) | Run hours divided by failure count | hours | Higher is better |
| MTTR (mean time to repair) | Repair hours divided by failure count | hours | Lower is better |
| OEE | Availability x Performance x Quality | % | Corporate target 85% |
| Availability | Run minutes divided by planned minutes | % | Planned minutes = 450 per shift |
| Backlog | Open, Scheduled and Deferred work orders not yet completed | count / weeks | Backlog weeks = backlog labor hours divided by weekly available labor hours |
| Wrench time | Hands-on tool time divided by total paid technician time | % | Industry benchmark 45 to 55% |
| Planned maintenance percentage | Preventive plus planned Corrective hours divided by total maintenance hours | % | Target 80% or higher |
| Emergency work ratio | Emergency work orders divided by all work orders | % | Lower is better |
| Breakdown count | Emergency and Corrective work orders coded to a failure | count | |
| Maintenance cost | Parts plus labor plus contractor cost on a work order | USD | |

## 3. Worked Example

For GVL-L3-WC01 since 2026-03-15: 30 breakdowns and approximately 286 repair hours give an MTTR of about 9.5 hours per failure. Plant PM compliance of 80.6% at Greenville compares to the 95% policy target.

## 4. Work Order Terms

| Term | Meaning |
|---|---|
| Preventive WO | Scheduled PM (see POL-MNT-001) |
| Corrective WO | Planned repair of a condition found before breakdown |
| Emergency WO | Unplanned repair after a breakdown |
| Priority | Medium, High or Critical |
| Status | Open, Scheduled, In Progress, Deferred, Completed, Cancelled |
| Deferral | Approved postponement of a PM |
| MOC | Management of Change request |
| RCA | Root cause analysis |
| CAPA | Corrective and preventive action record (owned by Quality) |

## 5. Condition Monitoring Terms

| Term | Meaning |
|---|---|
| mm/s RMS | Overall vibration velocity |
| Alert limit | OEM level that triggers increased monitoring (Hartwell spindle: 3.5 mm/s) |
| Replace limit | OEM level at which the component must be replaced (Hartwell spindle: 4.5 mm/s) |
| ISO 10816 | Standard classifying machine vibration into zones A to D |
| Preload | Axial force applied to spindle bearings to remove clearance |
| IoT historian | Time series store of machine_state, vibration_mm_s, temperature_c, motor_load_pct and power_kw |
| Criticality | A, B or C (STD-MNT-004) |
| Downtime reason codes | Equipment Failure, Planned Maintenance, Changeover, Material Shortage, Quality Hold, No Operator |

## 6. CNC Machine Failure Modes

| Failure mode | Description | Typical indicators |
|---|---|---|
| Spindle bearing wear | Degraded bearings, lubrication or preload in the spindle cartridge | Rising vibration and temperature, bore drift, growl |
| Pallet changer fault | Pallet clamp, seating or rotation failure | Clamp confirmation alarm, pallet not seated |
| Tool changer fault | Arm, magazine or tool-clamp failure | Tool change timeout, dropped tool |
| Coolant pump failure | Pump, filter or line failure; low flow | Coolant flow alarm, part temperature rise |
| Servo drive fault | Axis drive, encoder or amplifier fault | Axis following error, drive overcurrent |
| Hydraulic unit leak | Loss of hydraulic pressure | Low pressure alarm |
| Way lubrication failure | Insufficient way oil | Lube alarm, axis friction |
| Chip conveyor jam | Chips blocking the conveyor | Conveyor overload |
| Controller / electrical fault | CNC or cabinet fault | Controller alarm, intermittent stops |

Spindle bearing wear is the dominant failure mode on GVL-L3-WC01 in FY2026 (see RCA-2026-GVL-007).

## 7. Related Documents

POL-MNT-001, STD-MNT-004, STD-MNT-010, PM-CNC-030, OEM-HMT-HMC-SM7.
