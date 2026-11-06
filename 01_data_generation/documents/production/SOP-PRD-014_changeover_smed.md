# Changeover (SMED) Standard Work

| Field | Value |
|---|---|
| Document ID | SOP-PRD-014 |
| Title | Changeover (SMED) Standard Work |
| Revision | Rev B |
| Effective Date | 2026-02-02 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Katarzyna Nowak, Wroclaw Plant Manager (Operations Council chair, FY26) |
| Classification | Internal |

## 1. Purpose

This procedure standardizes changeovers across KK's Parts plants using Single-Minute Exchange of Die (SMED) principles. Changeover time is a coded downtime reason (see SOP-PRD-001) and directly reduces Availability. Shorter, repeatable changeovers allow smaller batches and better schedule adherence (PLN-PRD-003).

## 2. Scope

All lines at CLB, GVL, MTY, WRO and PNQ where product, tooling, program or fixture changes occur. It applies to operators, setters, shift supervisors and process engineers.

## 3. Definition

A changeover is the time from the **last good part of the previous product** to the **first good part of the next product** that passes first-article approval. It includes cleaning, tool and fixture exchange, program load, adjustments, first-article inspection and any rework of the first parts. It excludes planned maintenance performed in the same window, which is coded Planned Maintenance.

## 4. Changeover targets by line family

Targets are the maximum standard minutes per changeover. Any changeover above 120% of target triggers a review at the next daily meeting.

| Line family | Example lines | Target (min) |
|---|---|---|
| Machining (CNC mills, lathes, machining centers) | CLB-L1, GVL-L1, MTY-L1, MTY-L2 | 35 |
| Gearbox / precision machining and assembly | GVL-L3, CLB-L3 | 45 |
| Assembly and test | CLB-L2, WRO-L2, WRO-L3 | 25 |
| Crimp and wire processing | WRO-L1 | 20 |
| Stamping and cold heading (die changes) | PNQ-L1, PNQ-L2 | 40 |
| Heat treat, paint, plating (batch process) | GVL-L2, MTY-L3, PNQ-L3 | 60 |

Targets will be reviewed annually; Rev B introduced the batch-process family target of 60 minutes.

## 5. SMED procedure

### 5.1 Preparation (external activities - machine still running)

1. Review the next order on the schedule board and confirm tooling, fixtures, gauges and program revision are staged at the line side.
2. Verify the correct work instruction revision is issued. Setters must use the current revision only; superseded instructions must be removed from the line (see CAPA-2026-102 for the consequence of using a superseded setup instruction on Wroclaw C shift).
3. Confirm material for the next order is at the line. If it is not, notify the supervisor before stopping the machine.
4. Pre-heat tooling, load programs offline and prepare first-article inspection forms.

### 5.2 Changeover (internal activities - machine stopped)

1. Complete the last good part. Press **Start Changeover** on the MES terminal. This opens a Changeover downtime record.
2. Remove the previous tooling and clean the work area.
3. Install new tooling using quick-release fixtures and pre-set tool offsets.
4. Load the program or recipe and verify revision.
5. Run first articles. Inspect against the control plan; stop if any reading is out of specification.
6. On first-article approval by the quality technician, press **End Changeover**. The record closes at the timestamp of the first good part.

### 5.3 Post-changeover

1. Run a short stability check of the first 10 parts or first 5 minutes.
2. Record any deviations or unplanned waits in the comment field.
3. Return tooling and clean staging areas.

## 6. How changeover minutes are logged

- Changeover minutes are recorded in MES as downtime with reason code **Changeover**.
- Each record has the start time, end time, work center, previous and next product, and the setter's operator ID.
- If a changeover is interrupted by a breakdown, split the record: Changeover up to the failure, **Equipment Failure** during the repair, and Changeover again when resumed.
- Waiting for material during a changeover is **Material Shortage**, and waiting for first-article approval is part of Changeover unless the quality hold exceeds 15 minutes, in which case the excess is **Quality Hold**.
- Changeovers must be logged before the end of shift; supervisors approve them within 24 hours.

## 7. Performance measurement

| Metric | Formula | Review |
|---|---|---|
| Average changeover time | Total changeover minutes / changeovers | Weekly |
| Changeover adherence | Changeovers at or below target / total | Weekly |
| Changeover share of loss | Changeover minutes / total downtime minutes | Monthly |

## 8. Continuous improvement

Process engineers run a SMED study on any line where Changeover is among the top three loss codes for two consecutive months. Studies video the changeover, classify each element as internal or external, convert internal to external where possible, and standardize fasteners and locating features. Findings are recorded on the line's standard work sheet and tracked in the monthly operations review.

## 9. Action items from the FY26 review

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Audit setup work instruction revisions at all line side stations | Plant managers | 2026-08-31 |
| 2 | Add quick-release clamps on WRO-L1 crimp presses | Tomasz Wisniewski | 2026-09-30 |
| 3 | Publish changeover adherence in the weekly plant dashboard | Dana Whitfield | 2026-09-15 |

## 10. Related documents

SOP-PRD-001 (OEE Standard), SOP-PRD-020 (Escalation Matrix), PLN-PRD-003 (Scheduling), GLS-PRD-001 (Glossary).
