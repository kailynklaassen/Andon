# Vibration Monitoring Standard

| Field | Value |
|---|---|
| Document ID | STD-MNT-010 |
| Title | Vibration Monitoring Standard |
| Revision | Rev 2 |
| Effective date | 2025-10-01 |
| Owner | Marcus Okafor, Director of Reliability & Maintenance |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose and Scope

This standard defines how vibration is measured, evaluated, alarmed and stored for rotating equipment and machine tool spindles at KK's Parts plants. It applies to all A-critical and B-critical assets with rotating elements and to CNC spindles in particular.

## 2. Governing Principle: OEM Limits Prevail

Evaluation limits are taken from the OEM service manual for the specific machine. Where the OEM defines alert and replace limits, these are adopted as the alarm set points. Generic ISO 10816 zones are used only where no OEM limit exists. A KK's Parts internal procedure must never set a limit looser than the OEM value. For Hartwell HMC-Series spindles the limits are 3.5 mm/s (alert) and 4.5 mm/s (replace), per OEM-HMT-HMC-SM7 section 7.4.

## 3. Monitoring Methods

| Method | Description | Frequency | Typical use |
|---|---|---|---|
| Route-based (handheld) | Technician measures at defined points with a handheld meter and records in the CMMS | Monthly (PM), weekly at alert level | B and C assets, and A assets without sensors |
| Online sensors | Fixed accelerometer at the measurement point streaming to the IoT historian | Continuous (hourly aggregates) | A-critical assets |
| Periodic spectrum analysis | Vibration analyst captures FFT spectrum and bearing defect frequencies | Quarterly, or on alert | A-critical assets and diagnosis |

Online sensors are the preferred method for A-critical assets. Handheld readings taken during PM supplement but do not replace online alarms.

## 4. Measurement Conditions

1. Measure overall velocity in mm/s RMS.
2. Take readings at the same point each time (for a machining center, the spindle nose housing).
3. Run the spindle unloaded at the OEM test speed after warm-up (Hartwell: 6,000 rpm, 20 minutes).
4. Record the machine state; values taken while idle or in a changeover are not compared to running limits.

## 5. ISO 10816 Zones

| Zone | Meaning | Action |
|---|---|---|
| A | Newly commissioned machines | None |
| B | Acceptable for unrestricted long-term operation | None |
| C | Unsatisfactory for long-term operation | Plan corrective action |
| D | Vibration severe enough to cause damage | Stop or restrict; immediate action |

For Hartwell HMC-Series spindles, the OEM places the replacement limit (4.5 mm/s) at the zone C/D boundary for the machine class.

## 6. Alarm Handling

| Level | Trigger | Required response | Time limit |
|---|---|---|---|
| Normal | At or below OEM normal (Hartwell: 2.8 mm/s) | None | |
| Alert | At or above OEM alert (Hartwell: 3.5 mm/s) | Weekly readings; inspect lubrication; reliability engineer reviews trend | 5 working days |
| Replace | At or above OEM replace limit (Hartwell: 4.5 mm/s) | Raise Critical Corrective work order; restrict duty; order cartridge or bearings; notify Maintenance Manager and Director of Reliability & Maintenance | Same shift |
| Trend alarm | Monthly average rises more than 25% over a 60-day baseline | Reliability engineer review | 5 working days |

Alarms may not be cleared or the set point raised without written approval from the Director of Reliability & Maintenance.

## 7. IoT Historian Data

Online and condition data are stored in the IoT historian at hourly resolution. The telemetry fields are:

| Field | Description | Unit |
|---|---|---|
| machine_id | Work center ID, for example GVL-L3-WC01 | text |
| timestamp | Reading time (hourly) | UTC |
| machine_state | Running, Idle, Down, Setup | text |
| vibration_mm_s | Overall vibration velocity, RMS | mm/s |
| temperature_c | Spindle/bearing housing temperature | degrees C |
| motor_load_pct | Spindle motor load | percent |
| power_kw | Electrical power draw | kW |

Running-state vibration is used for limit comparison. Typical normal running vibration for GVL-L3-WC01 is approximately 2.8 mm/s. Rising vibration with rising temperature_c and motor_load_pct at constant cut is a signature of bearing wear.

## 8. Roles

| Role | Responsibility |
|---|---|
| Maintenance technician | Take route readings; escalate alarms |
| Reliability engineer | Weekly trend review, spectrum analysis, set point management |
| Maintenance Manager | Ensure actions are completed in the time limits |
| Director of Reliability & Maintenance | Own this standard; approve exceptions |

## 9. Gaps and Improvement Actions (FY2026)

1. Online sensors on all A-critical CNC spindles with alarms at OEM alert and replace limits (action in RCA-2026-GVL-007).
2. Align PM-CNC-030 with OEM limits (MOC-2026-031).
3. Add a CMMS rule that auto-raises a Corrective work order when a recorded reading reaches the replace limit.
