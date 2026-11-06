# Asset Criticality Ranking Standard

| Field | Value |
|---|---|
| Document ID | STD-MNT-004 |
| Title | Asset Criticality Ranking Standard |
| Revision | Rev 2 |
| Effective date | 2025-10-01 |
| Owner | Marcus Okafor, Director of Reliability & Maintenance |
| Approver | Dana Whitfield, VP Operations |
| Classification | Internal |

## 1. Purpose

This standard defines how KK's Parts ranks machines (work centers) as criticality A, B or C so that PM frequency, response times, deferral limits and spare parts are applied consistently across all plants.

## 2. Criticality Definitions

| Class | Definition | Typical example |
|---|---|---|
| **A** | Line bottleneck or single point of failure with no redundancy; failure stops line output or creates a safety or major quality risk | GVL-L3-WC01 CNC Horizontal Machining Center #1, which machines the gearbox bearing bores |
| **B** | Important to flow but with partial redundancy, buffer stock or an alternate route; failure reduces output | A CNC machining center in a multi-machine line with load-sharing capacity |
| **C** | Non-critical or easily substituted; failure has limited effect on output | Wash station, packaging stations |

## 3. Ranking Criteria

Each asset is scored 1 to 5 on the following criteria by the plant reliability engineer and reviewed by the Plant Maintenance Manager.

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| Production impact | Negligible | Reduced output | Line stops |
| Redundancy | Multiple alternates | Partial alternate | None (bottleneck) |
| Quality impact | None | Rework | Scrap or customer escape |
| Safety/environment | None | Minor | Reportable |
| Replacement lead time | Under 2 weeks | 2 to 8 weeks | Over 8 weeks |
| Repair cost | Under $5K | $5K to $50K | Over $50K |

Total score 22 to 30 = A; 14 to 21 = B; 6 to 13 = C. Any asset that is the sole bottleneck of a line is A regardless of score.

## 4. Consequences by Class

| Aspect | A | B | C |
|---|---|---|---|
| PM approach | Calendar PM plus condition-based triggers; online vibration where feasible | Calendar PM plus route-based condition checks | Calendar or run-to-fail by exception |
| Work order response (Critical/High) | Start within 1 hour | Start within 4 hours | Next working day |
| PM deferral | Maximum 1 consecutive; Plant Manager approval (POL-MNT-001) | 2 consecutive | 3 consecutive |
| Vibration review | Weekly at alert level, monthly otherwise | Monthly | Annual |
| Reliability review | Weekly stand-up | Monthly | Quarterly |

## 5. Spare Parts Strategy by Class

| Class | Strategy |
|---|---|
| A | Hold critical spares on site for components with lead time over 4 weeks, for example a spare spindle cartridge for each A-critical CNC. Stock is reviewed quarterly. |
| B | Hold common wear parts on site; critical components held at plant or regional pool; lead time must be known and documented |
| C | Order on demand; no critical spares unless failure cost exceeds $10K |

### 5.1 Spindle cartridges

Hartwell HMC spindle cartridges carry a 10-week lead time from purchase order. Columbus operates a spare-spindle program for A-critical CNCs. Greenville has no spare cartridge on site for GVL-L3-WC01, a gap highlighted in RCA-2026-GVL-007. Under this standard, an A-critical asset with a component lead time over 8 weeks and no on-site spare is a standing audit finding.

## 6. Review and Governance

1. Criticality is reviewed annually, and whenever a line is re-laid out or a bottleneck shifts.
2. Changes to a class require Maintenance Manager and Plant Manager approval.
3. The CMMS asset record holds the class; reports use the CMMS value.
4. The Director of Reliability & Maintenance audits class assignments each fiscal year.

## 7. Related Documents

POL-MNT-001, STD-MNT-010, GLS-MNT-001, RCA-2026-GVL-007.
