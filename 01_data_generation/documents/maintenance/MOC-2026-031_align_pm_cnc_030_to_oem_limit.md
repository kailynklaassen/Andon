# Management of Change Request — Align PM-CNC-030 Vibration Limit to OEM

| Field | Value |
|---|---|
| Document ID | MOC-2026-031 |
| Title | Management of Change: Align PM-CNC-030 Spindle Vibration Limit to Hartwell OEM Limit (4.5 mm/s) |
| Revision | Rev 1 |
| Submission date | 2026-07-14 |
| Report / status date | 2026-09-28 |
| Requester / Owner | Ashley Taylor, Reliability Engineer, Greenville |
| Sponsor | Marcus Okafor, Director of Reliability & Maintenance |
| Approver | Corporate Engineering Review Board (chair: Dana Whitfield, VP Operations) |
| Status | **Pending engineering approval** |
| Classification | Internal |

## 1. Change Description

| Item | Current state | Proposed state |
|---|---|---|
| Document changed | PM-CNC-030 Rev C (2019) | PM-CNC-030 Rev D |
| Vibration action limit (replace bearings) | 7.1 mm/s | **4.5 mm/s** for Hartwell HMC-Series machines |
| Alert level | None | **3.5 mm/s** (weekly vibration readings, lubrication inspection) |
| Measurement point | Spindle housing, radial | Spindle nose housing, per OEM-HMT-HMC-SM7 section 7.4 |
| Lubrication interval | Not specified | Relubricate every 2,000 hours or 6 months (OEM section 7.2) |
| Other OEMs | Same 7.1 limit | Limit per OEM manual; to be reviewed before Rev E |

## 2. Reason for Change

The 7.1 mm/s limit in PM-CNC-030 was set in 2019 and has not been revised. Hartwell's service manual (OEM-HMT-HMC-SM7, Rev 9) states that spindle bearings must be replaced at 4.5 mm/s and that operation above this level voids the spindle warranty. The gap of 2.6 mm/s meant that on GVL-L3-WC01 monthly PMs recorded "within limit" readings (4.39 mm/s in May, 6.46 mm/s in July) while the bearings were already beyond the OEM replacement threshold. See RCA-2026-GVL-007.

## 3. Affected Assets

All machines with Hartwell Machine Tools as OEM that use PM-CNC-030 (four assets). GVL-L3-WC02 is not affected: it is a Sato Precision machine (criticality C).

| Asset | Plant / Line | Description | Criticality | Notes |
|---|---|---|---|---|
| GVL-L3-WC01 | Greenville, Gearbox Assembly | CNC HMC #1, model HAR-119 | A | Currently at 8.75 mm/s (Sep average); cartridge replacement required |
| MTY-L2-WC01 | Monterrey, Housing Machining | CNC Horizontal Machining Center #1, model HAR-956 | A | Baseline readings to be re-taken |
| MTY-L2-WC02 | Monterrey, Housing Machining | CNC Horizontal Machining Center #2, model HAR-310 | B | Baseline readings to be re-taken |
| CLB-L1-WC01 | Columbus, Valve Body Machining | CNC Vertical Mill #1, model HAR-279 | A | Columbus already triggers condition-based PMs at OEM limits |

## 4. Risk Assessment

| Risk | If change is not made | If change is made | Rating |
|---|---|---|---|
| Spindle failure and unplanned downtime | Continues; further GVL-L3 loss (OEE 50% in September) | Earlier intervention reduces emergency repairs | High reduced to Low |
| Hartwell warranty voided | Occurs when operating above 4.5 mm/s | Warranty conditions met | High reduced to Low |
| Quality (bore position drift, CAPA-2026-103) | Continues | Drift detected earlier | Medium reduced to Low |
| Increase in planned work / spend | None | More spindle cartridge replacements brought forward; estimated 1 to 2 additional cartridge replacements per year fleetwide at $68,400 each | Medium |
| Machines already above 4.5 mm/s found at first re-baseline | Not discovered | Possible immediate Corrective WOs | Medium |
| Procedural drift between plants | Persists | Single standard | Low |

Overall risk of making the change: Low. Overall risk of not making the change: High.

## 5. Implementation Plan

1. Engineering approval of this MOC by the Corporate Engineering Review Board.
2. Issue PM-CNC-030 Rev D with Table 7-2 values embedded and the 3.5 mm/s alert step.
3. Re-baseline vibration on all four assets in the table within 10 working days of approval.
4. Train technicians at GVL, MTY and CLB on the new limits (30-minute toolbox session).
5. Update CMMS PM checklist fields so that readings at or above 4.5 mm/s automatically raise a Corrective work order.
6. Close the loop by monthly reporting of the four assets in the reliability review (MEMO-REL-2026-09).

## 6. Approvals and Status

| Role | Name | Decision | Date |
|---|---|---|---|
| Requester | Ashley Taylor | Submitted | 2026-07-14 |
| Plant maintenance | Luis Hernandez | Recommended | 2026-07-17 |
| Plant manager (Greenville) | Tom Brennan | Recommended | 2026-07-21 |
| Director, Reliability & Maintenance | Marcus Okafor | Endorsed | 2026-07-24 |
| Quality | Elena Ramirez | Informed (CAPA-2026-103 linked) | 2026-07-28 |
| Corporate Engineering Review Board | Dana Whitfield, chair | **Pending** | |

The MOC has been awaiting engineering approval since submission in July 2026. Delay of approval leaves PM-CNC-030 Rev C in force with its 7.1 mm/s limit.

## 7. Related Documents

PM-CNC-030, OEM-HMT-HMC-SM7, RCA-2026-GVL-007, FSR-HMT-2026-0412, POL-MNT-001, STD-MNT-010, CAPA-2026-103.
