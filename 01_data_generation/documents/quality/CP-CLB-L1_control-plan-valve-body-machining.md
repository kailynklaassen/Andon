# Control Plan: Valve Body Machining (CLB-L1)

| Field | Value |
|---|---|
| Document ID | CP-CLB-L1 |
| Title | Control Plan, Valve Body Machining, Columbus Hydraulics Plant |
| Revision | Rev C |
| Effective Date | 2026-01-12 |
| Owner | Elena Ramirez, Director of Quality |
| Approver | Kevin Thompson, Columbus Plant Manager |
| Classification | Internal |

## 1. Scope

This control plan covers CLB-L1 Valve Body Machining, which machines MAT-5001 Valve Body Castings (primary source SUP-1007 Brightline Castings) through two CNC mill operations, a deburr cell, a wash station and CMM inspection. It governs incoming casting checks, machined characteristics, leak testing and the reaction to nonconformance.

## 2. General Requirements

- Critical characteristics (CC) require a Cpk of at least 1.33 and 100% reaction on any out-of-specification reading.
- Measurement equipment is calibrated on the plant calibration schedule; CMM programs are validated at each revision.
- Castings are accepted only after QP-7.4 incoming inspection. Castings from suppliers under escalation (currently SUP-1007 under SCAR-2026-014 / CAPA-2026-101) receive the enhanced checks in Section 4.

## 3. Control Plan Table

| # | Operation | Characteristic | Spec | Class | Measurement method | Sample size and frequency | Reaction |
|---|---|---|---|---|---|---|---|
| 1 | Incoming | Casting dimensions at datum features | Per drawing | Standard | CMM / go-no-go gauges | AQL sampling per QP-7.4 | R1 |
| 2 | Incoming | Porosity (radiographic or sectioning) | ASTM E155 Level 1 critical zones, Level 2 elsewhere (SQA-BLC-2023 Section 4) | CC | Radiographic review of supplier film; Columbus sectioning of 1 casting per lot | 1 per lot; every lot while supplier is under SCAR | R3 |
| 3 | CNC Mill #1 | Datum face flatness | 0.020 mm | Standard | CMM | 1 piece per 25 | R1 |
| 4 | CNC Mill #2 | **Main spool bore diameter** | **25.000 mm +/- 0.015 mm** (24.985 to 25.015) | **CC** | Air gauge, verified by bore gauge setting master; CMM audit | 100% air gauge; CMM 1 piece per 25 and at start of shift | R2 |
| 5 | CNC Mill #2 | Bore cylindricity | 0.005 mm | CC | CMM | 1 piece per 25 | R2 |
| 6 | CNC Mill #2 | Bore surface finish | Ra 0.4 um maximum | Standard | Profilometer | 1 piece per shift | R1 |
| 7 | Deburr / wash | Cross-drilling burr and cleanliness | No burr; particle count within spec | Standard | Visual at 10x; gravimetric | 1 per hour; 1 per shift | R1 |
| 8 | Post-wash | Porosity breaking into sealing surface | No pore larger than 0.5 mm on machined sealing surfaces | CC | 10x visual / borescope on bore and ports | 100% visual by operator | R3 |
| 9 | Leak test | **Pressure-decay leak test** | Test at 1.5x working pressure for 30 s; leak rate not above 2.0 cc/min | CC | Pressure-decay leak tester | 100% of valve bodies | R3 |
| 10 | CMM inspection | Port positions and hole patterns | Per drawing | Standard | CMM | 1 piece per 25 | R1 |

## 4. Enhanced Controls for Castings from Escalated Suppliers

While a supplier is under a SCAR or controlled shipping, the following additional controls apply to castings from that supplier:

1. Incoming lots are sampled at tightened inspection (QP-7.4) and each lot is sectioned for porosity.
2. Machining of the bore is monitored for porosity exposed in the first cut; any porosity visible in the bore after the first operation triggers R3.
3. First-article leak test of 5 pieces at the start of each lot before releasing the lot to production.
4. Findings are logged on NCRs with the defect code "Porosity" or "Leak at test" so that COPQ attributable to the supplier can be charged back under the supplier agreement.

## 5. Reaction Plans

**R1: Standard characteristic out of specification**
Adjust, verify 3 good pieces, sort pieces since last good check, raise an NCR.

**R2: Bore diameter or cylindricity out of specification**
1. Stop the machine and notify the quality engineer.
2. Hold and 100% re-measure all parts since the last good check.
3. Check tool wear, offsets, thermal drift and spindle condition; compare against the maintenance record of the machine.
4. Restart only after 3 consecutive good pieces and CMM confirmation.
5. Two events on the same machine within 5 working days require a Major NCR and CAPA review (QP-10.2). Note that bore position drift at Greenville (CAPA-2026-103) was traced to spindle condition, so spindle vibration should be reviewed on repeated bore events.

**R3: Porosity or leak failure**
1. Segregate the part and the rest of the casting lot; raise a Major NCR (QP-8.7).
2. Scrap leaking parts. Machined castings scrapped for hidden porosity are costed at full machining value.
3. If 2 or more porosity or leak failures occur in a 50-piece sample, place the casting lot on Quality Hold (MES reason code "Quality Hold") and sort 100% before further machining.
4. Notify the supplier quality engineer (Rosa Martinez) within the shift.

## 6. Capability Monitoring

| Characteristic | Target |
|---|---|
| Bore diameter Cpk | At least 1.33 |
| Leak test first-pass rate | Reviewed weekly; trends reported to the monthly quality review |
| Porosity NCR count by casting supplier | Reviewed weekly |

## 7. Revision History

| Rev | Date | Change |
|---|---|---|
| B | 2024-11-18 | Added leak test pressure-decay limit |
| C | 2026-01-12 | Bore tolerance confirmed at +/- 0.015 mm; added enhanced controls for escalated suppliers |
