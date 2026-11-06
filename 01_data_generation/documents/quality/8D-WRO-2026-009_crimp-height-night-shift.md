# 8D Report: Crimp Height Variation, WRO-L1-WC02 Night Shift

| Field | Value |
|---|---|
| Document ID | 8D-WRO-2026-009 |
| Title | 8D Report, Crimp Height Variation on WRO-L1-WC02 Night Shift (C Shift) |
| Revision | Rev 2 (in progress, status as of 2026-09-22) |
| Opened | 2026-07-08 |
| Owner | Tomasz Wisniewski, Wroclaw Quality Engineer |
| Approver | Katarzyna Nowak, Wroclaw Plant Manager; Elena Ramirez, Director of Quality |
| Linked CAPA | CAPA-2026-102 (In Progress; due 2026-08-22) |
| Classification | Internal |

## D1. Team

| Role | Name |
|---|---|
| Team leader | Tomasz Wisniewski, Quality Engineer |
| Sponsor | Katarzyna Nowak, Plant Manager |
| C-shift supervisor | Marek Kaminski |
| Members | WRO-L1 process engineer, maintenance technician (Terminal Crimp Press #2), training coordinator, document control |

## D2. Problem Description

| Item | Detail |
|---|---|
| Machine | WRO-L1-WC02, Terminal Crimp Press #2 (Lumex Equipment, model LUM-486), Wire Cut & Crimp line |
| Characteristic | Crimp height 1.650 mm +/- 0.050 mm (CP-WRO-L1 Rev F), critical characteristic |
| Event | Crimp die change on 2026-06-08 |
| Observed | In-process defect rate (code: Crimp height out of spec) of **13.6% on C shift** against about 1.4% to 1.5% on A and B shifts. Before 2026-06-08 all shifts ran at about 1.2% to 1.5% |
| Is / Is not | Is: C shift, WC02, after the die change. Is not: A and B shifts; WC03 (Terminal Crimp Press #3); before 2026-06-08 |
| Impact | Higher scrap and rework NCRs, additional sorting, lower C-shift FPY, risk of escapes to harness assembly (WRO-L2) |

## D3. Interim Containment (complete)

1. Effective 2026-07-08, C-shift 100% crimp height check at first piece, every 30 minutes and after every reel change, by micrometer-based crimp height gauge.
2. Pull force testing frequency on C shift raised from once per hour to every 30 minutes at WC04 (Crimp Pull Tester).
3. All C-shift production since 2026-06-08 held, sorted and reworked or scrapped; no suspect material was shipped (verified against lot traceability).
4. Quality Hold used when two consecutive out-of-spec readings were found (logged in the MES as "Quality Hold").

## D4. Root Cause (complete, verified)

| Cause | Finding | Verification |
|---|---|---|
| Occurrence 1 | C-shift setup was performed using the superseded work instruction **WI-WRO-CR-07 Rev D** (die shut-height setting) instead of **Rev E**. Rev D carried an outdated shut-height offset | Printed Rev D copy found at the press; setup record compared; replicating Rev D setting produced a crimp height of 1.71 mm |
| Occurrence 2 | The **crimp force monitor alarm thresholds were widened** during the 2026-06-08 die change and **not restored** afterwards | Monitor configuration log compared with the validated parameters |
| Systemic cause | C shift has had **no Level 3 certified setter since May 2026**, so die setup was performed without the required certified verification | Training matrix and shift roster review |
| Escape cause | Widened thresholds allowed out-of-tolerance crimps to pass the force monitor; the sampling check did not detect the drift quickly enough | Control chart review |

Document control did not remove Rev D from the point of use when Rev E was released.

## D5. Permanent Corrective Actions (partly complete)

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | Remove Rev D from all stations; issue Rev E only at point of use | Document control | 2026-07-15 | Complete |
| 2 | Restore crimp force monitor thresholds to the validated values; lock with supervisor password | Process engineer | 2026-07-22 | Complete |
| 3 | Certify at least one Level 3 setter on C shift | Training coordinator / Marek Kaminski | 2026-09-30 | In progress (two candidates in training, assessment scheduled) |
| 4 | Add threshold verification to the die change checklist | Tomasz Wisniewski | 2026-09-30 | In progress |

## D6. Implementation and Validation (partly complete)

- Actions 1 and 2 are implemented. Validation is not complete: the process data since 2026-06-08 still show a C-shift in-process defect rate of 13.6% against 1.4% to 1.5% on A and B shifts, so effectiveness has not yet been demonstrated.
- Actions 3 and 4 not yet implemented. Interim containment (D3) therefore remains in place and will be removed only after a Level 3 setter is certified and effectiveness is demonstrated.
- Capability study on WC02 C shift since the die change: Cpk 0.33 (A and B shifts 1.34; target at least 1.33 under CP-WRO-L1). Before the die change C shift was at Cpk 1.33.

## D7. Prevent Recurrence (in progress)

| Action | Status |
|---|---|
| Update CP-WRO-L1 reaction plan to require threshold verification after any die change | Drafted for Rev G |
| Audit all work instructions at WRO-L1 and WRO-L2 for superseded revisions at point of use | Planned, 2026-10-09 |
| Extend die change checklist and setter certification rules to WC03 and WRO-L2 presses | Planned |
| Add Level 3 setter coverage to the shift staffing rules for all three shifts | Proposed |

## D8. Closure and Recognition (not started)

D8 will be completed after the effectiveness window of 90 days (QP-10.2 Section 6) from implementation of Action 3. The CAPA will be closed by the Director of Quality.

## Status Summary

| Item | Status |
|---|---|
| D1 to D4 | Complete |
| D5 | 2 of 4 actions complete |
| D6 | Partly complete |
| D7 | In progress |
| D8 | Not started |
| CAPA-2026-102 | In Progress (extension recorded in the register) |
