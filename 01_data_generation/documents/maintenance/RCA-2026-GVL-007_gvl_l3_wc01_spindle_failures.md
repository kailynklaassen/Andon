# Root Cause Analysis — Repeated Spindle Bearing Failures on GVL-L3-WC01

| Field | Value |
|---|---|
| Document ID | RCA-2026-GVL-007 |
| Title | Root Cause Analysis: Repeated Spindle Bearing Failures on GVL-L3-WC01 (March to September 2026) |
| Revision | Rev 1 |
| Report date | 2026-09-22 |
| Owner / Author | Ashley Taylor, Reliability Engineer, Greenville |
| Reviewer | Luis Hernandez, Greenville Maintenance Manager |
| Approver | Marcus Okafor, Director of Reliability & Maintenance |
| Classification | Internal |
| Related records | MOC-2026-031, FSR-HMT-2026-0412, CAPA-2026-103, PM-CNC-030, OEM-HMT-HMC-SM7 |

## 1. Executive Summary

GVL-L3-WC01 (CNC Horizontal Machining Center #1, Hartwell Machine Tools model HAR-119, installed 2013-08-27, criticality A) has suffered 30 breakdowns since spindle bearing wear began on 2026-03-15. The machine is the bottleneck of Gearbox Assembly line GVL-L3 and machines the gearbox bearing bores. Cumulative repair time is approximately 286 hours; Hartwell field-service and contractor cost is approximately $146K and total parts plus contractor cost is approximately $243K. Line OEE fell from 84% in March to 50% in September.

The root cause is spindle bearing degradation driven by lubrication breakdown and preload loss, which went unaddressed because (a) two preventive maintenance work orders were deferred and (b) the internal PM limit (7.1 mm/s in PM-CNC-030 Rev C) is far looser than the OEM replacement limit (4.5 mm/s in OEM-HMT-HMC-SM7, section 7.4). Vibration crossed the OEM limit in June 2026, about two months before the internal limit was reached in August.

## 2. Problem Statement

Repeated Emergency and Corrective work orders on the main spindle, with almost all failures coded "spindle bearing wear", beginning in the second half of March 2026 and increasing in frequency through September.

## 3. Timeline and Vibration Data

Normal running vibration for this machine is approximately 2.8 mm/s. Values are the monthly average running vibration at the spindle nose from the IoT historian.

| Month (2026) | Avg vibration (mm/s) | Versus OEM (alert 3.5 / replace 4.5) | Versus PM-CNC-030 (7.1) | PM event |
|---|---|---|---|---|
| March | 2.85 | Normal | Below | Wear begins 2026-03-15 |
| April | 3.44 | Just below alert | Below | PM completed, "within limit" |
| May | 4.39 | Above alert, just below replace | Below | PM completed, "within limit" |
| June | 5.23 | **Above OEM replace limit** | Below | PM due 2026-06-27 **deferred** |
| July | 6.46 | Above | Below | PM completed, "within limit" |
| August | 7.57 | Above | **Above** | PM completed; limit finally exceeded; Hartwell called (FSR-HMT-2026-0412) |
| September | 8.75 | Above | Above | PM due 2026-09-04 **deferred** |

Key observation: the monthly PMs in April, May and July were completed and the vibration was recorded, but each reading was judged acceptable because it was below 7.1 mm/s. A reading of 4.39 in May was within 0.11 mm/s of the OEM replacement limit, and June crossed it.

## 4. Impact

| Metric | Value |
|---|---|
| Breakdowns since 2026-03-15 | 30 (Emergency/Corrective) |
| Repair time | approx. 286 hours |
| Hartwell field-service / contractor cost | approx. $146K |
| Total parts plus contractor cost | approx. $243K |
| GVL-L3 OEE | Mar 84%, Apr 76%, May 67%, Jun 60%, Jul 55%, Aug 58%, Sep 50% |
| Quality | Rising "Bore out of tolerance" NCRs from bore position drift; CAPA-2026-103 opened 2026-05-24, due 2026-07-23, Open (overdue) |

## 5. Five Whys

1. **Why did the machine fail repeatedly?** The spindle bearings were worn and the spindle seized or tripped on overload.
2. **Why were the bearings worn?** Lubrication had degraded and bearing preload was lost, raising friction and vibration.
3. **Why was this not corrected early?** Vibration passed the OEM replacement limit (4.5 mm/s) in June, but no action was triggered.
4. **Why was no action triggered?** The PM procedure PM-CNC-030 Rev C only requires action at 7.1 mm/s, and two PMs (due 2026-06-27 and 2026-09-04) were deferred.
5. **Why is the procedure out of line with the OEM?** It has not been revised since 2019 and there is no process linking OEM manual revisions to internal procedures.

## 6. Fishbone Summary

| Category | Contributing causes |
|---|---|
| Method | PM limit 7.1 mm/s versus OEM 4.5 mm/s; no trend-based trigger; no OEM-to-procedure review |
| Machine | 13-year-old spindle; grease degradation; preload loss |
| Material | No spare spindle cartridge on site; 10-week lead time |
| Manpower | Staffing pressure on Greenville maintenance; PM backlog |
| Measurement | Handheld, once-monthly readings; no alarm on online data |
| Management | Deferral of an A-critical PM; compliance GVL-L3 76.7%; Hartwell warranty conditions not communicated to the floor |

## 7. Root Causes

1. **Lubrication degradation and preload loss** in the spindle cartridge, accelerated by operation beyond the OEM limit.
2. **Deferred preventive maintenance** on 2026-06-27 and 2026-09-04, removing the monthly opportunity to catch and escalate the trend.
3. **Outdated PM limit**: PM-CNC-030 Rev C at 7.1 mm/s versus OEM 4.5 mm/s.

## 8. Recommendations

| # | Action | Owner | Target |
|---|---|---|---|
| 1 | Replace the spindle cartridge (Hartwell quote $68,400 installed; 10-week lead time) | Luis Hernandez | Order immediately on approval |
| 2 | Adopt the OEM 4.5 mm/s limit in PM-CNC-030 through MOC-2026-031 and extend alert at 3.5 mm/s | Marcus Okafor | Approve by 2026-10-15 |
| 3 | Implement condition-based monitoring: online vibration alarms at 3.5 and 4.5 mm/s on all A-critical CNCs (per STD-MNT-010) | Ashley Taylor | Q1 FY2027 |
| 4 | Hold a spare spindle cartridge for each A-critical Hartwell HMC (as practised at Columbus) | Luis Hernandez | FY2027 budget |
| 5 | Restrict deferrals for A-critical assets to one consecutive deferral (POL-MNT-001) | Luis Hernandez | Immediate |
| 6 | Interim: reduce duty and monitor weekly until the cartridge arrives | Ashley Taylor | Immediate |

## 9. Interim Risk

With the 10-week lead time, the machine will continue to run well above the OEM replacement limit until replacement. Hartwell has warned that operation above 4.5 mm/s voids the spindle warranty.
