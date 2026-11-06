# OEE Measurement & Loss Categorization Standard

| Field | Value |
|---|---|
| Document ID | SOP-PRD-001 |
| Title | OEE Measurement & Loss Categorization Standard |
| Revision | Rev C |
| Effective Date | 2026-01-12 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Elena Ramirez, Director of Quality (data definitions co-sign); Dana Whitfield (policy) |
| Classification | Internal |
| Applies to | All KK's Parts plants: CLB, GVL, MTY, WRO, PNQ |

## 1. Purpose

This standard defines how KK's Parts measures Overall Equipment Effectiveness (OEE) and how every minute of lost production time is categorized. It ensures that OEE reported for Columbus, Greenville, Monterrey, Wroclaw and Pune is calculated the same way and can be compared fairly. The definitions here match the gold OEE metric views used for reporting.

## 2. Scope

The standard applies to every production line and work center (`<LINE>-WC<nn>`) that reports through the Manufacturing Execution System (MES), on every shift. It covers measurement of time, units and downtime. It does not cover maintenance KPIs such as MTBF, MTTR and PM compliance, which are governed by the maintenance procedures.

## 3. Definitions

| Term | Definition |
|---|---|
| Planned production time | 450 minutes per shift (480-minute shift minus a 30-minute break). |
| Run minutes | Planned production time minus all coded downtime minutes. |
| Availability | Run minutes ÷ planned minutes. |
| Performance | (Total units x ideal cycle time) ÷ run time. |
| Quality | Good units ÷ total units. |
| OEE | Availability x Performance x Quality. |
| First Pass Yield (FPY) | Good units ÷ total units. Scrap and rework both count as not-first-pass. |

Ideal cycle times are maintained per line in the scheduling master data (see PLN-PRD-003). Operators and supervisors must never overwrite an ideal cycle time on a shift result.

## 4. Shift calendar and planned time

Shifts are A 06:00-14:00, B 14:00-22:00 and C 22:00-06:00. Monday to Friday run three shifts; Saturday runs A and B; Sunday is dark. Each shift counts 450 planned minutes. Time outside these shifts, and the 30-minute break, is not planned time and is never recorded as downtime. Overtime on a dark day is recorded as a separate shift result with the same 450-minute planned basis.

## 5. Downtime reason codes

MES accepts exactly six downtime reason codes. No free-text or "Other" code is permitted. Every stop of one minute or longer on a work center must be coded before the end of the shift.

| Code | When to use | Example |
|---|---|---|
| Equipment Failure | Any unplanned stop caused by a machine fault, including time spent waiting for maintenance and repair, until the machine produces good parts again. | Spindle seizes on GVL-L3-WC01 and the line waits for the on-call technician. |
| Planned Maintenance | A stop for a scheduled preventive or condition-based work order (PM) that is on the maintenance calendar. | Monthly PM on a Terminal Crimp Press during the scheduled window. |
| Changeover | Time from the last good part of the previous product to the first good part of the next product, per SOP-PRD-014. | Fixture and program change on a CNC Horizontal Machining Center. |
| Material Shortage | The work center is ready but raw material, castings, components or packaging are missing or unusable for lack of quantity. | MTY-L1 waits for pump housing castings (MAT-5002). |
| Quality Hold | Production is stopped or product is held pending a quality disposition, containment or first-article approval. | Crimp height reading out of specification, line stopped for containment. |
| No Operator | The machine is available and material is present but no qualified operator is assigned. | Absence on C shift with no relief. |

### 5.1 Coding rules

1. Code by root cause of the stop, not by who was first to notice. If a machine is down because of a failure, the entire duration is Equipment Failure even if a material delivery also arrives late during the repair.
2. If two causes overlap, code the cause that began first. Do not split minutes between two codes unless the first cause has demonstrably ended.
3. A quality hold caused by a failing machine is coded Quality Hold only while the product disposition is pending. Time spent repairing the machine is Equipment Failure.
4. Waiting for a supervisor or operator to be reassigned is No Operator, not Material Shortage.
5. Startup and warm-up after a break is not downtime unless it exceeds 10 minutes, in which case it is coded to the cause.
6. Supervisors review and correct codes within 24 hours. Corrections are logged with the supervisor's ID and are visible in the shift result history.

### 5.2 Speed and quality loss

Minor stops under one minute and reduced-speed running are not downtime. They surface as Performance loss when total units are compared to run time at the ideal cycle time. Scrap and rework surface as Quality loss. Do not record them as downtime.

## 6. Targets

| Level | OEE target |
|---|---|
| Corporate ("world-class") | 85% |
| Plant | Corporate target applies to all plants; plant improvement glide paths are set in the annual operating plan. |

A line is flagged **Amber** when monthly OEE is below 85% and **Red** when it is more than 10 points below target (below 75%). Red lines require a written recovery plan in the monthly operations review.

## 7. Worked example

On one A shift a line has 450 planned minutes and records 63 minutes of Equipment Failure, 20 of Changeover and 7 of Material Shortage. Run minutes are 450 - 90 = 360, so Availability = 360 ÷ 450 = 80.0%. The line produced 2,100 units against 2,400 possible at the ideal cycle time, so Performance = 87.5%. Of 2,100 units, 2,058 were good, so Quality = 98.0%. OEE = 0.80 x 0.875 x 0.98 = 68.6%.

## 8. Reporting cadence

- Daily: shift results are available in MES by 07:00 the following day.
- Weekly: plant managers review the top three loss codes per line.
- Monthly: plants publish an operations review; lines in Red are escalated to the VP Operations.
- Quarterly: corporate publishes the Operations Performance Review (for example RPT-OPS-2026-Q3).

## 9. Responsibilities

| Role | Responsibility |
|---|---|
| Operators | Code every stop accurately and on time. |
| Shift supervisors | Review codes at end of shift; challenge "No Operator" and "Material Shortage" entries. |
| Plant managers | Own plant OEE and the monthly review. |
| Director of Reliability & Maintenance (Marcus Okafor) | Owns Equipment Failure and Planned Maintenance trends. |
| VP Operations (Dana Whitfield) | Owns this standard and the corporate target. |

## 10. Related documents

SOP-PRD-014 (Changeover), SOP-PRD-020 (Escalation Matrix), PLN-PRD-003 (Scheduling), GLS-PRD-001 (Glossary).

## 11. Revision history

| Rev | Date | Change |
|---|---|---|
| A | 2023-03-01 | Initial issue. |
| B | 2024-09-16 | Added Quality Hold and No Operator as separate codes. |
| C | 2026-01-12 | Clarified overlap rule and 450-minute planned time; aligned to gold metric views. |
