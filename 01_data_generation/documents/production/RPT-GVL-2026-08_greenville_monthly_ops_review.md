# Greenville Monthly Operations Review - August 2026

| Field | Value |
|---|---|
| Document ID | RPT-GVL-2026-08 |
| Title | Greenville Monthly Operations Review, August 2026 |
| Revision | Rev 1 |
| Report Date | 2026-09-14 |
| Owner | Tom Brennan, Greenville Plant Manager |
| Approver | Dana Whitfield, VP Operations (recipient) |
| Classification | Internal |

**MEMO**
**To:** Dana Whitfield, VP Operations
**From:** Tom Brennan, Greenville Plant Manager
**Cc:** Marcus Okafor, Luis Hernandez, Ashley Taylor, Elena Ramirez, Priya Nair
**Subject:** August 2026 operations review - GVL-L3 OEE collapse and recovery plan

## 1. Summary

Greenville (GVL) continues to run well below the 85% corporate OEE target, and the Gearbox Assembly line (GVL-L3) is the reason. GVL-L3 closed August at **58% OEE**, 27 points below target and 26 points below the 84% it delivered in March, before spindle bearing wear began on GVL-L3-WC01 (CNC Horizontal Machining Center #1). Nearly all lost time on the line traces to that single machine. Plant OEE for FY26 stands at 78.3%, and PM compliance for FY26 is 80.6% against our 84% target (GVL-L3 76.7%).

The line is now producing roughly 99 units per shift against about 144 in a healthy month, and we are accumulating a backlog we cannot recover through overtime alone.

## 2. GVL-L3 OEE by month

| Month | GVL-L3 OEE | Gap to 85% target |
|---|---|---|
| Oct 2025 | 82% | -3 pts |
| Jan 2026 | 82% | -3 pts |
| Mar 2026 | 84% | -1 pt |
| Apr 2026 | 76% | -9 pts |
| May 2026 | 67% | -18 pts |
| Jun 2026 | 60% | -25 pts |
| Jul 2026 | 55% | -30 pts |
| **Aug 2026** | **58%** | -27 pts |
| Sep 2026 (month to date) | 50% | -35 pts |

August improved by three points from July only because we ran the Saturday A and B shifts on all five Saturdays and used temporary tooling on WC02 to take load off WC01. This is not a recovery. Month-to-date September is the lowest of the year at 50%.

## 3. WC01 breakdown pattern

GVL-L3-WC01 is a Hartwell Machine Tools HAR-119, installed 2013-08-27, criticality A: it is the line bottleneck, it machines the gearbox bearing bores, and there is no redundancy. Key observations:

- Spindle bearing wear started on 2026-03-15. Average running vibration climbed from a normal 2.8 mm/s to 3.44 mm/s in April, 4.39 in May, 5.23 in June, 6.46 in July and **7.57 mm/s in August**.
- The Hartwell OEM manual (HMC-Series, section 7.4) sets an alert at 3.5 mm/s and requires bearing replacement at 4.5 mm/s. The machine crossed that limit in June 2026.
- Our internal procedure PM-CNC-030 Rev C (2019) triggers replacement at 7.1 mm/s. That limit was reached in August, about two months after the OEM limit. Monthly PMs were completed in April, May, July and August with vibration recorded as "within limit" until August; two PMs were deferred (due 2026-06-27 and 2026-09-04).
- Since 2026-03-15 the machine has accumulated about 30 breakdowns, almost all coded to spindle bearing wear, and about 286 hours of repair time. Cost of Hartwell field service and contractors is about $146K, and about $243K including parts. Most stops were coded **Equipment Failure** in MES.
- Typical failure sequence: vibration alarm, operator slows feed, spindle seizes or bore position drifts, line waits for the on-call technician and for Hartwell's field service engineer, Gary Lindqvist.

The detailed root-cause analysis (lubrication degradation and bearing preload loss, accelerated by deferred PMs and a loose PM limit) is in the maintenance investigation led by Ashley Taylor and Luis Hernandez and is not repeated here.

## 4. Impact on gearbox output

Using the ideal cycle time of 156.5 s/unit and 450 planned minutes per shift (PLN-PRD-003), GVL-L3 has a theoretical 172 units per shift. In August the schedule contained 73 shifts (21 weekdays x 3, plus 5 Saturdays x 2).

| Case | OEE | Approx. units per shift | Approx. August output |
|---|---|---|---|
| Healthy (March, 74 shifts) | 84% | 144 | 10,672 |
| Actual August (73 shifts) | 58% | 99 | 7,245 |
| **Shortfall** | | | **about 3,430 units** |

Stops on WC01 starve WC02 to WC06. Because WC01 is the bottleneck, every lost minute is a lost minute of line output. Availability is the main loss; Performance also suffers as operators slow feed rates, and Quality loss is rising because bore-position drift is producing out-of-tolerance bores (CAPA-2026-103, opened 2026-05-24, due 2026-07-23, still Open and overdue).

## 5. Customer backlog

The shortfall has turned into a past-due gearbox backlog in WH-GVL that is growing weekly. Strategic OEM customers have been given priority allocation under PLN-PRD-003, which pushes the delays onto smaller accounts. Planning has moved the committed load to the actual OEE of 58% for the next four weeks, but at that rate we still cannot meet requested dates for all open gearbox orders. Customer service has been asked to contact affected customers with revised dates.

## 6. Actions

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Approve and place PO for replacement spindle cartridge (Hartwell, $68,400 installed; 10-week lead time; no spare on site). If approved by 2026-09-18, delivery is expected about 2026-11-27 | Tom Brennan / Dana Whitfield (approval) | 2026-09-18 |
| 2 | Interim measures: reduced feed rates, weekly spindle vibration trending, daily lubrication check on WC01 | Luis Hernandez | 2026-09-21 |
| 3 | Approve MOC-2026-031 to align PM-CNC-030 with the OEM 4.5 mm/s limit (submitted July 2026) | Engineering approver; escalated by Marcus Okafor | 2026-09-25 |
| 4 | Close CAPA-2026-103 containment: 100% bore inspection on GVL-L3 until spindle replaced | Plant quality manager | 2026-09-21 |
| 5 | Re-plan GVL-L3 load at actual OEE and publish revised customer dates | Planning lead / Tom Brennan | 2026-09-18 |
| 6 | Adopt Columbus practices (condition-based PM, weekly reliability stand-up, spare-spindle program) - see CS-CLB-2026-02 | Luis Hernandez / Ashley Taylor | 2026-10-30 |
| 7 | Review spare-spindle policy for all A-critical CNCs | Marcus Okafor | 2026-10-15 |

## 7. Request to the VP Operations

1. Approve the spindle cartridge purchase.
2. Confirm authority to run Saturday overtime on GVL-L3 through November.
3. Sponsor adoption of OEM-based condition limits across all CNC machines at KK's Parts.
