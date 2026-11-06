# Columbus Best-Practice Case Study: Sustaining High OEE and PM Compliance

| Field | Value |
|---|---|
| Document ID | CS-CLB-2026-02 |
| Title | Columbus Best-Practice Case Study: How CLB Sustains High OEE and PM Compliance |
| Revision | Rev 1 |
| Report Date | 2026-09-21 |
| Owner | Kevin Thompson, Columbus Plant Manager |
| Approver | Marcus Okafor, Director of Reliability & Maintenance |
| Classification | Internal |

## 1. Purpose

This case study documents the practices that allow the Columbus Hydraulics Plant (CLB) to keep a high PM compliance rate and the lowest breakdown rate in the company, and recommends how Greenville (GVL) can adopt them. It is a companion to the Greenville review RPT-GVL-2026-08 and the Q3 operations review RPT-OPS-2026-Q3.

## 2. Results at a glance

| Measure | Columbus (CLB) | Greenville (GVL) | Corporate target |
|---|---|---|---|
| FY26 PM compliance | 96.6% | 80.6% (GVL-L3: 76.7%) | 95% policy |
| Plant PM compliance target | 97% | 84% | n/a |
| FY26 OEE | 81.3% (highest of the US plants) | 78.3% | 85% |
| Breakdown rate | Lowest in the company | Highest (driven by GVL-L3-WC01) | n/a |

Columbus does not reach the 85% OEE target either, with the remaining gap mainly from changeover and castings-supply losses (Brightline Castings, SUP-1007). But the losses are not reliability-driven, which is the key difference.

## 3. Practice 1 - Condition-based PM at OEM limits

Columbus triggers bearing and spindle work by measured condition, not by a calendar alone. For each A-critical machine the maintenance planner has loaded the **OEM-published limits** into the maintenance system. When a vibration, temperature or current reading reaches an alert limit, the system raises a work order automatically; when it reaches the replacement limit, the machine is scheduled for repair.

- Alert and replacement limits come directly from the OEM manual, for example 3.5 mm/s alert and 4.5 mm/s replacement for Hartwell HMC-series spindles.
- Internal procedures are reviewed against OEM manuals every 24 months, and any difference must go through management of change.
- PM tasks cannot be closed by a technician as "within limit" without recording the measured value and the applicable limit.

Greenville contrast: PM-CNC-030 Rev C (2019) uses a 7.1 mm/s trigger, 2.6 mm/s above the OEM replacement limit. Vibration on GVL-L3-WC01 exceeded 4.5 mm/s in June 2026 and no action was triggered until it reached 7.1 mm/s in August. MOC-2026-031 is pending to correct this.

## 4. Practice 2 - Weekly reliability stand-up

Every Tuesday at 08:00 a 30-minute stand-up reviews:

1. Machines with any reading above alert level or trending upward for three consecutive weeks.
2. All emergency and corrective work orders from the previous week, by cause.
3. Deferred PMs: a deferred PM must have a named approver, a reschedule date within 14 days and a risk statement. No PM may be deferred twice.
4. Spare parts status for A-critical machines.
5. Open actions from CAPA and root-cause reviews.

Attendees: Plant Manager, Maintenance Manager, reliability engineer, production supervisors from each shift and a quality representative. Decisions and owners are recorded in a one-page log, circulated the same day.

## 5. Practice 3 - Spare-spindle program for A-critical CNCs

For every A-critical CNC (bottleneck, no redundancy) Columbus holds either a spare spindle cartridge or a rebuilt spindle on exchange arrangement, with the OEM lead time covered by on-site stock. Spares are stored in WH-CLB, logged in the maintenance system, and replaced within one purchasing cycle of use. The investment was justified by comparing carrying cost against the cost of an extended line stop: the value of a day of bottleneck output exceeds the spare's annual carrying cost many times over.

Greenville contrast: GVL-L3-WC01 has no spare on site; the replacement cartridge has a 10-week Hartwell lead time at a quoted $68,400 installed. Cumulative repair and field-service/contractor cost since 2026-03-15 is already about $146K for field service and about $243K with parts.

## 6. Supporting behaviors

- **Reason-code discipline.** Operators code downtime correctly under SOP-PRD-001; supervisors audit 20 events a week.
- **PM scheduling is protected.** Planned maintenance windows are in the production calendar and are not removed to meet shipments (PLN-PRD-003). Greenville deferred PMs due 2026-06-27 and 2026-09-04.
- **OEM relationships.** Field service agreements with response times are in place before a failure.
- **Daily management.** Handover logs list machines in a degraded state (SOP-PRD-020).

## 7. Recommendations for Greenville

| # | Recommendation | Owner | Target date |
|---|---|---|---|
| 1 | Approve MOC-2026-031 and align PM-CNC-030 to the OEM 4.5 mm/s limit; audit all other CNC PM procedures against OEM manuals | Marcus Okafor | 2026-10-15 |
| 2 | Start a weekly reliability stand-up at GVL based on the Columbus agenda | Luis Hernandez, Ashley Taylor | 2026-09-29 |
| 3 | Adopt the deferred-PM rule (approver, 14-day reschedule, no double deferral) | Tom Brennan | 2026-09-30 |
| 4 | Stock a spare spindle cartridge for GVL-L3-WC01 after the current replacement and for other A-critical CNCs | Marcus Okafor, Dana Whitfield | 2026-12-15 |
| 5 | Load OEM alert and replacement limits into the maintenance system for all GVL A-critical machines | Ashley Taylor | 2026-10-30 |
| 6 | Kevin Thompson to host a two-day site visit for GVL maintenance leads | Kevin Thompson | 2026-10-09 |

## 8. Expected benefit

If Greenville reached Columbus PM compliance (about 97%) and OEM-based triggers, the expected result is a return of GVL-L3 to its pre-March OEE of around 84%, from the 58% recorded in August 2026.

## 9. Related documents

RPT-GVL-2026-08, RPT-OPS-2026-Q3, SOP-PRD-001, SOP-PRD-020, PLN-PRD-003, CAPA-2026-103.
