# Control Plan: Wire Cut & Crimp (WRO-L1)

| Field | Value |
|---|---|
| Document ID | CP-WRO-L1 |
| Title | Control Plan, Wire Cut & Crimp, Wroclaw Electrical Plant |
| Revision | Rev F |
| Effective Date | 2026-03-02 |
| Owner | Tomasz Wisniewski, Wroclaw Quality Engineer |
| Approver | Katarzyna Nowak, Wroclaw Plant Manager; Elena Ramirez, Director of Quality |
| Classification | Internal |

## 1. Scope

This control plan covers production on WRO-L1 Wire Cut & Crimp, which has four work centers in process order: WC01 Wire Cut & Strip, WC02 Terminal Crimp Press #2, WC03 Terminal Crimp Press #3 and WC04 Crimp Pull Tester. It is a production-phase plan derived from the process FMEA and the PPAP package.

## 2. General Requirements

- Process capability: Cpk of at least **1.33** on every critical characteristic, evaluated monthly from at least 125 consecutive pieces; Ppk of at least 1.67 at PPAP.
- Measurement system analysis: gauge R&R below 10% of tolerance for critical characteristics (acceptable up to 30% for non-critical, with approval).
- Setup: only certified setters may release a die change. Die setup follows the current work instruction (WI-WRO-CR-07 Rev E).
- Characteristics marked CC are critical and require immediate containment per the reaction plan.

## 3. Control Plan Table

| # | Work center | Characteristic | Spec | Class | Measurement method | Sample size and frequency | Control method | Reaction plan |
|---|---|---|---|---|---|---|---|---|
| 1 | WC01 | Cut length | Nominal +/- 1.0 mm | Standard | Calibrated steel rule / length gauge | 5 pieces per hour | X-bar R chart | R1 |
| 2 | WC01 | Strip length | Nominal +/- 0.5 mm | Standard | Optical comparator / strip gauge | 5 pieces per hour | X-bar R chart | R1 |
| 3 | WC01 | Strand nicking | No cut strands | Standard | Visual at 10x | 5 pieces per reel | Visual aid | R1 |
| 4 | WC02 / WC03 | **Crimp height** | **1.650 mm +/- 0.050 mm** (1.600 to 1.700) | **CC** | Crimp height micrometer with pointed anvil | First piece, then 5 pieces every hour and after any die change or reel change | X-bar R chart; Cpk monitored | R2 |
| 5 | WC02 / WC03 | Crimp width | 2.35 mm +/- 0.10 mm | Standard | Crimp width gauge | 3 pieces every 2 hours | Chart | R1 |
| 6 | WC02 / WC03 | Crimp force (process monitor) | Within validated window; alarm thresholds locked | CC | Inline crimp force monitor (CFM) | 100% of crimps | CFM alarm; threshold change requires supervisor and quality sign-off | R2 |
| 7 | WC02 / WC03 | Insulation grip / wire brush position | Per drawing | Standard | Visual / cross-section | First piece and 1 per shift | Checklist | R1 |
| 8 | WC04 | **Pull force** | Minimum per wire gauge, e.g. 90 N for 1.5 mm2 wire | **CC** | Crimp pull tester, 100 mm/min | 5 pieces per hour per press and after any die change | Run chart | R2 |
| 9 | WC02 / WC03 | Terminal type | Part-specific terminal | CC | Visual against reel label and setup sheet; barcode scan | Each reel change | Barcode interlock | R2 |
| 10 | WC02 / WC03 | Cross-section (destructive) | Compression and strand fill per IPC/WHMA-A-620 | Standard | Microsection | 1 per die change and 1 per month per press | Lab report | R1 |

## 4. Reaction Plans

**R1: Standard characteristic out of specification**
1. Stop the machine; tag and hold all product since the last good check.
2. Adjust and re-verify with 3 consecutive good pieces.
3. Sort held product 100%; raise an NCR (QP-8.7).
4. Record in the shift log.

**R2: Critical characteristic out of specification (crimp height, pull force, force monitor alarm, wrong terminal)**
1. **Stop and contain at any out-of-spec reading.** No tolerance for "one more check".
2. Notify the shift supervisor and quality engineer immediately; log the event in the MES with reason code "Quality Hold".
3. Hold, segregate and 100% sort all product since the last in-spec reading, including product at WC04 and downstream.
4. Do not restart until root cause has been identified and corrected, first-piece approval has been passed and a certified setter has signed the setup record.
5. Open an NCR (Major). Two events of the same defect code within 5 working days require a CAPA under QP-10.2.
6. Never widen CFM thresholds or adjust limits without a documented change approved by quality (introduced after 8D-WRO-2026-009).

## 5. Capability Monitoring

| Metric | Target | Review |
|---|---|---|
| Cpk, crimp height | At least 1.33 | Monthly, by press and by shift |
| Pull force Cpk | At least 1.33 | Monthly |
| In-process defect rate, crimp height | Baseline about 1.2% to 1.5% | Weekly, by shift |

If Cpk falls below 1.33, increase sampling to every 30 minutes and start containment until Cpk is restored; two consecutive months below 1.33 triggers a CAPA (QP-10.2).

## 6. Revision History

| Rev | Date | Change |
|---|---|---|
| E | 2025-04-14 | Added pull force frequency after die change |
| F | 2026-03-02 | Crimp height 1.650 +/- 0.050 mm confirmed as CC; CFM monitor added; reaction plan R2 revised to "stop and contain" |
| G (draft) | pending | Add threshold verification after die change (see 8D-WRO-2026-009 D7) |

## 7. Related Documents

WI-WRO-CR-07 Rev E (die shut-height setting), QP-8.7, QP-10.2, 8D-WRO-2026-009, GLS-QUA-001.
