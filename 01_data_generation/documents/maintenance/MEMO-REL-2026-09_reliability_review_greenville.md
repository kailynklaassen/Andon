# Memorandum — September 2026 Reliability Review: Greenville

| Field | Value |
|---|---|
| Document ID | MEMO-REL-2026-09 |
| Title | Reliability Review Memo, September 2026: Greenville PM Compliance and GVL-L3-WC01 |
| Revision | Rev 1 |
| Report date | 2026-09-29 |
| From (Owner) | Marcus Okafor, Director of Reliability & Maintenance |
| To (Approver) | Dana Whitfield, VP Operations |
| Copy | Tom Brennan, Luis Hernandez, Ashley Taylor, Elena Ramirez |
| Classification | Internal |

## 1. Purpose

This memo summarizes FY2026 maintenance performance at Greenville, explains the continuing losses on GVL-L3-WC01 and requests three decisions.

## 2. PM Compliance

Corporate policy (POL-MNT-001) sets a 95% PM compliance target. Plants also carry a FY2026 glide-path target.

| Plant | FY2026 PM compliance | Plant target | Corporate target |
|---|---|---|---|
| Columbus (CLB) | 96.6% | 97% | 95% |
| Greenville (GVL) | **80.6%** | 84% | 95% |
| Greenville Line GVL-L3 | **76.7%** | n/a | 95% |
| Monterrey (MTY) | 92.0% | 90% | 95% |
| Wroclaw (WRO) | 97.9% | 92% | 95% |
| Pune (PNQ) | 96.0% | 91% | 95% |

Greenville is 14.4 points below the corporate target and 3.4 points below its own 84% plant target. GVL-L3 is 18.3 points below the corporate target. Columbus, at 96.6%, is the internal benchmark; it runs condition-based PM triggers at OEM limits, a weekly reliability stand-up and a spare-spindle program for A-critical CNCs. Columbus has fewer breakdowns (48 versus 83 in FY2026) and the highest OEE among the US plants (81.3%, versus 78.3% at Greenville).

## 3. GVL-L3-WC01

GVL-L3-WC01 is the Hartwell HAR-119 CNC Horizontal Machining Center #1 on line GVL-L3 (criticality A, installed 2013-08-27). Spindle bearing wear began 2026-03-15.

| Metric | Value |
|---|---|
| Breakdowns since 2026-03-15 | 30 |
| Repair time | approx. 286 hours |
| Hartwell field-service / contractor cost | approx. $146K |
| Total parts plus contractor cost | approx. $243K |
| GVL-L3 OEE | 84% in March falling to 50% in September |
| Average vibration | 2.85 mm/s (Mar) rising to 8.75 mm/s (Sep) |
| Quality | Bore-out-of-tolerance NCRs rising; CAPA-2026-103 open and overdue (due 2026-07-23) |
| Downstream effect | Output shortfalls on gearbox lines; see RPT-GVL-2026-08 |

Details are in RCA-2026-GVL-007 and the Hartwell report FSR-HMT-2026-0412.

## 4. Findings

1. Vibration exceeded the Hartwell replacement limit of 4.5 mm/s in June 2026. PM-CNC-030 Rev C (2019) did not require action until 7.1 mm/s, which was reached in August, two months later.
2. Two PMs on the machine were deferred (due 2026-06-27 and 2026-09-04), against the intent of the one-consecutive-deferral limit for A-critical assets.
3. Hartwell has stated that operation above 4.5 mm/s voids the spindle warranty.
4. No spare cartridge is held at Greenville. A replacement takes 10 weeks from order.
5. MOC-2026-031 to align the PM limit with the OEM was submitted in July 2026 and is still pending engineering approval.

## 5. Recommendation

1. Replace the spindle cartridge now. Hartwell quote is $68,400 installed, with 10 weeks lead time. On approval by early October the machine would be down for the exchange in mid-December.
2. Approve MOC-2026-031 so that all Hartwell machines (GVL-L3-WC01, MTY-L2-WC01, MTY-L2-WC02 and CLB-L1-WC01) use the OEM 4.5 mm/s limit with a 3.5 mm/s alert.
3. Fund online vibration sensors and a spare spindle cartridge for each A-critical Hartwell machine, following the Columbus model.
4. Enforce the deferral rule in POL-MNT-001 and require Director approval for any second consecutive deferral on an A-critical asset.
5. Place Greenville on a recovery plan to reach its 84% plant target by end of Q1 FY2027 and 95% by FY2028.

## 6. Decisions Requested from the VP Operations

| # | Decision | Needed by |
|---|---|---|
| 1 | Approve capital of $68,400 for the GVL-L3-WC01 spindle cartridge | 2026-10-05 |
| 2 | Direct the Corporate Engineering Review Board to approve MOC-2026-031 | 2026-10-15 |
| 3 | Approve FY2027 funding for online sensors and spare cartridges (amount to follow) | FY2027 planning |

## 7. Cost of Inaction

At the September run rate GVL-L3 continues to run well below the 85% corporate OEE target, and another 10 weeks of operation above the OEM limit risks a catastrophic spindle failure and a longer outage than the planned exchange. The cumulative parts and contractor spend on this single machine already exceeds three times the cost of the replacement cartridge.
