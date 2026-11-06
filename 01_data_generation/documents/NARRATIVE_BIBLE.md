# Narrative Bible — KK's Parts (FY2026)

**Single source of truth for every document in `documents/`.** Every name, ID, date, limit, and
number a document mentions must match this file, which in turn matches the generated data
(`_story/story_anchors.json` in the raw volume, seed 42). If you change the `story:` block in
`config/demo_config.yml`, regenerate the data, re-read the anchors, and update this file before
regenerating documents.

Data window: **2025-10-01 → 2026-09-30 (FY2026)**. Documents are dated inside that window,
mostly Q3–Q4 FY2026 (April–September 2026). "Today" for the documents is late September 2026.

---

## Company

**KK's Parts** ("KK's Parts") — a mid-size industrial components manufacturer
selling hydraulics, drivetrain, housings, wire harnesses/controls, and fasteners to OEMs in
agriculture, construction, mining, energy, rail, and trucking.

| Plant | Name | Location | Family | PM compliance target | FY26 PM compliance (actual) | FY26 OEE |
|---|---|---|---|---|---|---|
| CLB | Columbus Hydraulics Plant | Columbus, OH | Hydraulic Components | 97% | 96.6% | 81.3% |
| GVL | Greenville Drivetrain Plant | Greenville, SC | Gears & Drivetrain | 84% | 80.6% (GVL-L3: 76.7%) | 78.3% |
| MTY | Monterrey Machining Plant | Monterrey, NL, Mexico | Machined Housings | 90% | 92.0% | 78.2% |
| WRO | Wroclaw Electrical Plant | Wroclaw, Poland | Wire Harnesses & Controls | 92% | 97.9% | 83.0% |
| PNQ | Pune Fastener Plant | Pune, MH, India | Precision Fasteners & Stampings | 91% | 96.0% | 83.8% |

Corporate PM compliance policy target is **95%**. Corporate OEE target is **85%** ("world-class").

### Lines (plant → line → process flow of work centers)
- CLB-L1 Valve Body Machining · CLB-L2 Pump Assembly · CLB-L3 Cylinder Fabrication
- GVL-L1 Gear Hobbing · GVL-L2 Heat Treat · **GVL-L3 Gearbox Assembly** (WC01 CNC HMC #1 → WC02 CNC HMC #2 → WC03 Servo Press-Fit → WC04 Robotic Assembly Cell → WC05 End-of-Line Test Stand → WC06 Packaging; ideal cycle 156.5 s/unit)
- MTY-L1 Casting Finishing · MTY-L2 Housing Machining · MTY-L3 Paint & Coat
- **WRO-L1 Wire Cut & Crimp** (WC01 Wire Cut & Strip → WC02 Terminal Crimp Press #2 → WC03 Terminal Crimp Press #3 → WC04 Crimp Pull Tester) · WRO-L2 Harness Assembly · WRO-L3 Control Module Assembly
- PNQ-L1 Cold Heading · PNQ-L2 Stamping · PNQ-L3 Plating & Finishing

Work center IDs follow `<LINE>-WC<nn>` in process order. Machine criticality: **A** (bottleneck / no redundancy), **B**, **C**.

Shifts: **A** 06:00–14:00, **B** 14:00–22:00, **C** 22:00–06:00. Mon–Fri three shifts, Saturday A+B, Sunday dark.
Planned production time = 450 min per shift (480 minus 30-min break).

Downtime reason codes used in MES (exactly these six): **Equipment Failure, Planned Maintenance,
Changeover, Material Shortage, Quality Hold, No Operator.**

Warehouses: WH-CLB, WH-GVL, WH-MTY, WH-WRO, WH-PNQ (plant warehouses) and distribution centers
**DC-MEM Memphis**, **DC-RNO Reno**, **DC-RTM Rotterdam**.

### People (fictional — use these names consistently)
| Role | Name |
|---|---|
| VP Operations (corporate) | Dana Whitfield |
| Director of Reliability & Maintenance (corporate) | Marcus Okafor |
| Director of Quality (corporate) | Elena Ramirez |
| Director of Supply Chain & Logistics | Priya Nair |
| Greenville Plant Manager | Tom Brennan |
| Greenville Maintenance Manager | Luis Hernandez |
| Greenville reliability engineer | Ashley Taylor |
| Columbus Plant Manager | Kevin Thompson |
| Monterrey Plant Manager | Alejandro Reyes |
| Monterrey Quality Manager | Guadalupe Flores |
| Wroclaw Plant Manager | Katarzyna Nowak |
| Wroclaw Quality Engineer | Tomasz Wisniewski |
| Wroclaw C-shift supervisor | Marek Kaminski |
| Supplier Quality Engineer (castings) | Rosa Martinez |
| Logistics Manager, Memphis DC | Brian Wilson |
| Hartwell Machine Tools field service engineer | Gary Lindqvist |
| Brightline Castings quality manager | Hector Salinas |
| Ridgeway Freight account manager | Janet Cole |
| Apex Agricultural Equipment — Director of Supplier Management | Rebecca Haines |

---

## Storyline 1 — The failing spindle (Maintenance ⇄ Production ⇄ Quality)

- Asset: **GVL-L3-WC01**, *CNC Horizontal Machining Center #1*, Greenville Gearbox Assembly, OEM **Hartwell Machine Tools**, model **HAR-119**, installed 2013-08-27, criticality **A** (line bottleneck; machines the gearbox bearing bores).
- Normal running vibration ≈ **2.8 mm/s**. Spindle bearing wear begins **2026-03-15**.
- Average running vibration by month (mm/s): Mar 2.85 · **Apr 3.44 · May 4.39 · Jun 5.23 · Jul 6.46 · Aug 7.57 · Sep 8.75**.
- **Hartwell OEM service manual** (HMC-Series, section 7.4): alert at **3.5 mm/s**, **replace spindle bearings at 4.5 mm/s** (ISO 10816 zone C/D boundary for this class).
- **KK's Parts internal PM procedure PM-CNC-030 Rev C (2019)** uses an outdated limit of **7.1 mm/s** to trigger bearing replacement. Monthly PMs on WC01 were *completed* in April, May, July, August (vibration recorded but "within PM-CNC-030 limit") — so nobody acted until it crossed 7.1 in August. Two PMs were deferred (due 2026-06-27 and 2026-09-04).
- Vibration crossed the OEM limit in **June 2026** — about **two months before** the internal limit was reached.
- Since 2026-03-15: **30 breakdowns** (Emergency/Corrective WOs, almost all "spindle bearing wear"), **≈286 hours** of repair time, **≈$146K Hartwell field-service/contractor cost** and **≈$243K total parts + contractor cost**.
- GVL-L3 line OEE by month: Oct 82% · Jan 82% · Mar 84% · **Apr 76% · May 67% · Jun 60% · Jul 55% · Aug 58% · Sep 50%**.
- Quality spill-over: "Bore out of tolerance" NCRs on GVL-L3 rise (bearing bore position drift). **CAPA-2026-103** "Bore position drift on GVL-L3-WC01 (spindle condition)" — opened 2026-05-24, due 2026-07-23, status **Open (overdue)**.
- Replacement spindle cartridge lead time from Hartwell: **10 weeks**; no spare on site. Quote **$68,400** installed.
- Pending **MOC-2026-031** (Management of Change) to align PM-CNC-030 with the OEM limit — submitted July 2026, awaiting engineering approval.
- Root-cause language: lubrication degradation + bearing preload loss, accelerated by deferred PMs and a too-loose PM limit.

## Storyline 2 — Brightline Castings (Supply Chain ⇄ Quality ⇄ Production)

- Supplier **SUP-1007 Brightline Castings**, Saltillo, Mexico. Primary source for **MAT-5001 Valve Body Casting, MAT-5002 Pump Housing Casting, MAT-5004 Manifold Casting, MAT-5005 Bearing Cap Casting** (Gearbox Housing Casting MAT-5003 comes from SUP-1002 Keystone Foundry). Ships to **CLB and MTY** (and GVL for some castings).
- Issue start **2026-05-01** (Brightline moved production to a new furnace line / changed sand supplier).
- On-time delivery: **92% before → 44% after**; average lateness when late after May **9.3 days**.
- Incoming quality: **237 PPM before → 2,726 PPM after**, vs contract limit **500 PPM** in the Supplier Quality Agreement (SQA-BLC-2023, defect PPM limit 500; on-time target 95%; SCAR response within 10 business days; 8D within 30 days).
- Effects: **214 material-shortage downtime events** on consuming lines (mostly GVL-L3, MTY-L3, CLB-L2 and MTY-L1); **380 porosity NCRs** after May; **≈$1.68M** cost of poor quality from porosity since May.
- **SCAR-2026-014** issued to Brightline 2026-05-25 → tracked as **CAPA-2026-101** "SCAR: casting porosity from Brightline Castings", due 2026-07-24, status **Overdue**. Brightline's 8D response was late and incomplete (containment only, no permanent corrective action).
- Alternates: **SUP-1002 Keystone Foundry** (Erie, USA, PPM limit 500) and **SUP-1003 Silesia Metalworks** (Katowice, Poland, PPM limit 250). A dual-sourcing proposal (Keystone for MAT-5001/5002) is under review: PPAP ~12 weeks, +6% piece price.

## Storyline 3 — Ridgeway Freight (Supply Chain / outbound logistics)

- Carrier **CAR-04 Ridgeway Freight** (LTL), lane origin **DC-MEM Memphis**. Carries **≈38%** of Memphis shipments.
- Carrier on-time (delivered by carrier due date = ship date + planned transit): **77%** for FY26 vs contract SLA **95%**. Other carriers: Summit Logistics 94.6%, BlueLine Express 97.4%, TransAmerica Truckload 93.5%, Coastal Intermodal 93.2%, Rhine-Maas 94.1%, EuroSprint 92.2%, Pacific Rim Forwarding 88.1%.
- Ridgeway by month: Oct 79% · **Nov 69%** · Dec 75% · Jan–Jun 78–82% · **Jul 74% · Aug 72% · Sep 73%** (peak season and summer driver shortage).
- Contract **CTA-RF-2024-07**: 95% on-time SLA, service credit of 2% of monthly freight spend for each point below 92%, quarterly business review, termination for convenience with 60 days notice.
- Customer impact: **CUST-2001 Apex Agricultural Equipment** (Strategic, served from DC-MEM): on-time to customer-requested date **91.7% on Ridgeway** shipments vs ~98% on other carriers (95.8% on-time overall). Measured as **OTIF** (on time AND in full) Apex is at **≈92.6% overall** and **88.3% on Ridgeway** — below the standard. Apex's supplier scorecard requires **95% OTIF**. Apex's Director of Supplier Management **Rebecca Haines** sent an escalation letter in August 2026.

## Storyline 4 — Night-shift crimp defects (Quality ⇄ Production)

- Machine **WRO-L1-WC02**, *Terminal Crimp Press #2*, OEM **Lumex Equipment**, model **LUM-486**, Wroclaw Wire Cut & Crimp line.
- After a crimp die change on **2026-06-08**, **C shift (22:00–06:00)** sees crimp-height defects: in-process defect rate **13.6% on C shift vs ~1.4–1.5% on A/B** (before June 8 all shifts ~1.2–1.5%).
- Critical characteristic: **crimp height 1.650 mm ± 0.050 mm** (control plan CP-WRO-L1 Rev F). Reaction plan: stop and contain at any out-of-spec reading; Cpk target ≥ 1.33.
- Root cause (8D in progress): night-shift setup uses a superseded work instruction **WI-WRO-CR-07 Rev D** (die shut-height setting) rather than **Rev E**; C shift also lacks a Level 3 certified setter since May. Crimp force monitor alarm thresholds were widened during die change and not restored.
- **CAPA-2026-102** "Crimp height variation on WRO-L1-WC02 night shift", opened 2026-07-08, due 2026-08-22, status **In Progress**. 8D number **8D-WRO-2026-009**.

## Positive benchmark — Columbus
- CLB keeps **96.6% PM compliance**, lowest breakdown rate, OEE 81.3% (highest of the US plants). Practices: condition-based PM triggers at OEM limits, weekly reliability stand-up, spare-spindle program for A-critical CNCs. Useful contrast to Greenville.

---

## Key definitions (must match the gold metric views)
- **OEE** = Availability × Performance × Quality. Availability = run minutes ÷ planned minutes; Performance = (total units × ideal cycle time) ÷ run time; Quality = good units ÷ total units.
- **First Pass Yield (FPY)** = good units ÷ total units (scrap and rework both count as not-first-pass).
- **PPM (supplier)** = rejected qty ÷ received qty × 1,000,000.
- **COPQ** = cost of poor quality from NCRs (scrap value, rework cost, handling).
- **PM compliance** = completed preventive WOs ÷ preventive WOs due.
- **MTBF** = run hours ÷ failure count; **MTTR** = repair hours ÷ failure count.
- **Supplier OTD** = receipts with days_late = 0 ÷ receipts.
- **Carrier on-time** = delivered on/before carrier due date. **Customer OTIF** = delivered on/before customer-requested date AND full quantity.
- **Days of supply** = on-hand ÷ average daily demand. Stockout = on-hand < allocated.
