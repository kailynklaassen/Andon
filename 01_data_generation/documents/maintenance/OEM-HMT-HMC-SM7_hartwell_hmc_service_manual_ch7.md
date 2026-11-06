# Hartwell Machine Tools — HMC-Series Horizontal Machining Center Service Manual

**Hartwell Machine Tools, Technical Publications**

| Field | Value |
|---|---|
| Document ID | OEM-HMT-HMC-SM7 |
| Title | HMC-Series Horizontal Machining Center Service Manual, Excerpt: Chapter 7 Spindle |
| Revision | Rev 9 (Service Bulletin SB-HMC-07 incorporated) |
| Effective date | 2024-02-01 (held on file at KK's Parts since 2024-03-12) |
| Owner | Hartwell Machine Tools, Technical Publications |
| Approver | Hartwell Machine Tools, Product Engineering |
| Classification | Hartwell Proprietary – Customer Use |
| Applies to | All HMC-Series machines, including model HAR-119 |

> This excerpt is supplied to the machine owner for maintenance planning. Redistribution outside the owner's organization is not permitted.

## 7.1 Scope

This chapter covers the main spindle cartridge of HMC-Series horizontal machining centers: condition limits, lubrication, bearing preload, symptoms of wear, and warranty conditions. Follow this chapter in preference to any generic or legacy maintenance procedure. Where an owner's procedure conflicts with Table 7-2, Table 7-2 governs.

## 7.2 Spindle Lubrication

The spindle bearings are grease-packed for life of the interval below and supplemented by an oil-air system on high-duty configurations.

| Item | Specification | Interval |
|---|---|---|
| Bearing grease (cartridge relubrication) | Hartwell-approved lithium-complex spindle grease, NLGI 2 | Every 2,000 operating hours or 6 months, whichever comes first |
| Oil-air line (if fitted) | ISO VG 32 spindle oil, 0.03 ml per cycle | Check reservoir weekly; replace oil every 4,000 hours |
| Drawbar clamping grease | Hartwell-approved grease | Every 1,000 operating hours |
| Spindle chiller coolant | 30% glycol mix, 18-22 C setpoint | Check monthly; replace every 12 months |

Do not mix greases. Over-greasing raises bearing temperature and accelerates preload loss. Degraded or contaminated grease is the most common precursor to spindle bearing wear on machines past 10 years in service.

## 7.3 Bearing Preload

Spindle bearings are supplied with a factory-set preload. Preload is verified by measuring axial displacement under a 1,200 N test load.

| Condition | Axial displacement | Action |
|---|---|---|
| Within specification | 3 to 5 micrometres | None |
| Marginal | 5 to 8 micrometres | Re-verify within 30 days; review lubrication |
| Out of specification | Greater than 8 micrometres | Replace spindle cartridge |

Preload loss raises vibration, causes the spindle nose to run warm, and degrades bore position accuracy. Preload cannot be restored in the field; a cartridge replacement is required.

## 7.4 Vibration Limits

Vibration shall be measured as overall velocity in mm/s RMS, at the **spindle nose housing**, with the spindle running unloaded at 6,000 rpm after a 20-minute warm-up. Measurement bands follow ISO 10816 (machine class: Class II, medium machines, rigidly mounted).

**Table 7-2: Spindle vibration limits (RMS velocity, mm/s)**

| Level | Velocity (mm/s RMS) | ISO 10816 reference | Required action |
|---|---|---|---|
| Normal | 2.8 or below | Zone A/B | Continue routine monitoring |
| Alert | 3.5 | Zone B/C | Increase measurement frequency to weekly; inspect lubrication; schedule bearing assessment |
| **Replace spindle bearings** | **4.5** | Zone C/D boundary for this class | Plan cartridge replacement immediately; limit duty; do not exceed 4.5 mm/s in service |

Note: values between levels are interpolated; any reading at or above a level triggers that level's action. Hartwell recommends that owners embed Table 7-2 directly in their preventive maintenance procedures and review them whenever this manual is revised.

## 7.5 Symptoms of Bearing Wear

| Symptom | Typical onset |
|---|---|
| Rising overall velocity trend at the spindle nose | Earliest sign; weeks to months before failure |
| Spindle housing temperature rise of 8 C or more above baseline | Alert level and above |
| Audible growl or whine above 4,000 rpm | At or beyond the alert level |
| Bore diameter or position drift in finished parts | Typically above 4.5 mm/s |
| Spindle load (current) increase at constant cut | Late stage |
| Metallic particles in drained grease | Late stage |

## 7.6 Recommended Inspection Schedule

1. Monthly: record vibration at the spindle nose against Table 7-2.
2. Every 6 months: relubricate the cartridge and verify preload.
3. After any spindle crash or overload: measure vibration and verify preload within 24 hours.
4. At Alert level or above: weekly vibration readings and a spectrum capture for the bearing defect frequencies.

## 7.7 Warranty Note

Hartwell's spindle warranty and any extended spindle service agreement are conditional on the owner acting on Table 7-2. **Operating a spindle above 4.5 mm/s RMS voids the spindle warranty** for the affected cartridge and for consequential damage to the headstock. Hartwell may request vibration records, lubrication logs and PM records as evidence of compliance. Owners are responsible for ensuring that internal procedures use limits no looser than those in Table 7-2.

## 7.8 Spare Parts and Lead Time

| Part | Hartwell part group | Standard lead time |
|---|---|---|
| Spindle cartridge, complete, exchange | SPN-CART | 10 weeks from purchase order |
| Spindle bearing set (field replacement, not recommended) | SPN-BRG | 6 weeks |
| Drawbar assembly | SPN-DRW | 4 weeks |

Hartwell strongly advises owners of A-critical machines to hold a spare cartridge. Field service can be requested through the Hartwell Customer Service Center; emergency response is typically within 3 business days.

## 7.9 Revision History

| Rev | Date | Change |
|---|---|---|
| 7 | 2018-05-14 | Replacement limit confirmed at 4.5 mm/s |
| 8 | 2021-09-20 | Added preload test procedure (7.3) |
| 9 | 2024-02-01 | Added warranty conditions (7.7); aligned grease interval to 2,000 hours or 6 months |
