"""
mfg_datagen — synthetic source-system data for KK's Parts.

WHY THIS EXISTS
---------------
Agents are only as convincing as the data they reason over. Random data gives
random answers. This generator builds data with *causal chains* so that the
supervisor agent can discover real stories by combining Genie spaces:

    machine health  ──► sensor drift ──► breakdowns ──► emergency work orders
          ▲                                  │
    skipped PMs                              ▼
                                   line downtime ──► lower OEE ──► FG stockouts
    supplier quality/lateness ──► incoming NCRs, porosity scrap,     │
                                  material-shortage downtime         ▼
    carrier performance ───────────────────────────────► late customer shipments

The four storylines in `story:` (demo_config.yml) are planted on top of that
baseline, and the Genie documents are written around the same names and numbers.

DESIGN
------
* Pure pandas/numpy — runs on serverless compute with no %pip installs, and
  locally for fast iteration (`python mfg_datagen.py --out /tmp/mfg_raw`).
* Output mimics *source systems*, not a clean star schema. Each table is tagged
  with the system it "came from" (ERP, MES, CMMS, QMS, WMS, IoT historian, HR)
  and lands as CSV / JSON / Parquet in a UC Volume. The medallion pipeline
  (02_medallion_pipeline) is what turns this into analytics-ready data.
* A little realistic mess is injected (duplicate sensor rows, mixed-case
  status codes, missing readings) so the silver layer has real work to do.
* Deterministic: same seed + same config = identical data, which keeps the
  hand-written documents accurate across re-deploys.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

# =============================================================================
# 1. REFERENCE CATALOGS
#    Static knowledge about machine types, products, and suppliers. Changing a
#    value here changes the "physics" of the plant.
# =============================================================================

# machine type -> display name, OEMs, sensor baselines, PM interval, failure modes
MACHINE_TYPES: dict[str, dict] = {
    "CNC_MILL":             dict(name="CNC Vertical Mill",        oems=["Hartwell Machine Tools", "Sato Precision"],     temp=38, vib=2.4, kw=22, pm=30, modes=["spindle bearing wear", "tool changer fault", "coolant pump failure", "servo drive fault"]),
    "CNC_LATHE":            dict(name="CNC Turning Center",       oems=["Hartwell Machine Tools", "Sato Precision"],     temp=36, vib=2.1, kw=18, pm=30, modes=["chuck hydraulic leak", "turret indexing fault", "spindle bearing wear", "servo drive fault"]),
    "CNC_MACHINING_CENTER": dict(name="CNC Horizontal Machining Center", oems=["Hartwell Machine Tools", "Sato Precision"], temp=40, vib=2.8, kw=30, pm=30, modes=["spindle bearing wear", "pallet changer fault", "tool changer fault", "coolant pump failure"]),
    "GEAR_HOBBER":          dict(name="CNC Gear Hobber",          oems=["Nordberg Gear Systems"],                        temp=37, vib=2.6, kw=26, pm=45, modes=["hob spindle wear", "indexing table fault", "lube system failure"]),
    "DEBURR_CELL":          dict(name="Robotic Deburr Cell",      oems=["Vantage Robotics"],                             temp=31, vib=1.6, kw=8,  pm=60, modes=["servo fault", "spindle motor failure", "sensor misalignment"]),
    "WASH_STATION":         dict(name="Parts Washer",             oems=["Brenner Finishing"],                            temp=55, vib=0.9, kw=15, pm=60, modes=["pump failure", "heater element failure", "nozzle clog"]),
    "CMM_INSPECTION":       dict(name="Coordinate Measuring Machine", oems=["Calder Test Systems"],                      temp=21, vib=0.3, kw=3,  pm=90, modes=["probe calibration drift", "air bearing fault"]),
    "PRESS_FIT":            dict(name="Servo Press-Fit Station",  oems=["Nordberg Presses"],                             temp=33, vib=1.4, kw=11, pm=45, modes=["load cell drift", "servo fault", "fixture wear"]),
    "ASSEMBLY_CELL":        dict(name="Robotic Assembly Cell",    oems=["Vantage Robotics", "Kessler Automation"],       temp=30, vib=1.2, kw=9,  pm=60, modes=["gripper failure", "vision sensor fault", "PLC fault", "servo fault"]),
    "TEST_STAND":           dict(name="End-of-Line Test Stand",   oems=["Calder Test Systems"],                          temp=34, vib=1.0, kw=12, pm=60, modes=["calibration drift", "fixture wear", "pressure transducer failure"]),
    "PACKAGING":            dict(name="Automated Packaging Line", oems=["Kessler Automation"],                           temp=28, vib=1.1, kw=6,  pm=60, modes=["conveyor belt wear", "label printer fault", "jam"]),
    "SAW_CELL":             dict(name="Automatic Band Saw",       oems=["Ironbridge Industrial"],                        temp=35, vib=2.2, kw=7,  pm=45, modes=["blade wear", "hydraulic feed fault"]),
    "ROBOTIC_WELDER":       dict(name="Robotic MIG Welder",       oems=["Vantage Robotics"],                             temp=42, vib=1.5, kw=14, pm=45, modes=["wire feed jam", "torch failure", "servo fault"]),
    "PAINT_BOOTH":          dict(name="Paint Booth",              oems=["Brenner Finishing"],                            temp=27, vib=0.8, kw=20, pm=60, modes=["filter clog", "atomizer failure", "airflow fault"]),
    "HEAT_TREAT_FURNACE":   dict(name="Carburizing Furnace",      oems=["Orion Thermal Systems"],                        temp=890, vib=0.6, kw=180, pm=60, modes=["heating element failure", "thermocouple drift", "atmosphere control fault"]),
    "QUENCH_TANK":          dict(name="Oil Quench Tank",          oems=["Orion Thermal Systems"],                        temp=70, vib=0.7, kw=25, pm=90, modes=["agitator failure", "oil cooler fault"]),
    "HARDNESS_TESTER":      dict(name="Automatic Hardness Tester", oems=["Calder Test Systems"],                         temp=22, vib=0.4, kw=2,  pm=90, modes=["indenter wear", "calibration drift"]),
    "SHOT_BLAST":           dict(name="Shot Blast Cabinet",       oems=["Ironbridge Industrial"],                        temp=32, vib=3.1, kw=19, pm=30, modes=["blast wheel wear", "dust collector fault"]),
    "LEAK_TESTER":          dict(name="Helium Leak Tester",       oems=["Calder Test Systems"],                          temp=24, vib=0.5, kw=4,  pm=90, modes=["seal fixture wear", "sensor drift"]),
    "CURE_OVEN":            dict(name="Cure Oven",                oems=["Orion Thermal Systems"],                        temp=185, vib=0.6, kw=60, pm=60, modes=["burner fault", "conveyor drive failure", "thermocouple drift"]),
    "WIRE_CUTTER":          dict(name="Automatic Wire Cut & Strip", oems=["Lumex Equipment"],                            temp=29, vib=1.3, kw=4,  pm=45, modes=["blade wear", "feed roller slip"]),
    "CRIMP_PRESS":          dict(name="Terminal Crimp Press",     oems=["Lumex Equipment"],                              temp=31, vib=1.8, kw=3,  pm=30, modes=["crimp die wear", "crimp force monitor fault", "applicator jam"]),
    "PULL_TESTER":          dict(name="Crimp Pull Tester",        oems=["Calder Test Systems"],                          temp=23, vib=0.4, kw=1,  pm=90, modes=["load cell drift"]),
    "CONTINUITY_TESTER":    dict(name="Harness Continuity Tester", oems=["Calder Test Systems"],                         temp=24, vib=0.3, kw=1,  pm=90, modes=["fixture pin wear", "software fault"]),
    "SMT_PLACER":           dict(name="SMT Pick-and-Place",       oems=["Lumex Equipment"],                              temp=30, vib=1.0, kw=7,  pm=30, modes=["nozzle clog", "feeder fault", "vision camera fault"]),
    "REFLOW_OVEN":          dict(name="Reflow Oven",              oems=["Orion Thermal Systems"],                        temp=245, vib=0.5, kw=35, pm=60, modes=["heater zone failure", "conveyor fault"]),
    "AOI_INSPECTION":       dict(name="Automated Optical Inspection", oems=["Calder Test Systems"],                      temp=25, vib=0.3, kw=2,  pm=90, modes=["camera calibration drift", "lighting failure"]),
    "WIRE_DRAWER":          dict(name="Wire Drawing Machine",     oems=["Ironbridge Industrial"],                        temp=48, vib=2.9, kw=45, pm=45, modes=["die wear", "capstan bearing wear"]),
    "COLD_HEADER":          dict(name="Multi-Station Cold Header", oems=["Nordberg Presses"],                            temp=46, vib=4.2, kw=75, pm=30, modes=["punch breakage", "transfer finger fault", "lube system failure"]),
    "THREAD_ROLLER":        dict(name="Thread Rolling Machine",   oems=["Nordberg Presses"],                             temp=41, vib=3.0, kw=18, pm=45, modes=["die wear", "feed fault"]),
    "OPTICAL_SORTER":       dict(name="Optical Sorting Machine",  oems=["Calder Test Systems"],                          temp=26, vib=0.8, kw=3,  pm=90, modes=["camera fault", "reject air jet failure"]),
    "COIL_FEEDER":          dict(name="Servo Coil Feeder",        oems=["Nordberg Presses"],                             temp=30, vib=1.5, kw=6,  pm=60, modes=["straightener roll wear", "servo fault"]),
    "STAMPING_PRESS":       dict(name="Progressive Stamping Press", oems=["Nordberg Presses"],                           temp=44, vib=3.6, kw=90, pm=30, modes=["clutch/brake wear", "die damage", "hydraulic overload fault"]),
    "PLATING_TANK":         dict(name="Zinc-Nickel Plating Line", oems=["Brenner Finishing"],                            temp=38, vib=0.6, kw=40, pm=60, modes=["rectifier fault", "pump failure", "bath chemistry drift"]),
}

# plant -> part prefix, ideal seconds per unit, price band, and part names (3 per line)
PLANT_PRODUCTS: dict[str, dict] = {
    "CLB": dict(prefix="HYD", cycle_s=95, cost=(85, 650), names=[
        ["Directional Control Valve Body", "Pressure Relief Valve Body", "Flow Control Valve Body"],
        ["Gear Pump 16cc", "Gear Pump 32cc", "Axial Piston Pump 45cc"],
        ["Tie-Rod Cylinder 2in Bore", "Welded Cylinder 3in Bore", "Telescopic Cylinder 4-Stage"]]),
    "GVL": dict(prefix="DRV", cycle_s=140, cost=(60, 1900), names=[
        ["Helical Gear 42T", "Spur Gear 28T", "Ring Gear 96T"],
        ["Carburized Pinion Shaft", "Hardened Ring Gear Set", "Case-Hardened Spline Shaft"],
        ["Planetary Gearbox PG-200", "Right-Angle Gearbox RA-150", "Inline Gearbox IL-90"]]),
    "MTY": dict(prefix="HSG", cycle_s=180, cost=(45, 380), names=[
        ["Pump Housing Casting (Finished)", "Valve Manifold Casting (Finished)", "Bearing Cap Casting (Finished)"],
        ["Gearbox Housing GH-200", "Motor End Bell ME-90", "Transmission Case Half TC-150"],
        ["Powder-Coated Housing GH-200", "E-Coated Bracket Assembly", "Painted Cover Plate"]]),
    "WRO": dict(prefix="ELC", cycle_s=26, cost=(4, 140), names=[
        ["Crimped Lead 18AWG", "Crimped Lead 14AWG", "Shielded Lead 22AWG"],
        ["Engine Harness EH-12", "Cab Harness CH-08", "Sensor Jumper Harness SJ-04"],
        ["Pump Controller Module PCM-3", "Valve Driver Board VDB-2", "Telematics Interface Unit TIU-1"]]),
    "PNQ": dict(prefix="FST", cycle_s=3, cost=(0.08, 2.4), names=[
        ["Hex Flange Bolt M10x40", "Socket Head Cap Screw M8x25", "Shoulder Bolt M12x60"],
        ["Stamped Bracket SB-14", "Stamped Clip SC-03", "Progressive-Die Washer PW-20"],
        ["Zn-Ni Plated Bolt M10x40", "Zn-Ni Plated Stud M12x80", "Passivated Washer M10"]]),
}

# each line has one critical-to-quality characteristic measured during in-process inspection
LINE_CHARACTERISTIC = {
    "CNC_MILL": ("Bore diameter", "mm", 25.000, 0.015), "PRESS_FIT": ("Press-fit force", "kN", 12.0, 1.5),
    "SAW_CELL": ("Cylinder wall thickness", "mm", 6.35, 0.10), "CNC_LATHE": ("Shaft OD", "mm", 40.000, 0.020),
    "WASH_STATION": ("Case hardness", "HRC", 60.0, 2.0), "CNC_MACHINING_CENTER": ("Bearing bore position", "mm", 0.000, 0.025),
    "SHOT_BLAST": ("Surface porosity", "count/cm2", 0.0, 1.0), "WIRE_CUTTER": ("Crimp height", "mm", 1.650, 0.050),
    "ASSEMBLY_CELL": ("Circuit continuity resistance", "ohm", 0.050, 0.030), "SMT_PLACER": ("Solder joint height", "mm", 0.120, 0.030),
    "WIRE_DRAWER": ("Head height", "mm", 6.400, 0.150), "COIL_FEEDER": ("Flatness", "mm", 0.000, 0.080),
}

# in-process defect codes by plant
DEFECT_CODES = {
    "CLB": ["Bore out of tolerance", "Porosity", "Surface finish", "Leak at test", "Weld undercut"],
    "GVL": ["Tooth profile error", "Bore out of tolerance", "Hardness out of spec", "Noise at test", "Burr"],
    "MTY": ["Porosity", "Bore out of tolerance", "Coating thickness", "Leak at test", "Casting inclusion"],
    "WRO": ["Crimp height out of spec", "Wrong terminal", "Open circuit", "Solder bridge", "Insulation damage"],
    "PNQ": ["Thread defect", "Head crack", "Plating thickness", "Burr", "Dimensional - length"],
}

SUPPLIER_CATEGORIES = {
    # category -> (materials, unit, unit cost range, lead time days, consuming plants)
    "Castings":                (["Valve Body Casting", "Pump Housing Casting", "Gearbox Housing Casting", "Manifold Casting", "Bearing Cap Casting"], "EA", (18, 140), 21, ["CLB", "MTY", "GVL"]),
    "Steel Bar & Coil":        (["4140 Steel Bar 2in", "8620 Steel Bar 3in", "1018 Cold-Rolled Coil", "4340 Steel Forging Blank"], "KG", (1.1, 3.8), 28, ["CLB", "GVL", "PNQ"]),
    "Bearings":                (["Tapered Roller Bearing 32210", "Deep Groove Ball Bearing 6205", "Needle Bearing NK25"], "EA", (4, 48), 35, ["GVL", "CLB"]),
    "Seals & O-Rings":         (["Viton O-Ring Kit", "Rod Seal 50mm", "Piston Seal 80mm"], "EA", (0.6, 9), 14, ["CLB"]),
    "Hydraulic Fittings":      (["SAE O-Ring Boss Fitting", "JIC 37deg Fitting", "Hydraulic Hose Assembly"], "EA", (2, 26), 21, ["CLB"]),
    "Wire & Cable":            (["18AWG GXL Wire", "14AWG GXL Wire", "22AWG Shielded Cable"], "M", (0.08, 0.9), 21, ["WRO"]),
    "Electronic Components":   (["MCU 32-bit ARM", "Power MOSFET 60V", "Sealed Connector 12-Pin", "Crimp Terminal 0.64mm"], "EA", (0.05, 7.5), 42, ["WRO"]),
    "Fastener Wire":           (["10B21 Cold-Heading Wire", "1022 Cold-Heading Wire"], "KG", (1.3, 2.4), 30, ["PNQ"]),
    "Coatings & Chemicals":    (["Zinc-Nickel Plating Chemistry", "Powder Coat Black RAL9005", "E-Coat Resin"], "KG", (6, 32), 14, ["MTY", "PNQ", "CLB"]),
    "Packaging":               (["Corrugated Shipper Box", "VCI Poly Bag", "Wood Pallet 48x40"], "EA", (0.2, 14), 10, ["CLB", "GVL", "MTY", "WRO", "PNQ"]),
}

SUPPLIER_NAMES = [
    ("Brightline Castings", "Saltillo", "Mexico", "Castings"),
    ("Keystone Foundry", "Erie", "USA", "Castings"),
    ("Silesia Metalworks", "Katowice", "Poland", "Castings"),
    ("Allegheny Bar Products", "Pittsburgh", "USA", "Steel Bar & Coil"),
    ("Tata Precision Steel", "Jamshedpur", "India", "Steel Bar & Coil"),
    ("Rhein Stahl Service", "Duisburg", "Germany", "Steel Bar & Coil"),
    ("Sentinel Bearings", "Greenville", "USA", "Bearings"),
    ("Kyoei Bearing Co.", "Osaka", "Japan", "Bearings"),
    ("Delta Seal Technologies", "Cleveland", "USA", "Seals & O-Rings"),
    ("ProFlow Fittings", "Toledo", "USA", "Hydraulic Fittings"),
    ("Ohio Valley Hydraulics", "Dayton", "USA", "Hydraulic Fittings"),
    ("Vistula Cable Works", "Gdansk", "Poland", "Wire & Cable"),
    ("NordWire GmbH", "Hamburg", "Germany", "Wire & Cable"),
    ("Pacific Semicon Supply", "Penang", "Malaysia", "Electronic Components"),
    ("Arrowpoint Electronics", "Austin", "USA", "Electronic Components"),
    ("Danube Connectors", "Budapest", "Hungary", "Electronic Components"),
    ("Deccan Wire Industries", "Pune", "India", "Fastener Wire"),
    ("Sahyadri Steel Wire", "Nashik", "India", "Fastener Wire"),
    ("ChemCoat Solutions", "Houston", "USA", "Coatings & Chemicals"),
    ("Lusitania Finishes", "Porto", "Portugal", "Coatings & Chemicals"),
    ("Midwest Corrugated", "Indianapolis", "USA", "Packaging"),
    ("EuroPack Logistics", "Lodz", "Poland", "Packaging"),
    ("Monterrey Empaques", "Monterrey", "Mexico", "Packaging"),
    ("Konkan Packaging", "Mumbai", "India", "Packaging"),
]

CARRIERS = [
    ("CAR-01", "Summit Logistics", "LTL"), ("CAR-02", "BlueLine Express", "Parcel"),
    ("CAR-03", "TransAmerica Truckload", "FTL"), ("CAR-04", "Ridgeway Freight", "LTL"),
    ("CAR-05", "Coastal Intermodal", "Intermodal"), ("CAR-06", "Rhine-Maas Transport", "FTL"),
    ("CAR-07", "EuroSprint Cargo", "LTL"), ("CAR-08", "Pacific Rim Forwarding", "Ocean/Air"),
]

CUSTOMER_WORDS_A = ["Apex", "Granite", "Prairie", "Summit", "Ironwood", "Harbor", "Cobalt", "Redline", "Evergreen", "Titan",
                    "Northstar", "Bluewater", "Frontier", "Highland", "Sterling", "Vector", "Pioneer", "Keystone", "Atlas", "Orion"]
CUSTOMER_WORDS_B = [("Agricultural Equipment", "Agriculture"), ("Construction Machinery", "Construction"), ("Truck & Bus", "Automotive"),
                    ("Mining Systems", "Mining"), ("Wind Energy", "Energy"), ("Material Handling", "Industrial"),
                    ("Marine Propulsion", "Marine"), ("Rail Systems", "Rail"), ("Forestry Machines", "Forestry"), ("Power Systems", "Energy")]

FIRST_NAMES = {
    "North America": ["James", "Maria", "Robert", "Jennifer", "Michael", "Linda", "David", "Patricia", "Carlos", "Ashley", "Daniel", "Jessica", "Marcus", "Tanya", "Kevin", "Rosa", "Brian", "Monique", "Luis", "Sarah", "Alejandro", "Guadalupe", "Diego", "Sofia"],
    "Europe":        ["Piotr", "Anna", "Tomasz", "Katarzyna", "Marek", "Agnieszka", "Krzysztof", "Magdalena", "Jan", "Ewa", "Pawel", "Monika", "Lukas", "Hanna"],
    "Asia Pacific":  ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Suresh", "Kavya", "Arjun", "Neha", "Rajesh", "Pooja", "Sanjay", "Meera"],
}
LAST_NAMES = {
    "North America": ["Johnson", "Garcia", "Williams", "Martinez", "Brown", "Lopez", "Davis", "Hernandez", "Miller", "Gonzalez", "Wilson", "Ramirez", "Taylor", "Flores", "Thompson", "Reyes", "Okafor", "Nguyen"],
    "Europe":        ["Nowak", "Kowalski", "Wisniewski", "Wojcik", "Kaminski", "Lewandowski", "Zielinski", "Szymanski", "Mazur", "Krawczyk", "Becker", "Fischer"],
    "Asia Pacific":  ["Sharma", "Patil", "Kulkarni", "Deshpande", "Joshi", "Iyer", "Reddy", "Nair", "Gupta", "Kumar", "Mehta", "Pawar"],
}

SHIFTS = {"A": 6, "B": 14, "C": 22}          # shift -> start hour (8h shifts)
PLANNED_MIN_PER_SHIFT = 450                    # 480 minutes minus a 30-minute break


@dataclass
class Table:
    """One output file set: which source system it came from + the data."""
    system: str          # erp | mes | cmms | qms | wms | iot_historian | hr
    entity: str          # folder name in the raw volume
    df: pd.DataFrame
    fmt: str             # csv | json | parquet
    description: str


# =============================================================================
# 2. GENERATOR
# =============================================================================
class MfgGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg["data"]["seed"])
        self.start = pd.Timestamp(cfg["data"]["start_date"])
        self.end = pd.Timestamp(cfg["data"]["end_date"]) + pd.Timedelta(hours=23, minutes=59)
        self.days = pd.date_range(self.start.normalize(), self.end.normalize(), freq="D")
        self.story = cfg["story"]
        self.tables: dict[str, Table] = {}
        self.events: list[dict] = []           # every downtime interval, machine- or line-level
        self.anchors: dict = {}                # facts the documents must match

    # ---------------------------------------------------------------- helpers
    def _add(self, system, entity, df, fmt, description):
        self.tables[entity] = Table(system, entity, df.reset_index(drop=True), fmt, description)

    def _name(self, region: str) -> str:
        return f"{self.rng.choice(FIRST_NAMES[region])} {self.rng.choice(LAST_NAMES[region])}"

    @staticmethod
    def _scheduled_shifts(day: pd.Timestamp) -> list[str]:
        """Production calendar: 3 shifts Mon-Fri, 2 on Saturday, Sunday dark."""
        wd = day.weekday()
        return ["A", "B", "C"] if wd < 5 else (["A", "B"] if wd == 5 else [])

    def _frac_after(self, day, start) -> float:
        """0 before `start`, ramping to 1 at the end of the window (story intensity)."""
        start = pd.Timestamp(start)
        if day < start:
            return 0.0
        return min(1.0, (day - start).days / max(1, (self.end - start).days))

    # ------------------------------------------------------------- phase 1
    def build_master_data(self):
        """Plants, lines, work centers, warehouses, parts, suppliers, materials, BOM,
        customers, carriers, employees — the ERP/MES/HR reference data."""
        rng, comp = self.rng, self.cfg["company"]

        plants, lines, machines, parts = [], [], [], []
        for p in comp["plants"]:
            plants.append(dict(plant_id=p["plant_id"], plant_name=p["name"], city=p["city"], state_country=p["state_country"],
                               region=p["region"], latitude=p["lat"], longitude=p["lon"], product_family=p["product_family"],
                               pm_compliance_target=p["pm_compliance_target"]))
            prod = PLANT_PRODUCTS[p["plant_id"]]
            for li, ln in enumerate(p["lines"]):
                flow = ln["process_flow"]
                cycle = prod["cycle_s"] * float(rng.uniform(0.85, 1.15))
                lines.append(dict(line_id=ln["line_id"], plant_id=p["plant_id"], line_name=ln["name"], line_sequence=li + 1,
                                  work_center_count=len(flow), ideal_cycle_time_s=round(cycle, 2),
                                  shifts_per_weekday=3, commissioned_year=int(rng.integers(2006, 2021))))
                for si, mtype in enumerate(flow):
                    mt = MACHINE_TYPES[mtype]
                    mid = f"{ln['line_id']}-WC{si + 1:02d}"
                    # Hidden health profile drives breakdown rate and sensor drift.
                    health = rng.choice(["healthy", "wear", "poor"], p=[0.62, 0.26, 0.12])
                    if p["plant_id"] == "CLB":
                        health = rng.choice(["healthy", "wear"], p=[0.85, 0.15])
                    oem = str(rng.choice(mt["oems"]))
                    if mid == self.story["failing_machine"]["machine_id"]:
                        health, oem = "failing", self.story["failing_machine"]["oem"]
                    machines.append(dict(
                        machine_id=mid, line_id=ln["line_id"], plant_id=p["plant_id"], process_step=si + 1,
                        machine_type=mtype, machine_name=f"{mt['name']} #{si + 1}", oem=oem,
                        model=f"{oem.split()[0][:3].upper()}-{int(rng.integers(100, 990))}",
                        serial_number=f"SN{int(rng.integers(10_000_000, 99_999_999))}",
                        install_date=(pd.Timestamp(f"{int(rng.integers(2008, 2023))}-01-01") + pd.Timedelta(days=int(rng.integers(0, 360)))).date(),
                        criticality="A" if si == int(np.argmax([MACHINE_TYPES[t]["kw"] for t in flow])) else str(rng.choice(["B", "C"], p=[0.6, 0.4])),
                        pm_interval_days=mt["pm"], _health=health))
                for k, pname in enumerate(prod["names"][li]):
                    lo, hi = prod["cost"]
                    cost = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
                    parts.append(dict(part_number=f"{prod['prefix']}-{li + 1}{k + 1}{int(rng.integers(10, 99))}", part_name=pname,
                                      product_family=p["product_family"], plant_id=p["plant_id"], line_id=ln["line_id"],
                                      unit_of_measure="EA", standard_cost_usd=round(cost, 4 if cost < 5 else 2),
                                      list_price_usd=round(cost * float(rng.uniform(1.35, 1.8)), 4 if cost < 5 else 2),
                                      weight_kg=round(float(rng.uniform(0.01, 0.2) if prod["prefix"] == "FST" else rng.uniform(0.2, 60)), 3),
                                      lifecycle_status=str(rng.choice(["Active", "Active", "Active", "Active", "Phase-Out"]))))

        self.plants, self.lines = pd.DataFrame(plants), pd.DataFrame(lines)
        self.machines, self.parts = pd.DataFrame(machines), pd.DataFrame(parts)
        self.region_of = dict(zip(self.plants.plant_id, self.plants.region))

        # Warehouses: one per plant + the configured distribution centers.
        wh = [dict(warehouse_id=f"WH-{p['plant_id']}", warehouse_name=f"{p['city']} Plant Warehouse", warehouse_type="Plant",
                   plant_id=p["plant_id"], city=p["city"], state_country=p["state_country"], region=p["region"],
                   latitude=p["lat"], longitude=p["lon"], capacity_pallets=int(rng.integers(3000, 8000))) for p in comp["plants"]]
        wh += [dict(warehouse_id=d["warehouse_id"], warehouse_name=d["name"], warehouse_type="Distribution Center", plant_id=None,
                    city=d["city"], state_country=d["state_country"], region=d["region"], latitude=d["lat"], longitude=d["lon"],
                    capacity_pallets=int(rng.integers(12000, 30000))) for d in comp["distribution_centers"]]
        self.warehouses = pd.DataFrame(wh)

        # Suppliers + the materials they supply.
        sup, mats = [], []
        story_sup = self.story["problem_supplier"]
        for i, (nm, city, country, cat) in enumerate(SUPPLIER_NAMES):
            sid = story_sup["supplier_id"] if nm == story_sup["name"] else f"SUP-{1001 + i + (1 if 1001 + i >= int(story_sup['supplier_id'][4:]) else 0)}"
            sup.append(dict(supplier_id=sid, supplier_name=nm, city=city, country=country, category=cat,
                            payment_terms=str(rng.choice(["Net 30", "Net 45", "Net 60"])),
                            quality_agreement_ppm_limit=story_sup["contract_ppm_limit"] if nm == story_sup["name"] else int(rng.choice([250, 500, 750, 1000])),
                            on_time_target=0.95, approved_since=int(rng.integers(2009, 2023)),
                            _on_time_base=float(rng.uniform(0.86, 0.97)), _ppm_base=float(rng.uniform(80, 420))))
        self.suppliers = pd.DataFrame(sup)
        mid_counter = 5001
        for cat, (names, uom, (lo, hi), lead, plants_using) in SUPPLIER_CATEGORIES.items():
            cat_sups = self.suppliers[self.suppliers.category == cat].supplier_id.tolist()
            for nm in names:
                # Brightline is the primary source for most castings (that's why its problems hurt).
                primary = story_sup["supplier_id"] if (cat == "Castings" and nm != "Gearbox Housing Casting") else str(rng.choice(cat_sups))
                mats.append(dict(material_id=f"MAT-{mid_counter}", material_name=nm, category=cat, unit_of_measure=uom,
                                 standard_cost_usd=round(float(rng.uniform(lo, hi)), 3), primary_supplier_id=primary,
                                 lead_time_days=int(lead + rng.integers(-4, 5)), _plants=plants_using))
                mid_counter += 1
        self.materials = pd.DataFrame(mats)

        # Bill of materials: every part consumes 2-4 materials its plant buys.
        bom = []
        for _, pr in self.parts.iterrows():
            cands = self.materials[self.materials._plants.apply(lambda ps: pr.plant_id in ps)]
            pick = cands.sample(n=min(len(cands), int(rng.integers(2, 5))), random_state=int(rng.integers(0, 1e9)))
            # castings-based families always include a casting
            if pr.plant_id in ("CLB", "MTY") and not (pick.category == "Castings").any():
                pick = pd.concat([pick, cands[cands.category == "Castings"].head(1)])
            for _, m in pick.iterrows():
                bom.append(dict(part_number=pr.part_number, material_id=m.material_id,
                                quantity_per=round(float(rng.uniform(0.2, 4)), 3) if m.unit_of_measure != "EA" else int(rng.integers(1, 5))))
        self.bom = pd.DataFrame(bom).drop_duplicates(["part_number", "material_id"])

        # Customers (served from the DC in their region).
        cust = []
        combos = [(a, b) for a in CUSTOMER_WORDS_A for b in CUSTOMER_WORDS_B]
        picks = rng.choice(len(combos), size=48, replace=False)
        for i, ci in enumerate(picks):
            a, (b, ind) = combos[ci]
            region = str(rng.choice(["North America", "Europe", "Asia Pacific"], p=[0.6, 0.3, 0.1]))
            dc = {"Europe": "DC-RTM", "Asia Pacific": "DC-RNO"}.get(region, str(rng.choice(["DC-MEM", "DC-RNO"], p=[0.65, 0.35])))
            cust.append(dict(customer_id=f"CUST-{2001 + i}", customer_name=f"{a} {b}", industry=ind, region=region,
                             serving_dc=dc, tier=str(rng.choice(["Strategic", "Key", "Standard"], p=[0.15, 0.35, 0.5])),
                             otif_target=0.95))
        cust[0].update(customer_name="Apex Agricultural Equipment", industry="Agriculture", region="North America", serving_dc="DC-MEM", tier="Strategic")
        self.customers = pd.DataFrame(cust).drop_duplicates("customer_name")

        self.carriers = pd.DataFrame([dict(carrier_id=c, carrier_name=n, mode=m, sla_on_time_target=0.95) for c, n, m in CARRIERS])

        emps, eid = [], 30001
        role_mix = [("Production Operator", 0.58), ("Maintenance Technician", 0.12), ("Quality Inspector", 0.08),
                    ("Shift Supervisor", 0.06), ("Production Planner", 0.04), ("Warehouse Associate", 0.12)]
        for p in comp["plants"]:
            n = int(rng.integers(110, 150))
            roles = rng.choice([r for r, _ in role_mix], size=n, p=[w for _, w in role_mix])
            for r in roles:
                emps.append(dict(employee_id=f"E{eid}", employee_name=self._name(p["region"]), plant_id=p["plant_id"], role=r,
                                 shift=str(rng.choice(["A", "B", "C"])),
                                 certification_level=str(rng.choice(["Level 1", "Level 2", "Level 3", "Master"], p=[0.3, 0.4, 0.22, 0.08])),
                                 hire_date=(pd.Timestamp("2008-01-01") + pd.Timedelta(days=int(rng.integers(0, 6200)))).date()))
                eid += 1
        self.employees = pd.DataFrame(emps)
        self.staff = {(pl, role): grp.employee_id.tolist() for (pl, role), grp in self.employees.groupby(["plant_id", "role"])}

    # ------------------------------------------------------------- phase 2
    def build_purchasing(self):
        """Purchase orders + goods receipts (with incoming inspection). The problem
        supplier gets later and dirtier after `issue_start`."""
        rng, s = self.rng, self.story["problem_supplier"]
        issue_start = pd.Timestamp(s["issue_start"])
        sup = self.suppliers.set_index("supplier_id")
        pos, rcpts, po_n = [], [], 700001
        for _, m in self.materials.iterrows():
            for plant in m._plants:
                cadence = int(rng.integers(10, 18))
                d = self.start + pd.Timedelta(days=int(rng.integers(0, cadence)))
                while d <= self.end - pd.Timedelta(days=m.lead_time_days):
                    sp = sup.loc[m.primary_supplier_id]
                    on_time_p, ppm = sp._on_time_base, sp._ppm_base
                    late_lo, late_hi = 1, 6
                    promised = d + pd.Timedelta(days=int(m.lead_time_days))
                    if m.primary_supplier_id == s["supplier_id"] and promised >= issue_start:
                        k = 0.5 + 0.5 * self._frac_after(promised, issue_start)
                        on_time_p, ppm, late_lo, late_hi = 0.52 - 0.12 * k, 1800 + 1400 * k, 4, 15
                    late = 0 if rng.random() < on_time_p else int(rng.integers(late_lo, late_hi))
                    received = promised + pd.Timedelta(days=late - int(rng.integers(0, 3)) if late == 0 else late)
                    qty = int(rng.integers(400, 2500)) if m.unit_of_measure == "EA" else int(rng.integers(2000, 15000))
                    price = round(m.standard_cost_usd * (1 + 0.0002 * (d - self.start).days) * float(rng.uniform(0.97, 1.04)), 3)
                    po_id = f"PO-{po_n}"
                    pos.append(dict(po_number=po_id, po_line=1, supplier_id=m.primary_supplier_id, material_id=m.material_id,
                                    ship_to_plant_id=plant, order_date=d.date(), promised_date=promised.date(), order_qty=qty,
                                    unit_price_usd=price, currency="USD", buyer_id=str(rng.choice(self.staff[(plant, "Production Planner")])),
                                    po_status="Closed" if received <= self.end else "Open"))
                    if received <= self.end:
                        insp = min(qty, 200 if m.unit_of_measure == "EA" else 500)
                        rejected = int(rng.binomial(qty, min(0.5, ppm / 1e6)))
                        rcpts.append(dict(receipt_id=f"GR-{po_n}", po_number=po_id, receipt_date=received.date(), received_qty=int(qty * (1 if rng.random() > 0.04 else rng.uniform(0.85, 0.98))),
                                          inspected_qty=insp, rejected_qty=rejected, days_late=max(0, (received - promised).days),
                                          inspection_result="REJECT" if rejected > 0 and m.primary_supplier_id == s["supplier_id"] else ("ACCEPT" if rejected == 0 else "ACCEPT WITH DEVIATION"),
                                          _plant=plant, _supplier=m.primary_supplier_id, _material=m.material_id, _cat=m.category,
                                          _promised=promised, _received=received, _uc=m.standard_cost_usd))
                    d += pd.Timedelta(days=cadence)
                    po_n += 1
        self.pos, self.receipts = pd.DataFrame(pos), pd.DataFrame(rcpts)

        # Material shortages: a critical late receipt starves the lines that consume it.
        mat_lines = (self.bom.merge(self.parts[["part_number", "line_id", "plant_id"]], on="part_number")
                     .groupby(["material_id", "plant_id"]).line_id.apply(lambda s: sorted(set(s))).to_dict())
        for _, r in self.receipts[self.receipts.days_late >= 4].iterrows():
            cands = mat_lines.get((r._material, r._plant), [])
            if not cands or (r._cat not in ("Castings", "Bearings", "Electronic Components", "Steel Bar & Coil", "Fastener Wire") and rng.random() > 0.3):
                continue
            line = str(rng.choice(cands))
            day = r._promised + pd.Timedelta(days=1)
            while day < r._received and day <= self.end:
                if self._scheduled_shifts(day) and rng.random() < 0.45:
                    st = day.normalize() + pd.Timedelta(hours=int(rng.integers(6, 20)))
                    self.events.append(dict(level="line", line_id=line, machine_id=None, start=st,
                                            end=st + pd.Timedelta(minutes=int(rng.integers(90, 420))), reason="Material Shortage",
                                            detail=f"Awaiting {self.materials.set_index('material_id').loc[r._material, 'material_name']} ({r._material})",
                                            po=r.po_number, wo=None, ncr=None))
                day += pd.Timedelta(days=1)

    # ------------------------------------------------------------- phase 3
    def build_maintenance(self):
        """Day-by-day reliability simulation per machine: PMs (completed or deferred
        by plant compliance), breakdown hazard that rises with health profile and
        overdue PMs, and the corrective / emergency work orders that follow."""
        rng, fm = self.rng, self.story["failing_machine"]
        deg_start = pd.Timestamp(fm["degradation_start"])
        comp = dict(zip(self.plants.plant_id, self.plants.pm_compliance_target))
        base_rate = {"healthy": 1 / 160, "wear": 1 / 75, "poor": 1 / 38, "failing": 1 / 70}
        wos, wo_n = [], 900001
        self.breakdowns = []
        for _, m in self.machines.iterrows():
            mt = MACHINE_TYPES[m.machine_type]
            techs = self.staff[(m.plant_id, "Maintenance Technician")]
            compliance = comp[m.plant_id] - (0.14 if m.line_id == fm["machine_id"][:6] else 0)
            next_pm = self.start + pd.Timedelta(days=int(rng.integers(0, m.pm_interval_days)))
            last_pm = next_pm - pd.Timedelta(days=m.pm_interval_days)
            for day in self.days:
                shifts = self._scheduled_shifts(day)
                # --- preventive maintenance due today?
                if day >= next_pm:
                    done = rng.random() < compliance
                    due = next_pm
                    if done:
                        st = day.normalize() + pd.Timedelta(hours=int(rng.choice([6, 7, 14, 22])))
                        dur = float(rng.uniform(1.0, 3.5))
                        last_pm = day
                        self.events.append(dict(level="machine", line_id=m.line_id, machine_id=m.machine_id, start=st,
                                                end=st + pd.Timedelta(hours=dur), reason="Planned Maintenance",
                                                detail=f"{m.pm_interval_days}-day PM", po=None, wo=f"WO-{wo_n}", ncr=None))
                        wos.append(self._wo(wo_n, m, "Preventive", "Medium", f"{m.pm_interval_days}-day preventive maintenance", None,
                                            st, st, st + pd.Timedelta(hours=dur), "Completed", rng.choice(techs), dur * float(rng.uniform(1, 1.6)),
                                            float(rng.uniform(40, 600)), 0.0, due))
                        next_pm = due + pd.Timedelta(days=m.pm_interval_days)
                    else:
                        wos.append(self._wo(wo_n, m, "Preventive", "Medium", f"{m.pm_interval_days}-day preventive maintenance", None,
                                            day, None, None, str(rng.choice(["Deferred", "DEFERRED", "deferred"])), None, 0, 0, 0, due))
                        next_pm = due + pd.Timedelta(days=int(rng.integers(7, 15)))   # rescheduled, clock keeps running
                    wo_n += 1
                if not shifts:
                    continue
                # --- breakdown hazard for today
                overdue = max(0, (day - last_pm).days - m.pm_interval_days)
                lam = base_rate[m._health] * min(3.5, 1 + 0.045 * overdue)
                if m._health == "failing" and day >= deg_start:
                    lam = 1 / 55 + (self._frac_after(day, deg_start) ** 1.4) / 3.2
                if rng.random() < lam:
                    sh = str(rng.choice(shifts))
                    st = day.normalize() + pd.Timedelta(hours=SHIFTS[sh] + float(rng.uniform(0, 7.5)))
                    if m._health == "failing" and day >= deg_start:
                        mode = "spindle bearing wear" if rng.random() < 0.8 else str(rng.choice(mt["modes"]))
                        hours = float(rng.uniform(4, 15))
                    else:
                        mode = str(rng.choice(mt["modes"]))
                        hours = float(np.clip(rng.lognormal(np.log(2.2), 0.6), 0.5, 18))
                    end = st + pd.Timedelta(hours=hours)
                    emergency = hours > 6 or m.criticality == "A" and rng.random() < 0.5
                    contractor = float(rng.uniform(4800, 12500)) if (m._health == "failing" and day >= deg_start and rng.random() < 0.6) else (
                        float(rng.uniform(800, 4000)) if emergency and rng.random() < 0.3 else 0.0)
                    self.breakdowns.append(dict(machine_id=m.machine_id, start=st, end=end, mode=mode))
                    self.events.append(dict(level="machine", line_id=m.line_id, machine_id=m.machine_id, start=st, end=end,
                                            reason="Equipment Failure", detail=mode, po=None, wo=f"WO-{wo_n}", ncr=None))
                    wos.append(self._wo(wo_n, m, "Emergency" if emergency else "Corrective", "Critical" if emergency else "High",
                                        f"Breakdown - {mode}", mode, st, st + pd.Timedelta(minutes=int(rng.integers(10, 60))), end,
                                        str(rng.choice(["Completed", "Completed", "COMPLETED", "completed "])), rng.choice(techs),
                                        hours * float(rng.uniform(1.1, 2.2)), float(rng.uniform(150, 6500 if emergency else 2200)), contractor, None))
                    wo_n += 1
        self.work_orders = pd.DataFrame(wos)

    def _wo(self, n, m, wtype, prio, desc, mode, created, started, completed, status, tech, labor, parts, contractor, due):
        return dict(work_order_id=f"WO-{n}", machine_id=m.machine_id, line_id=m.line_id, plant_id=m.plant_id,
                    work_order_type=wtype, priority=prio, failure_mode=mode, description=desc,
                    pm_due_date=None if due is None else pd.Timestamp(due).date(),
                    created_ts=pd.Timestamp(created).strftime("%Y-%m-%d %H:%M:%S"),
                    started_ts=None if started is None else pd.Timestamp(started).strftime("%Y-%m-%d %H:%M:%S"),
                    completed_ts=None if completed is None else pd.Timestamp(completed).strftime("%Y-%m-%d %H:%M:%S"),
                    status=status, technician_id=tech, labor_hours=round(labor, 2), parts_cost_usd=round(parts, 2),
                    contractor_cost_usd=round(contractor, 2))

    # ------------------------------------------------------------- phase 4
    def build_line_schedule(self):
        """Production orders per line (each 2-6 days), with a changeover at the start
        of every order, plus occasional 'no operator' gaps (worse on Greenville C shift)."""
        rng = self.rng
        pos, n = [], 400001
        parts_by_line = self.parts.groupby("line_id").part_number.apply(list).to_dict()
        for _, ln in self.lines.iterrows():
            d = self.start
            while d <= self.end:
                dur = int(rng.integers(2, 7))
                part = str(rng.choice(parts_by_line[ln.line_id]))
                pos.append(dict(production_order_id=f"MO-{n}", line_id=ln.line_id, plant_id=ln.plant_id, part_number=part,
                                scheduled_start=d.date(), scheduled_end=min(d + pd.Timedelta(days=dur - 1), self.end).date()))
                co = d.normalize() + pd.Timedelta(hours=6)
                self.events.append(dict(level="line", line_id=ln.line_id, machine_id=None, start=co,
                                        end=co + pd.Timedelta(minutes=int(rng.integers(30, 110))), reason="Changeover",
                                        detail=f"Changeover to {part}", po=None, wo=None, ncr=None))
                d += pd.Timedelta(days=dur)
                n += 1
            for day in self.days:
                shifts = self._scheduled_shifts(day)
                p = 0.03 if ln.plant_id == "GVL" else 0.012
                if shifts and rng.random() < p:
                    sh = "C" if (ln.plant_id == "GVL" and "C" in shifts and rng.random() < 0.7) else str(rng.choice(shifts))
                    st = day.normalize() + pd.Timedelta(hours=SHIFTS[sh])
                    self.events.append(dict(level="line", line_id=ln.line_id, machine_id=None, start=st,
                                            end=st + pd.Timedelta(minutes=int(rng.integers(45, 240))), reason="No Operator",
                                            detail="Unfilled operator position", po=None, wo=None, ncr=None))
        self.prod_orders = pd.DataFrame(pos)

    # ------------------------------------------------------------- phase 5
    def _defect_rate(self, line_id: str, plant_id: str, shift: str, day: pd.Timestamp) -> tuple[float, str | None]:
        """Defect probability for one line-shift, plus the dominant story defect (if any)."""
        base = {"CLB": 0.0045, "GVL": 0.008, "MTY": 0.009, "WRO": 0.006, "PNQ": 0.004}[plant_id]
        fm, sup, q = self.story["failing_machine"], self.story["problem_supplier"], self.story["quality_shift_issue"]
        if line_id == fm["machine_id"][:6] and day >= pd.Timestamp(fm["degradation_start"]):
            return base + 0.03 * self._frac_after(day, fm["degradation_start"]) + 0.004, "Bore out of tolerance"
        if line_id in ("MTY-L1", "MTY-L2", "CLB-L1") and day >= pd.Timestamp(sup["issue_start"]):
            return base + 0.022 + 0.015 * self._frac_after(day, sup["issue_start"]), "Porosity"
        if line_id == q["machine_id"][:6] and shift == q["shift"] and day >= pd.Timestamp(q["start"]):
            return base + 0.055, "Crimp height out of spec"
        return base, None

    def build_production_and_quality(self):
        """Shift-level production results (OEE inputs), in-process inspections,
        nonconformance reports (NCRs), quality holds, and CAPAs."""
        rng = self.rng
        lines = self.lines.set_index("line_id")
        first_mc = self.machines[self.machines.process_step == 1].set_index("line_id").machine_id.to_dict()
        line_type = self.machines[self.machines.process_step == 1].set_index("line_id").machine_type.to_dict()
        machines_by_line = self.machines.groupby("line_id").machine_id.apply(list).to_dict()
        inspectors = {p: self.staff[(p, "Quality Inspector")] for p in self.plants.plant_id}
        po_df = self.prod_orders.copy()
        po_df["s"], po_df["e"] = pd.to_datetime(po_df.scheduled_start), pd.to_datetime(po_df.scheduled_end)

        insp, ncrs, ncr_n, insp_n = [], [], 600001, 800001
        fm = self.story["failing_machine"]
        for _, ln in self.lines.iterrows():
            lpo = po_df[po_df.line_id == ln.line_id]
            char = LINE_CHARACTERISTIC.get(line_type[ln.line_id], ("Critical dimension", "mm", 10.0, 0.05))
            for day in self.days:
                for sh in self._scheduled_shifts(day):
                    rate, story_defect = self._defect_rate(ln.line_id, ln.plant_id, sh, day)
                    order = lpo[(lpo.s <= day) & (lpo.e >= day)]
                    part = order.part_number.iloc[0] if len(order) else None
                    n_sample = 125 if ln.plant_id == "PNQ" else 50
                    defects = int(rng.binomial(n_sample, min(0.5, rate * 2.2)))
                    code = story_defect if (story_defect and rng.random() < 0.75) else str(rng.choice(DEFECT_CODES[ln.plant_id]))
                    nom, tol = char[2], char[3]
                    shift_off = (0.55 if story_defect else 0.05) * tol * float(rng.normal(1, 0.25))
                    sd = tol / (2.2 if story_defect else 4.2) * float(rng.uniform(0.9, 1.1))
                    ts = day.normalize() + pd.Timedelta(hours=SHIFTS[sh] + float(rng.uniform(1, 6)))
                    result = "FAIL" if defects > 2 else "PASS"
                    insp.append(dict(inspection_id=f"INSP-{insp_n}", inspection_type="In-Process", inspection_ts=ts.strftime("%Y-%m-%d %H:%M:%S"),
                                     plant_id=ln.plant_id, line_id=ln.line_id, shift=sh, production_order_part=part,
                                     inspector_id=str(rng.choice(inspectors[ln.plant_id])), sample_size=n_sample, defects_found=defects,
                                     primary_defect_code=code if defects else None, characteristic=char[0], characteristic_uom=char[1],
                                     nominal=nom, lower_spec_limit=round(nom - tol, 4), upper_spec_limit=round(nom + tol, 4),
                                     measured_mean=round(nom + shift_off, 4), measured_std_dev=round(sd, 5), result=result))
                    insp_n += 1
                    if result == "FAIL" and rng.random() < (0.35 if story_defect else 0.4):
                        severity = "Major" if (story_defect or rng.random() < 0.3) else "Minor"
                        qty = int(rng.integers(6, 80) * (40 if ln.plant_id == "PNQ" else 1))
                        part_cost = float(self.parts.set_index("part_number").standard_cost_usd.get(part, 50.0)) if part else 50.0
                        disp = str(rng.choice(["Scrap", "Rework", "Use As Is", "Sort & Rework"], p=[0.45, 0.35, 0.05, 0.15]))
                        ncrs.append(dict(ncr_id=f"NCR-{ncr_n}", opened_date=day.date(), source="In-Process", plant_id=ln.plant_id,
                                         line_id=ln.line_id, machine_id=(fm["machine_id"] if code == "Bore out of tolerance" and ln.line_id == fm["machine_id"][:6] else
                                                                         self.story["quality_shift_issue"]["machine_id"] if code == "Crimp height out of spec" and story_defect else None),
                                         part_number=part, material_id=None, supplier_id=None, defect_code=code, severity=severity,
                                         qty_affected=qty, disposition=disp,
                                         cost_of_poor_quality_usd=round(qty * part_cost * (1.0 if disp == "Scrap" else 0.35) + 180, 2),
                                         inspection_id=f"INSP-{insp_n - 1}", _story=story_defect))
                        if severity == "Major" and rng.random() < 0.55:
                            st = ts + pd.Timedelta(minutes=10)
                            self.events.append(dict(level="line", line_id=ln.line_id, machine_id=None, start=st,
                                                    end=st + pd.Timedelta(minutes=int(rng.integers(90, 360))), reason="Quality Hold",
                                                    detail=f"Containment for {code}", po=None, wo=None, ncr=f"NCR-{ncr_n}"))
                        ncr_n += 1

        # Incoming-inspection NCRs from supplier rejects.
        for _, r in self.receipts[self.receipts.rejected_qty > 0].iterrows():
            if r._supplier == self.story["problem_supplier"]["supplier_id"] or rng.random() < 0.35:
                ncrs.append(dict(ncr_id=f"NCR-{ncr_n}", opened_date=r.receipt_date, source="Incoming Inspection", plant_id=r._plant,
                                 line_id=None, machine_id=None, part_number=None, material_id=r._material, supplier_id=r._supplier,
                                 defect_code="Porosity" if r._cat == "Castings" else str(rng.choice(["Dimensional", "Documentation", "Damage in transit", "Wrong material"])),
                                 severity="Major" if r._supplier == self.story["problem_supplier"]["supplier_id"] else str(rng.choice(["Major", "Minor"], p=[0.3, 0.7])),
                                 qty_affected=int(r.rejected_qty), disposition="Return to Vendor",
                                 cost_of_poor_quality_usd=round(r.rejected_qty * r._uc + 250, 2), inspection_id=None, _story=None))
                ncr_n += 1
        self.inspections, self.ncrs = pd.DataFrame(insp), pd.DataFrame(ncrs)
        self.ncrs["opened_date"] = pd.to_datetime(self.ncrs.opened_date)

        # CAPAs: one per storyline + a batch of routine ones; NCRs link to them.
        capas, cn = [], 101
        def capa(title, rc, plant, opened, due, status, owner_role, ncr_mask, closed=None, verified=None, supplier=None):
            nonlocal cn
            cid = f"CAPA-2026-{cn:03d}"
            capas.append(dict(capa_id=cid, title=title, root_cause_category=rc, plant_id=plant, supplier_id=supplier,
                              opened_date=pd.Timestamp(opened).date(), due_date=pd.Timestamp(due).date(),
                              closed_date=None if closed is None else pd.Timestamp(closed).date(), status=status,
                              owner_id=str(rng.choice(self.staff[(plant, owner_role)])), effectiveness_verified=verified))
            self.ncrs.loc[ncr_mask & self.ncrs.get("capa_id", pd.Series(index=self.ncrs.index, dtype=object)).isna(), "capa_id"] = cid
            cn += 1
        self.ncrs["capa_id"] = None
        sup, q = self.story["problem_supplier"], self.story["quality_shift_issue"]
        capa(f"SCAR: casting porosity from {sup['name']}", "Supplier", "MTY", pd.Timestamp(sup["issue_start"]) + pd.Timedelta(days=24),
             pd.Timestamp(sup["issue_start"]) + pd.Timedelta(days=84), "Overdue", "Shift Supervisor",
             (self.ncrs.defect_code == "Porosity") & (self.ncrs.opened_date >= pd.Timestamp(sup["issue_start"])), supplier=sup["supplier_id"])
        capa(f"Crimp height variation on {q['machine_id']} night shift", "Method / Work Instruction", "WRO",
             pd.Timestamp(q["start"]) + pd.Timedelta(days=30), pd.Timestamp(q["start"]) + pd.Timedelta(days=75), "In Progress", "Quality Inspector",
             (self.ncrs.defect_code == "Crimp height out of spec") & (self.ncrs.opened_date >= pd.Timestamp(q["start"])))
        capa(f"Bore position drift on {fm['machine_id']} (spindle condition)", "Machine", "GVL",
             pd.Timestamp(fm["degradation_start"]) + pd.Timedelta(days=70), pd.Timestamp(fm["degradation_start"]) + pd.Timedelta(days=130), "Open", "Shift Supervisor",
             (self.ncrs.defect_code == "Bore out of tolerance") & (self.ncrs.line_id == fm["machine_id"][:6]))
        routine = self.ncrs[self.ncrs.capa_id.isna() & (self.ncrs.severity == "Major")].sample(frac=0.25, random_state=7)
        for _, r in routine.head(30).iterrows():
            opened = r.opened_date + pd.Timedelta(days=int(rng.integers(2, 10)))
            due = opened + pd.Timedelta(days=int(rng.integers(30, 60)))
            closed = due - pd.Timedelta(days=int(rng.integers(-15, 20)))
            status = "Closed" if closed <= self.end else ("Overdue" if due < self.end else "In Progress")
            capa(f"{r.defect_code} - {r.line_id if isinstance(r.line_id, str) else r.supplier_id}", str(rng.choice(["Machine", "Method / Work Instruction", "Material", "Operator Training", "Measurement"])),
                 r.plant_id, opened, due, status, "Quality Inspector", self.ncrs.ncr_id == r.ncr_id,
                 closed=closed if status == "Closed" else None, verified=bool(rng.random() < 0.8) if status == "Closed" else None)
        self.capas = pd.DataFrame(capas)
        self.ncrs["status"] = np.where(self.ncrs.capa_id.notna() & self.ncrs.capa_id.isin(self.capas[self.capas.status != "Closed"].capa_id), "Open - CAPA Pending",
                                       np.where(self.ncrs.opened_date > self.end - pd.Timedelta(days=10), "Open", "Closed"))
        self.ncrs["opened_date"] = self.ncrs.opened_date.dt.date

        # ---- Shift production results from the merged downtime intervals
        ev = pd.DataFrame(self.events)
        shift_rows = []
        for line_id, ln in lines.iterrows():
            le = ev[ev.line_id == line_id].sort_values("start")
            # merge overlapping intervals so availability is not double-counted
            merged = []
            for s, e in zip(le.start, le.end):
                if merged and s <= merged[-1][1]:
                    merged[-1][1] = max(merged[-1][1], e)
                else:
                    merged.append([s, e])
            reason_min = {}
            for _, r in le.iterrows():
                for sh_day in pd.date_range((r.start - pd.Timedelta(hours=8)).normalize(), r.end.normalize(), freq="D"):
                    for sh, h in SHIFTS.items():
                        ss = sh_day + pd.Timedelta(hours=h); se = ss + pd.Timedelta(hours=8)
                        ov = (min(se, r.end) - max(ss, r.start)).total_seconds() / 60
                        if ov > 0:
                            reason_min[(sh_day, sh, r.reason)] = reason_min.get((sh_day, sh, r.reason), 0) + ov
            down = {}
            for s, e in merged:
                for sh_day in pd.date_range((s - pd.Timedelta(hours=8)).normalize(), e.normalize(), freq="D"):
                    for sh, h in SHIFTS.items():
                        ss = sh_day + pd.Timedelta(hours=h); se = ss + pd.Timedelta(hours=8)
                        ov = (min(se, e) - max(ss, s)).total_seconds() / 60
                        if ov > 0:
                            down[(sh_day, sh)] = down.get((sh_day, sh), 0) + ov
            lpo = po_df[po_df.line_id == line_id]
            sup_story = self.story["problem_supplier"]
            for day in self.days:
                for sh in self._scheduled_shifts(day):
                    dmin = min(PLANNED_MIN_PER_SHIFT, down.get((day, sh), 0.0))
                    run = PLANNED_MIN_PER_SHIFT - dmin
                    perf = float(np.clip(rng.normal(0.87, 0.04), 0.6, 0.98))
                    if line_id == fm["machine_id"][:6]:
                        perf -= 0.10 * self._frac_after(day, fm["degradation_start"])   # spindle runs de-rated
                    if line_id in ("MTY-L1", "MTY-L2") and day >= pd.Timestamp(sup_story["issue_start"]):
                        perf -= 0.03
                    total = int(run * 60 / ln.ideal_cycle_time_s * perf)
                    rate, _ = self._defect_rate(line_id, ln.plant_id, sh, day)
                    scrap = int(rng.binomial(total, min(0.5, rate))) if total else 0
                    rework = int(rng.binomial(total, min(0.5, rate * 0.35))) if total else 0
                    order = lpo[(lpo.s <= day) & (lpo.e >= day)]
                    shift_rows.append(dict(
                        shift_result_id=f"SR-{line_id}-{day:%Y%m%d}-{sh}", production_date=day.date(), shift=sh,
                        plant_id=ln.plant_id, line_id=line_id,
                        production_order_id=order.production_order_id.iloc[0] if len(order) else None,
                        part_number=order.part_number.iloc[0] if len(order) else None,
                        planned_minutes=PLANNED_MIN_PER_SHIFT, downtime_minutes=round(dmin, 1), run_minutes=round(run, 1),
                        ideal_cycle_time_s=ln.ideal_cycle_time_s, total_units=total, scrap_units=scrap, rework_units=rework,
                        good_units=max(0, total - scrap - rework),
                        dt_equipment_failure_min=round(reason_min.get((day, sh, "Equipment Failure"), 0), 1),
                        dt_planned_maintenance_min=round(reason_min.get((day, sh, "Planned Maintenance"), 0), 1),
                        dt_changeover_min=round(reason_min.get((day, sh, "Changeover"), 0), 1),
                        dt_material_shortage_min=round(reason_min.get((day, sh, "Material Shortage"), 0), 1),
                        dt_quality_hold_min=round(reason_min.get((day, sh, "Quality Hold"), 0), 1),
                        dt_no_operator_min=round(reason_min.get((day, sh, "No Operator"), 0), 1),
                        supervisor_id=str(rng.choice(self.staff[(ln.plant_id, "Shift Supervisor")]))))
        self.shift_results = pd.DataFrame(shift_rows)
        # roll production orders up with what was actually produced
        made = self.shift_results.groupby("production_order_id").agg(completed_qty=("good_units", "sum"), scrap_qty=("scrap_units", "sum")).reset_index()
        self.prod_orders = self.prod_orders.merge(made, on="production_order_id", how="left").fillna({"completed_qty": 0, "scrap_qty": 0})
        self.prod_orders["planned_qty"] = (self.prod_orders.completed_qty * rng.uniform(1.02, 1.18, len(self.prod_orders))).round().astype(int)
        self.prod_orders["order_status"] = np.where(pd.to_datetime(self.prod_orders.scheduled_end) < self.end.normalize(), "Closed", "Released")

        # downtime events table (what the MES logged)
        ops = {p: self.staff[(p, "Production Operator")] for p in self.plants.plant_id}
        plant_of_line = dict(zip(self.lines.line_id, self.lines.plant_id))
        ev = ev.sort_values("start").reset_index(drop=True)
        ev["downtime_event_id"] = [f"DT-{1000001 + i}" for i in range(len(ev))]
        ev["plant_id"] = ev.line_id.map(plant_of_line)
        ev["shift"] = ev.start.dt.hour.map(lambda h: "A" if 6 <= h < 14 else ("B" if 14 <= h < 22 else "C"))
        ev["reported_by"] = [str(rng.choice(ops[p])) for p in ev.plant_id]
        ev["duration_minutes"] = ((ev.end - ev.start).dt.total_seconds() / 60).round(1)
        self.downtime = ev.rename(columns=dict(start="start_ts", end="end_ts", reason="reason_category", detail="reason_detail",
                                               po="related_po_number", wo="related_work_order_id", ncr="related_ncr_id"))
        self.downtime["machine_id"] = self.downtime.machine_id.fillna(self.downtime.line_id.map(first_mc))
        self.downtime["event_scope"] = self.downtime.pop("level").map({"machine": "Machine", "line": "Line"})
        for c in ("start_ts", "end_ts"):
            self.downtime[c] = self.downtime[c].dt.strftime("%Y-%m-%dT%H:%M:%S")
        self._machines_by_line = machines_by_line

    # ------------------------------------------------------------- phase 6
    def build_telemetry(self):
        """IoT historian: one reading per machine per interval. Status comes from the
        production calendar + downtime events; vibration/temperature carry the health
        drift and a 36h precursor before every breakdown (what PdM looks for)."""
        rng = self.rng
        step = int(self.cfg["data"]["telemetry_interval_minutes"])
        ts = pd.date_range(self.start, self.end, freq=f"{step}min")
        n = len(ts)
        hour, wd = ts.hour.values, ts.weekday.values
        sched = np.where(wd < 5, True, np.where(wd == 5, (hour >= 6) & (hour < 22), False))
        # Compare in int64 nanoseconds regardless of pandas' internal datetime unit.
        ts_ns = np.asarray(ts.values, dtype="datetime64[ns]").astype("int64")
        def idx(t):
            return int(np.searchsorted(ts_ns, np.datetime64(pd.Timestamp(t), "ns").astype("int64")))
        line_down = {}
        for _, e in self.downtime[self.downtime.event_scope == "Line"].iterrows():
            line_down.setdefault(e.line_id, []).append((idx(e.start_ts), idx(e.end_ts)))
        mach_down = {}
        for _, e in self.downtime[self.downtime.event_scope == "Machine"].iterrows():
            mach_down.setdefault(e.machine_id, []).append((idx(e.start_ts), idx(e.end_ts)))
        bd_by_m = {}
        for b in self.breakdowns:
            bd_by_m.setdefault(b["machine_id"], []).append(idx(b["start"]))
        fm = self.story["failing_machine"]
        q = self.story["quality_shift_issue"]
        deg_i = idx(fm["degradation_start"])
        frames = []
        for _, m in self.machines.iterrows():
            mt = MACHINE_TYPES[m.machine_type]
            status = np.where(sched, "RUNNING", "IDLE").astype(object)
            for a, b in line_down.get(m.line_id, []):
                status[a:b + 1] = np.where(status[a:b + 1] == "RUNNING", "STOPPED", status[a:b + 1])
            for a, b in mach_down.get(m.machine_id, []):
                status[a:b + 1] = "DOWN"
            running = status == "RUNNING"
            drift = np.zeros(n)
            if m._health == "wear":
                drift = np.linspace(0, 0.35, n)
            elif m._health == "poor":
                drift = np.linspace(0.15, 0.7, n)
            elif m._health == "failing":
                drift = np.clip((np.arange(n) - deg_i) / max(1, n - deg_i), 0, 1) ** 1.3 * 2.1
            precursor = np.zeros(n)
            for bi in bd_by_m.get(m.machine_id, []):
                w = int(36 * 60 / step)
                lo = max(0, bi - w)
                precursor[lo:bi] += np.linspace(0, 0.9, bi - lo)
            vib = mt["vib"] * (1 + drift + precursor) * rng.lognormal(0, 0.08, n)
            temp = mt["temp"] * (1 + 0.12 * drift + 0.05 * precursor) + rng.normal(0, max(0.6, mt["temp"] * 0.015), n) + 2.5 * np.sin(2 * np.pi * hour / 24)
            load = np.clip(rng.normal(68, 7, n) + 9 * drift, 5, 100)
            kw = mt["kw"] * load / 70 * rng.lognormal(0, 0.04, n)
            cycle = np.full(n, np.nan)
            if m.machine_id == q["machine_id"]:
                temp = temp + np.where((ts >= pd.Timestamp(q["start"])) & ((hour >= 22) | (hour < 6)), 3.0, 0.0)
            # machines that aren't running read near-zero
            vib = np.where(running, vib, mt["vib"] * 0.06 * rng.random(n))
            load = np.where(running, load, 0.0)
            kw = np.where(running, kw, mt["kw"] * 0.04)
            temp = np.where(running, temp, 22 + (mt["temp"] - 22) * (0.25 if mt["temp"] > 100 else 0.05) + rng.normal(0, 0.5, n))
            frames.append(pd.DataFrame(dict(machine_id=m.machine_id, reading_ts=ts.strftime("%Y-%m-%dT%H:%M:%SZ"), machine_state=status,
                                            temperature_c=np.round(temp, 2), vibration_mm_s=np.round(vib, 3),
                                            motor_load_pct=np.round(load, 1), power_kw=np.round(kw, 2))))
        tel = pd.concat(frames, ignore_index=True)
        # realistic historian mess: ~0.4% duplicate packets, ~0.2% dropped sensor values
        dup = tel.sample(frac=0.004, random_state=11)
        tel = pd.concat([tel, dup], ignore_index=True)
        tel.loc[tel.sample(frac=0.002, random_state=12).index, "vibration_mm_s"] = np.nan
        self.telemetry = tel

    # ------------------------------------------------------------- phase 7
    def build_inventory_and_fulfillment(self):
        """Daily inventory (FG at DCs, materials at plant warehouses), customer sales
        orders, and outbound shipments. FG availability follows the producing line's
        recent output; carrier lateness follows carrier performance."""
        rng = self.rng
        # FG availability factor per part per day = trailing 14-day output vs the part's norm
        sr = self.shift_results.copy()
        sr["production_date"] = pd.to_datetime(sr.production_date)
        out = sr.groupby(["line_id", "production_date"]).good_units.sum().unstack(0).reindex(self.days).fillna(0)
        avail = (out.rolling(14, min_periods=1).mean() / out.mean().replace(0, 1)).clip(0, 1.4)
        inv = []
        for _, p in self.parts.iterrows():
            for dc in self.cfg["company"]["distribution_centers"]:
                ss = float(rng.uniform(150, 900)) * (60 if p.plant_id == "PNQ" else 1)
                f = avail[p.line_id].values
                on_hand = np.maximum(0, ss * (2.4 * f - 0.65) * rng.lognormal(0, 0.12, len(self.days)))
                alloc = ss * rng.uniform(0.15, 0.5, len(self.days))
                inv.append(pd.DataFrame(dict(snapshot_date=self.days.date, warehouse_id=dc["warehouse_id"], item_id=p.part_number,
                                             item_type="Finished Good", on_hand_qty=on_hand.round(0), allocated_qty=alloc.round(0),
                                             safety_stock_qty=round(ss), unit_cost_usd=p.standard_cost_usd)))
        shortage_windows = {}
        for _, r in self.receipts[self.receipts.days_late >= 4].iterrows():
            shortage_windows.setdefault((r._plant, r._material), []).append((r._promised, r._received))
        for _, m in self.materials.iterrows():
            for plant in m._plants:
                ss = float(rng.uniform(500, 4000))
                oh = ss * rng.uniform(1.4, 2.6, len(self.days))
                for a, b in shortage_windows.get((plant, m.material_id), []):
                    mask = (self.days >= a) & (self.days <= b)
                    oh[mask] = ss * rng.uniform(0.0, 0.35, mask.sum())
                inv.append(pd.DataFrame(dict(snapshot_date=self.days.date, warehouse_id=f"WH-{plant}", item_id=m.material_id,
                                             item_type="Raw Material", on_hand_qty=oh.round(0), allocated_qty=(ss * 0.3 * rng.random(len(self.days))).round(0),
                                             safety_stock_qty=round(ss), unit_cost_usd=m.standard_cost_usd)))
        self.inventory = pd.concat(inv, ignore_index=True)
        fg = self.inventory[self.inventory.item_type == "Finished Good"].set_index(["warehouse_id", "item_id", "snapshot_date"])
        stockout = (fg.on_hand_qty < fg.allocated_qty).to_dict()

        # Sales orders + shipments
        car = self.story["problem_carrier"]
        carriers_by_dc = {"DC-MEM": (["CAR-01", "CAR-02", "CAR-03", car["carrier_id"], "CAR-05"], [0.18, 0.12, 0.2, 0.38, 0.12]),
                          "DC-RNO": (["CAR-01", "CAR-02", "CAR-03", "CAR-05", "CAR-08"], [0.25, 0.15, 0.3, 0.15, 0.15]),
                          "DC-RTM": (["CAR-06", "CAR-07", "CAR-02"], [0.45, 0.4, 0.15])}
        carrier_ot = {"CAR-01": 0.95, "CAR-02": 0.97, "CAR-03": 0.94, car["carrier_id"]: 0.80, "CAR-05": 0.91, "CAR-06": 0.95, "CAR-07": 0.93, "CAR-08": 0.89}
        transit = {"DC-MEM": (2, 5), "DC-RNO": (2, 6), "DC-RTM": (2, 5)}
        cust = self.customers.reset_index(drop=True)
        cust_w = cust.tier.map({"Strategic": 5, "Key": 2.5, "Standard": 1}).values
        cust_w = cust_w / cust_w.sum()
        so, sh, n = [], [], 1
        lines_per_day = self.cfg["data"]["sales_order_lines_per_day"]
        for day in self.days:
            k = int(rng.poisson(lines_per_day * (0.35 if day.weekday() >= 5 else 1.0)))
            for _ in range(k):
                c = cust.iloc[int(rng.choice(len(cust), p=cust_w))]
                p = self.parts.iloc[int(rng.integers(0, len(self.parts)))]
                qty = int(rng.integers(5, 400) * (250 if p.plant_id == "PNQ" else 1))
                req = day + pd.Timedelta(days=int(rng.integers(7, 30)))
                so_id = f"SO-{500000 + n}"
                so.append(dict(sales_order_id=so_id, order_line=1, order_date=day.date(), customer_id=c.customer_id,
                               part_number=p.part_number, order_qty=qty, unit_price_usd=p.list_price_usd,
                               requested_delivery_date=req.date(), fulfillment_dc=c.serving_dc,
                               order_channel=str(rng.choice(["EDI", "Portal", "Email"], p=[0.6, 0.3, 0.1]))))
                planned_ship = req - pd.Timedelta(days=transit[c.serving_dc][1])
                backorder = stockout.get((c.serving_dc, p.part_number, planned_ship.date()), False)
                ship = max(day + pd.Timedelta(days=1), planned_ship + pd.Timedelta(days=int(rng.integers(3, 12)) if backorder else int(rng.integers(-2, 1))))
                cid = str(rng.choice(carriers_by_dc[c.serving_dc][0], p=carriers_by_dc[c.serving_dc][1]))
                ot = carrier_ot[cid] - (0.08 if (cid == car["carrier_id"] and (ship.month in (11, 12) or ship.month in (7, 8, 9))) else 0)
                t_lo, t_hi = transit[c.serving_dc]
                std_transit = int(rng.integers(t_lo, t_hi + 1))
                tdays = std_transit + (0 if rng.random() < ot else int(rng.integers(1, 5)))
                delivered = ship + pd.Timedelta(days=tdays)
                if ship <= self.end:
                    shipped_qty = qty if rng.random() > 0.035 else int(qty * rng.uniform(0.6, 0.95))
                    sh.append(dict(shipment_id=f"SHP-{300000 + n}", sales_order_id=so_id, ship_from_warehouse_id=c.serving_dc,
                                   carrier_id=cid, ship_date=ship.date(), planned_transit_days=std_transit,
                                   carrier_due_date=(ship + pd.Timedelta(days=std_transit)).date(), promised_delivery_date=req.date(),
                                   delivered_date=delivered.date() if delivered <= self.end else None, shipped_qty=shipped_qty,
                                   freight_cost_usd=round(float(rng.uniform(80, 2400)) * (1.6 if cid in ("CAR-03", "CAR-08") else 1), 2),
                                   tracking_number=f"{cid[-2:]}{int(rng.integers(10**9, 10**10 - 1))}",
                                   shipment_status="Delivered" if delivered <= self.end else "In Transit"))
                n += 1
        self.sales_orders, self.shipments = pd.DataFrame(so), pd.DataFrame(sh)
        self.shipments = pd.concat([self.shipments, self.shipments.sample(frac=0.003, random_state=21)], ignore_index=True)  # EDI resend dupes

    # ------------------------------------------------------------- phase 8
    def compute_anchors(self):
        """The exact facts the documents are written around. Saved next to the data
        so anyone regenerating documents uses the same numbers."""
        fm, sup, car, q = (self.story[k] for k in ("failing_machine", "problem_supplier", "problem_carrier", "quality_shift_issue"))
        wo = self.work_orders
        fwo = wo[(wo.machine_id == fm["machine_id"]) & wo.work_order_type.isin(["Emergency", "Corrective"])]
        fwo_after = fwo[pd.to_datetime(fwo.created_ts) >= pd.Timestamp(fm["degradation_start"])]
        tel = self.telemetry[(self.telemetry.machine_id == fm["machine_id"]) & (self.telemetry.machine_state == "RUNNING")].copy()
        tel["m"] = tel.reading_ts.str[:7]
        vib_by_month = tel.groupby("m").vibration_mm_s.mean().round(2).to_dict()
        sr = self.shift_results.copy()
        sr["m"] = pd.to_datetime(sr.production_date).dt.strftime("%Y-%m")
        def oee(df):
            a = df.run_minutes.sum() / df.planned_minutes.sum()
            perf = (df.total_units * df.ideal_cycle_time_s / 60).sum() / max(1, df.run_minutes.sum())
            qual = df.good_units.sum() / max(1, df.total_units.sum())
            return round(a * perf * qual, 3)
        line_oee = {m: oee(g) for m, g in sr[sr.line_id == fm["machine_id"][:6]].groupby("m")}
        plant_oee = {p: oee(g) for p, g in sr.groupby("plant_id")}
        rc = self.receipts
        b = rc[rc._supplier == sup["supplier_id"]]
        b_before, b_after = b[b._promised < pd.Timestamp(sup["issue_start"])], b[b._promised >= pd.Timestamp(sup["issue_start"])]
        shp = self.shipments.drop_duplicates("shipment_id")
        shp = shp[shp.delivered_date.notna()]
        shp_ot = (pd.to_datetime(shp.delivered_date) <= pd.to_datetime(shp.carrier_due_date))
        otif = ((pd.to_datetime(shp.delivered_date) <= pd.to_datetime(shp.promised_delivery_date)))
        self._otif_by_dc = otif.groupby(shp.ship_from_warehouse_id).mean().round(3).to_dict()
        car_ot = shp_ot.groupby(shp.carrier_id).mean().round(3).to_dict()
        ridge_mem = shp_ot[(shp.carrier_id == car["carrier_id"]) & (shp.ship_from_warehouse_id == car["lane_origin"])].mean()
        insp = self.inspections
        wro = insp[insp.line_id == q["machine_id"][:6]].copy()
        wro["after"] = pd.to_datetime(wro.inspection_ts) >= pd.Timestamp(q["start"])
        crimp = (wro.groupby(["after", "shift"]).apply(lambda g: g.defects_found.sum() / g.sample_size.sum()).round(4))
        plant_pm = {}
        for p, g in wo[wo.work_order_type == "Preventive"].groupby("plant_id"):
            plant_pm[p] = round((g.status.str.strip().str.lower() == "completed").mean(), 3)
        self.anchors = dict(
            company=self.cfg["company"]["name"], window=[str(self.start.date()), str(self.end.date())],
            failing_machine=dict(machine_id=fm["machine_id"], oem=fm["oem"], degradation_start=fm["degradation_start"],
                                 breakdowns_total=int(len(fwo)), breakdowns_since_degradation=int(len(fwo_after)),
                                 downtime_hours_since_degradation=round(float(((pd.to_datetime(fwo_after.completed_ts) - pd.to_datetime(fwo_after.created_ts)).dt.total_seconds() / 3600).sum()), 1),
                                 contractor_cost_usd_since_degradation=round(float(fwo_after.contractor_cost_usd.sum()), 2),
                                 total_maintenance_cost_usd_since_degradation=round(float((fwo_after.parts_cost_usd + fwo_after.contractor_cost_usd).sum()), 2),
                                 avg_running_vibration_by_month=vib_by_month, line_oee_by_month=line_oee,
                                 oem_limit_mm_s=fm["oem_vibration_limit_mm_s"], internal_limit_mm_s=fm["internal_pm_limit_mm_s"],
                                 first_month_above_oem_limit=next((k for k, v in sorted(vib_by_month.items()) if v > fm["oem_vibration_limit_mm_s"]), None)),
            pm_compliance_by_plant=plant_pm, oee_by_plant=plant_oee,
            problem_supplier=dict(supplier_id=sup["supplier_id"], name=sup["name"], issue_start=sup["issue_start"],
                                  on_time_before=round(float((b_before.days_late == 0).mean()), 3), on_time_after=round(float((b_after.days_late == 0).mean()), 3),
                                  avg_days_late_after=round(float(b_after.days_late[b_after.days_late > 0].mean()), 1),
                                  ppm_before=round(float(b_before.rejected_qty.sum() / max(1, b_before.received_qty.sum()) * 1e6), 0),
                                  ppm_after=round(float(b_after.rejected_qty.sum() / max(1, b_after.received_qty.sum()) * 1e6), 0),
                                  contract_ppm_limit=sup["contract_ppm_limit"],
                                  material_shortage_events=int(((self.downtime.reason_category == "Material Shortage") &
                                                                self.downtime.related_po_number.isin(self.pos[self.pos.supplier_id == sup["supplier_id"]].po_number)).sum()),
                                  porosity_ncrs_after=int(((self.ncrs.defect_code == "Porosity") & (pd.to_datetime(self.ncrs.opened_date) >= pd.Timestamp(sup["issue_start"]))).sum()),
                                  porosity_copq_usd_after=round(float(self.ncrs[(self.ncrs.defect_code == "Porosity") & (pd.to_datetime(self.ncrs.opened_date) >= pd.Timestamp(sup["issue_start"]))].cost_of_poor_quality_usd.sum()), 2)),
            problem_carrier=dict(carrier_id=car["carrier_id"], name=car["name"], on_time_all_lanes=car_ot.get(car["carrier_id"]),
                                 on_time_from_lane_origin=round(float(ridge_mem), 3), lane_origin=car["lane_origin"],
                                 sla=car["sla_on_time_target"], all_carriers_on_time=car_ot,
                                 customer_on_time_by_dc=self._otif_by_dc),
            quality_shift_issue=dict(machine_id=q["machine_id"], shift=q["shift"], start=q["start"],
                                     defect_rate_by_period_shift={f"{'after' if a else 'before'}_{s}": float(v) for (a, s), v in crimp.items()}),
            capas=self.capas[["capa_id", "title", "status", "opened_date", "due_date"]].head(3).astype(str).to_dict("records"),
            row_counts={k: int(len(t.df)) for k, t in self.tables.items()},
        )

    # ------------------------------------------------------------- run
    def run(self) -> dict[str, Table]:
        steps = [("master data", self.build_master_data), ("purchasing", self.build_purchasing),
                 ("maintenance", self.build_maintenance), ("line schedule", self.build_line_schedule),
                 ("production & quality", self.build_production_and_quality), ("telemetry", self.build_telemetry),
                 ("inventory & fulfillment", self.build_inventory_and_fulfillment)]
        for label, fn in steps:
            print(f"  · {label} ...", flush=True)
            fn()

        def clean(df):  # drop generator-internal columns (prefixed with _)
            return df[[c for c in df.columns if not c.startswith("_")]]

        A = self._add
        A("erp", "plants", self.plants, "csv", "Manufacturing plants with location and PM compliance target")
        A("mes", "production_lines", self.lines, "json", "Production lines per plant with ideal cycle time")
        A("mes", "work_centers", clean(self.machines), "json", "Machines/work centers in process-flow order on each line")
        A("erp", "warehouses", self.warehouses, "csv", "Plant warehouses and distribution centers")
        A("erp", "parts", self.parts, "csv", "Manufactured part master (finished goods)")
        A("erp", "suppliers", clean(self.suppliers), "csv", "Approved supplier list")
        A("erp", "materials", clean(self.materials), "csv", "Purchased materials and their primary supplier")
        A("erp", "bill_of_materials", self.bom, "csv", "Materials consumed per part")
        A("erp", "customers", self.customers, "csv", "Customer master")
        A("erp", "carriers", self.carriers, "csv", "Freight carriers")
        A("hr", "employees", self.employees, "csv", "Plant workforce")
        A("erp", "purchase_orders", self.pos, "csv", "Purchase order lines")
        A("erp", "goods_receipts", clean(self.receipts), "csv", "Goods receipts with incoming inspection results")
        A("erp", "production_orders", self.prod_orders, "csv", "Manufacturing orders per line")
        A("mes", "shift_production", self.shift_results, "json", "Per line per shift production results (OEE inputs)")
        A("mes", "downtime_events", self.downtime, "json", "Line and machine downtime events with reason codes")
        A("cmms", "maintenance_work_orders", self.work_orders, "csv", "Preventive, corrective and emergency work orders")
        A("qms", "inspections", self.inspections, "csv", "In-process quality inspections with SPC measurements")
        A("qms", "nonconformances", clean(self.ncrs), "csv", "Nonconformance reports (in-process and incoming)")
        A("qms", "capa", self.capas, "csv", "Corrective and preventive actions")
        A("iot_historian", "machine_telemetry", self.telemetry, "json", "Machine sensor readings")
        A("wms", "inventory_snapshots", self.inventory, "parquet", "Daily on-hand inventory by warehouse and item")
        A("erp", "sales_orders", self.sales_orders, "csv", "Customer sales order lines")
        A("wms", "shipments", self.shipments, "csv", "Outbound shipments to customers")
        print("  · anchors ...", flush=True)
        self.compute_anchors()
        return self.tables


# =============================================================================
# 3. WRITER — land each table as files in the raw volume, by source system
# =============================================================================
def write_tables(tables: dict[str, Table], base_path: str, anchors: dict | None = None) -> pd.DataFrame:
    """Write to <base>/<system>/<entity>/... and return a manifest DataFrame.
    Telemetry is split into monthly JSON files the way a historian export would be."""
    import os
    manifest = []
    for name, t in tables.items():
        folder = f"{base_path}/{t.system}/{t.entity}"
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):                          # idempotent re-runs
            os.remove(f"{folder}/{f}")
        if t.entity == "machine_telemetry":
            months = t.df.reading_ts.str[:7]
            for mth, part in t.df.groupby(months):
                part.to_json(f"{folder}/telemetry_{mth}.json", orient="records", lines=True)
        elif t.fmt == "csv":
            t.df.to_csv(f"{folder}/{t.entity}.csv", index=False)
        elif t.fmt == "json":
            t.df.to_json(f"{folder}/{t.entity}.json", orient="records", lines=True, date_format="iso")
        else:
            t.df.to_parquet(f"{folder}/{t.entity}.parquet", index=False)
        manifest.append(dict(source_system=t.system, entity=t.entity, format=t.fmt, rows=len(t.df), path=folder, description=t.description))
        print(f"  wrote {t.system}/{t.entity:<24} {len(t.df):>10,} rows  ({t.fmt})", flush=True)
    if anchors is not None:
        os.makedirs(f"{base_path}/_story", exist_ok=True)
        with open(f"{base_path}/_story/story_anchors.json", "w") as f:
            json.dump(anchors, f, indent=2, default=str)
    return pd.DataFrame(manifest)


if __name__ == "__main__":   # local run:  python mfg_datagen.py --config ../config/demo_config.yml --out /tmp/mfg_raw
    import argparse, yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="../config/demo_config.yml")
    ap.add_argument("--out", default="/tmp/mfg_raw")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    g = MfgGenerator(cfg)
    tabs = g.run()
    write_tables(tabs, a.out, g.anchors)
    print(json.dumps(g.anchors, indent=2, default=str)[:6000])
