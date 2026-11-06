# Maintenance Strategy and PM Compliance Policy

| Field | Value |
|---|---|
| Document ID | POL-MNT-001 |
| Title | Maintenance Strategy and PM Compliance Policy |
| Revision | Rev 3 |
| Effective date | 2025-10-01 (start of FY2026) |
| Owner | Marcus Okafor, Director of Reliability & Maintenance |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose and Scope

This policy sets the maintenance strategy, the preventive maintenance (PM) compliance target, the work order taxonomy and the deferral rules for all KK's Parts plants: Columbus (CLB), Greenville (GVL), Monterrey (MTY), Wroclaw (WRO) and Pune (PNQ).

## 2. Strategy

1. Preventive maintenance is performed on a calendar or usage basis and, wherever sensor data exists, is supplemented by condition-based triggers.
2. Where an OEM manual defines a condition limit (for example a vibration limit), the OEM limit governs. Internal procedures may be stricter than the OEM but never looser.
3. Maintenance effort is prioritized by asset criticality (STD-MNT-004).
4. Condition monitoring is performed according to STD-MNT-010.

## 3. PM Compliance Target

| Level | Target |
|---|---|
| Corporate policy target | **95%** |
| Plant targets (FY2026 operating plan) | CLB 97%, GVL 84%, MTY 90%, WRO 92%, PNQ 91% |

Plant targets below 95% are temporary glide-path values approved for FY2026 and must reach 95% by FY2028. Plants below their plant target for two consecutive months must submit a recovery plan to the Director of Reliability & Maintenance.

### 3.1 How PM compliance is calculated

PM compliance = completed Preventive work orders divided by Preventive work orders due in the period.

- A PM is "due" when its scheduled due date falls in the reporting period.
- A PM counts as completed only if its work order status is Completed and it was finished within the period of its due date (plus the grace window below).
- Deferred PMs remain in the denominator and do not count as completed unless completed within the period.
- Grace window: 7 days for monthly PMs, 14 days for quarterly or longer.
- Corrective and Emergency work orders are excluded from the calculation.

## 4. Work Order Types

| Type | Definition | Examples |
|---|---|---|
| Preventive | Planned, scheduled work to prevent failure | Monthly CNC PM (PM-CNC-030), lubrication rounds |
| Corrective | Planned repair of a condition found before functional failure | Bearing replacement raised at a PM |
| Emergency | Unplanned response to a breakdown that stops production | Spindle seizure, servo drive fault |

## 5. Priorities

| Priority | Definition | Response target |
|---|---|---|
| Critical | Stops production on an A-critical asset or creates a safety risk | Start within 1 hour |
| High | Stops or severely limits a B-critical asset, or has quality impact | Start within 4 hours |
| Medium | No immediate production impact | Start within 3 working days |

## 6. Work Order Status Values

| Status | Meaning |
|---|---|
| Open | Created, not yet scheduled |
| Scheduled | Assigned a date and resources |
| In Progress | Work started |
| Deferred | Approved for postponement under Section 7 |
| Completed | All steps signed off and recorded |
| Cancelled | Not required; reason recorded |

## 7. PM Deferral Rules

| Asset criticality | Who may approve a deferral | Maximum |
|---|---|---|
| A | Plant Maintenance Manager **and** Plant Manager | **1 consecutive deferral**; a second requires approval by the Director of Reliability & Maintenance |
| B | Plant Maintenance Manager | 2 consecutive deferrals |
| C | Maintenance Supervisor | 3 consecutive deferrals |

1. A deferral request must state the reason, the risk, the compensating action and the new date.
2. A deferral may not be approved if the latest condition reading is at or above the OEM alert level without a documented risk assessment.
3. Production scheduling pressure alone is not sufficient reason to defer an A-critical PM.
4. Deferred PMs are reviewed in the weekly reliability stand-up.

## 8. Reporting

PM compliance is reported monthly by plant, line and criticality in the reliability dashboard. The Director of Reliability & Maintenance issues a quarterly review to the VP Operations. Exceptions are escalated per the reliability memo process (see MEMO-REL-2026-09).

## 9. Document Control

| Rev | Date | Change |
|---|---|---|
| 1 | 2020-01-15 | Initial policy |
| 2 | 2023-02-06 | Added criticality-based deferral rules |
| 3 | 2025-10-01 | Added OEM-governs clause and plant glide-path targets |
