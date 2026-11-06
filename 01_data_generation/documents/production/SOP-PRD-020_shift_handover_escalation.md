# Shift Handover & Downtime Escalation Matrix

| Field | Value |
|---|---|
| Document ID | SOP-PRD-020 |
| Title | Shift Handover & Downtime Escalation Matrix |
| Revision | Rev B |
| Effective Date | 2026-03-02 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Marcus Okafor, Director of Reliability & Maintenance |
| Classification | Internal |

## 1. Purpose

This procedure ensures that production information passes cleanly between shifts and that unplanned downtime is escalated to the right people at defined time thresholds. It reduces the time a line stays down because the right person was not told.

## 2. Scope

All production lines at CLB, GVL, MTY, WRO and PNQ. Applies to shift supervisors, line leads, maintenance technicians, plant managers and corporate functions.

## 3. Shift pattern

| Shift | Hours | Days |
|---|---|---|
| A | 06:00-14:00 | Mon-Sat |
| B | 14:00-22:00 | Mon-Sat |
| C | 22:00-06:00 | Mon-Fri |

Sunday is dark. Each shift has 450 planned production minutes. Handover takes place at the line in the final 15 minutes of the outgoing shift and is not coded as downtime.

## 4. Shift handover

### 4.1 Required content

The outgoing supervisor completes the electronic handover log in MES and reviews it verbally with the incoming supervisor. The log must include:

1. Safety incidents, near-misses and open hazards.
2. Production result versus plan, including units, scrap and rework.
3. All downtime events longer than 15 minutes, with reason code and status.
4. Open maintenance work orders and machines running in a degraded state, for example elevated vibration or noise.
5. Open quality holds and containment actions.
6. Material status: shortages expected in the next 8 hours.
7. Operator staffing and certification gaps (for example no Level 3 certified setter available).
8. Active work instructions and revisions in use for setups.

### 4.2 Rules

- The incoming supervisor signs the log. An unsigned log is escalated to the plant manager at 09:00 the next working day.
- Degraded-machine observations must be copied to the maintenance team's daily list; observation without a work order is not acceptable.
- A-shift supervisors attend the 07:30 daily operations meeting; B and C supervisors send the written handover to the plant manager by 06:15 and 14:15.

## 5. Downtime escalation matrix

Time is measured from the start of the stop on a work center, regardless of reason-code corrections. The notifying person is the shift supervisor unless stated.

| Reason code | At 30 minutes | At 60 minutes | At 120 minutes |
|---|---|---|---|
| Equipment Failure | Maintenance Supervisor on shift; line lead | Plant Maintenance Manager (GVL: Luis Hernandez); plant manager informed | Plant Manager (GVL: Tom Brennan); Director of Reliability & Maintenance (Marcus Okafor); OEM field service engaged if applicable (for GVL-L3-WC01, Gary Lindqvist at Hartwell Machine Tools) |
| Planned Maintenance | Maintenance Supervisor confirms completion estimate | Plant Maintenance Manager; production planner re-sequences orders | Plant Manager; VP Operations informed if the overrun delays customer orders |
| Changeover | Process engineer (SMED owner) | Production Manager; quality technician checks first-article status | Plant Manager; review of work instruction and setter certification |
| Material Shortage | Material handler / line planner checks stock and open receipts | Plant Supply Chain Lead; planner re-sequences orders | Plant Manager and Director of Supply Chain & Logistics (Priya Nair); supplier expedite request; Supplier Quality Engineer informed if the shortage is quality-driven |
| Quality Hold | Quality technician | Plant Quality Manager (MTY: Guadalupe Flores); production supervisor | Plant Manager; Director of Quality (Elena Ramirez); customer notification assessed |
| No Operator | Production Manager arranges relief | HR/Staffing lead; cross-shift volunteer call | Plant Manager; overtime authorization; line scheduled to run reduced rate |

### 5.1 Escalation conventions

- Escalation is by phone and Teams message. Email alone does not meet this procedure.
- Escalations are logged in MES with the time, recipient and outcome.
- When a stop on an A-criticality machine (bottleneck, no redundancy) reaches 30 minutes, the plant manager is informed regardless of reason code.
- A repeat stop (same machine, same cause, three times in seven days) triggers a work order review by reliability engineering and an entry on the agenda of the weekly reliability stand-up.

## 6. Recovery and close-out

1. Supervisor confirms the first good part and ends the downtime record with the correct reason code.
2. For stops longer than 120 minutes, the plant produces a one-page incident summary within 48 hours: timeline, root cause, containment, owner and due date.
3. Stops linked to supplier, quality or reliability issues reference the relevant record, for example SCAR-2026-014, CAPA-2026-103.

## 7. Roles by plant (primary contacts)

| Plant | Plant Manager | Quality | Maintenance / Reliability |
|---|---|---|---|
| CLB | Kevin Thompson | Plant quality manager | Plant maintenance manager |
| GVL | Tom Brennan | Plant quality manager | Luis Hernandez; Ashley Taylor (reliability) |
| MTY | Alejandro Reyes | Guadalupe Flores | Plant maintenance manager |
| WRO | Katarzyna Nowak | Tomasz Wisniewski (Quality Engineer) | Plant maintenance manager |
| PNQ | Plant manager | Plant quality manager | Plant maintenance manager |

Wroclaw C-shift supervisor: Marek Kaminski.

## 8. Audit

Plant managers sample ten handover logs per month. Target is 100% completeness for items 3 to 5 of section 4.1. Results are reviewed in the monthly operations review.

## 9. Related documents

SOP-PRD-001, SOP-PRD-014, PLN-PRD-003, GLS-PRD-001.
