# Plant & Line Process Flow Reference

| Field | Value |
|---|---|
| Document ID | PFD-ALL-001 |
| Title | Plant & Line Process Flow Reference |
| Revision | Rev D |
| Effective Date | 2026-04-06 |
| Owner | Dana Whitfield, VP Operations |
| Approver | Marcus Okafor, Director of Reliability & Maintenance |
| Classification | Internal |

## 1. Purpose and scope

This reference lists, for each KK's Parts plant and production line, the ordered work centers material passes through, what each step does and where the constraints are. Work center IDs follow `<LINE>-WC<nn>` in process order, with WC01 as the first step. Machine criticality is **A** (bottleneck, no redundancy), **B** or **C**; the authoritative criticality per asset is in the asset register. Where this document names a bottleneck, it describes the practical constraint, not the register value, except where criticality A is stated.

Flow notation: each line is serial, WC01 to the last WC. Finished goods leave the last work center for the plant warehouse (WH-CLB, WH-GVL, WH-MTY, WH-WRO, WH-PNQ) and then the distribution centers DC-MEM, DC-RNO or DC-RTM.

## 2. Columbus Hydraulics Plant (CLB) - Columbus, OH

### CLB-L1 Valve Body Machining
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| CLB-L1-WC01 | CNC Vertical Mill #1 | Hartwell Machine Tools HAR-279 | A | Rough mill valve body ports and faces from casting MAT-5001. |
| CLB-L1-WC02 | CNC Vertical Mill #2 | Sato Precision SAT-214 | C | Finish mill and drill spool bores. |
| CLB-L1-WC03 | Robotic Deburr Cell #3 | Vantage Robotics VAN-430 | B | Remove burrs from cross-drilled passages. |
| CLB-L1-WC04 | Parts Washer #4 | Brenner Finishing BRE-302 | B | Remove chips and coolant. |
| CLB-L1-WC05 | Coordinate Measuring Machine #5 | Calder Test Systems CAL-774 | B | Verify critical bore dimensions. |

Bottleneck note: the two milling centers set pace. Casting shortages from Brightline Castings (SUP-1007) have caused Material Shortage stops at the start of the line.

### CLB-L2 Pump Assembly
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| CLB-L2-WC01 | Servo Press-Fit Station #1 | Nordberg Presses NOR-660 | C | Press bearings and bushings into pump housings. |
| CLB-L2-WC02 | Robotic Assembly Cell #2 | Kessler Automation KES-356 | B | Install gears and shaft. |
| CLB-L2-WC03 | Robotic Assembly Cell #3 | Vantage Robotics VAN-794 | C | Install seals and end cover; torque fasteners. |
| CLB-L2-WC04 | End-of-Line Test Stand #4 | Calder Test Systems CAL-133 | A | Pressure and flow test. |
| CLB-L2-WC05 | Automated Packaging Line #5 | Kessler Automation KES-861 | B | Label, protect and pack. |

Bottleneck note: the end-of-line test stand sets the final rate.

### CLB-L3 Cylinder Fabrication
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| CLB-L3-WC01 | Automatic Band Saw #1 | Ironbridge Industrial IRO-464 | B | Cut tube and rod stock to length. |
| CLB-L3-WC02 | CNC Turning Center #2 | Sato Precision SAT-742 | B | Turn and bore cylinder components. |
| CLB-L3-WC03 | Robotic MIG Welder #3 | Vantage Robotics VAN-243 | B | Weld ports and mounting features. |
| CLB-L3-WC04 | Paint Booth #4 | Brenner Finishing BRE-439 | A | Prime and paint. |
| CLB-L3-WC05 | End-of-Line Test Stand #5 | Calder Test Systems CAL-205 | C | Pressure test finished cylinders. |

Bottleneck note: welding and paint cure.

## 3. Greenville Drivetrain Plant (GVL) - Greenville, SC

### GVL-L1 Gear Hobbing
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| GVL-L1-WC01 | CNC Turning Center #1 | Sato Precision SAT-484 | C | Turn gear blanks. |
| GVL-L1-WC02 | CNC Gear Hobber #2 | Nordberg Gear Systems NOR-619 | A | Cut gear teeth (roughing). |
| GVL-L1-WC03 | CNC Gear Hobber #3 | Nordberg Gear Systems NOR-137 | B | Cut gear teeth (finishing). |
| GVL-L1-WC04 | Robotic Deburr Cell #4 | Vantage Robotics VAN-228 | B | Break edges and remove burrs. |
| GVL-L1-WC05 | Coordinate Measuring Machine #5 | Calder Test Systems CAL-923 | C | Inspect tooth form and runout. |

Bottleneck note: the hobbing machines.

### GVL-L2 Heat Treat
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| GVL-L2-WC01 | Parts Washer #1 | Brenner Finishing BRE-108 | B | Clean parts before furnace. |
| GVL-L2-WC02 | Carburizing Furnace #2 | Orion Thermal Systems ORI-692 | A | Carburize or harden. |
| GVL-L2-WC03 | Carburizing Furnace #3 | Orion Thermal Systems ORI-749 | B | Second furnace for temper or capacity. |
| GVL-L2-WC04 | Oil Quench Tank #4 | Orion Thermal Systems ORI-967 | B | Quench in oil. |
| GVL-L2-WC05 | Automatic Hardness Tester #5 | Calder Test Systems CAL-375 | B | Verify case depth and hardness. |

Bottleneck note: furnace cycle time; batch process.

### GVL-L3 Gearbox Assembly (ideal cycle 156.5 s/unit)
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| GVL-L3-WC01 | CNC Horizontal Machining Center #1 | Hartwell Machine Tools HAR-119 | A | Machines the gearbox bearing bores. Hartwell Machine Tools HAR-119, installed 2013-08-27, criticality **A**. |
| GVL-L3-WC02 | CNC Horizontal Machining Center #2 | Sato Precision SAT-184 | C | Machines mating faces and remaining features. |
| GVL-L3-WC03 | Servo Press-Fit Station #3 | Nordberg Presses NOR-333 | B | Press bearings, seals and shafts into the housing. |
| GVL-L3-WC04 | Robotic Assembly Cell #4 | Kessler Automation KES-426 | B | Assemble gear sets and torque fasteners. |
| GVL-L3-WC05 | End-of-Line Test Stand #5 | Calder Test Systems CAL-988 | B | Run, noise and leak test. |
| GVL-L3-WC06 | Automated Packaging Line #6 | Kessler Automation KES-931 | B | Pack, label and release to WH-GVL. |

Bottleneck note: **GVL-L3-WC01** is the line bottleneck with no redundancy. Its spindle bearing condition has driven the line's OEE from 84% in March 2026 to 50% in September 2026. Bore-position drift feeds quality records such as CAPA-2026-103. See RPT-GVL-2026-08 and PM-CNC-030 / MOC-2026-031.

## 4. Monterrey Machining Plant (MTY) - Monterrey, NL, Mexico

### MTY-L1 Casting Finishing
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| MTY-L1-WC01 | Automatic Band Saw #1 | Ironbridge Industrial IRO-367 | B | Remove gates and risers from castings. |
| MTY-L1-WC02 | Shot Blast Cabinet #2 | Ironbridge Industrial IRO-950 | C | Clean surface and remove sand. |
| MTY-L1-WC03 | CNC Vertical Mill #3 | Sato Precision SAT-743 | A | Mill datum and mating surfaces. |
| MTY-L1-WC04 | Coordinate Measuring Machine #4 | Calder Test Systems CAL-247 | C | Inspect datum features. |

Bottleneck note: starved by casting supply; Material Shortage stops since May 2026 (Brightline Castings); see LSR-MTY-2026-011.

### MTY-L2 Housing Machining
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| MTY-L2-WC01 | CNC Horizontal Machining Center #1 | Hartwell Machine Tools HAR-956 | A | Rough machine housing. |
| MTY-L2-WC02 | CNC Horizontal Machining Center #2 | Hartwell Machine Tools HAR-310 | B | Semi-finish bores and faces. |
| MTY-L2-WC03 | CNC Horizontal Machining Center #3 | Sato Precision SAT-523 | C | Finish bores and tapping. |
| MTY-L2-WC04 | Parts Washer #4 | Brenner Finishing BRE-921 | B | Remove chips. |
| MTY-L2-WC05 | Helium Leak Tester #5 | Calder Test Systems CAL-613 | B | Pressure-decay test, catching porosity leakers. |

Bottleneck note: the three machining centers run in series; the leak tester rejects porosity from poor castings.

### MTY-L3 Paint & Coat
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| MTY-L3-WC01 | Parts Washer #1 | Brenner Finishing BRE-321 | B | Degrease before paint. |
| MTY-L3-WC02 | Paint Booth #2 | Brenner Finishing BRE-143 | B | Apply coating. |
| MTY-L3-WC03 | Cure Oven #3 | Orion Thermal Systems ORI-841 | A | Cure coating. |
| MTY-L3-WC04 | Automated Packaging Line #4 | Kessler Automation KES-850 | C | Pack for shipment. |

Bottleneck note: cure oven capacity.

## 5. Wroclaw Electrical Plant (WRO) - Wroclaw, Poland

### WRO-L1 Wire Cut & Crimp
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| WRO-L1-WC01 | Automatic Wire Cut & Strip #1 | Lumex Equipment LUM-401 | A | Cut wire to length and strip insulation. |
| WRO-L1-WC02 | Terminal Crimp Press #2 | Lumex Equipment LUM-486 | B | Crimp terminals (Lumex Equipment LUM-486). |
| WRO-L1-WC03 | Terminal Crimp Press #3 | Lumex Equipment LUM-697 | B | Crimp terminals on the opposite wire end. |
| WRO-L1-WC04 | Crimp Pull Tester #4 | Calder Test Systems CAL-954 | C | Pull-force test sample crimps. |

Naming note: press numbering (#2, #3) follows the asset register; there is no Terminal Crimp Press #1 on this line. Quality note: crimp height 1.650 mm +/- 0.050 mm (control plan CP-WRO-L1 Rev F); C-shift defects on WRO-L1-WC02 are tracked in CAPA-2026-102.

### WRO-L2 Harness Assembly
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| WRO-L2-WC01 | Robotic Assembly Cell #1 | Vantage Robotics VAN-250 | A | Lay out wires on board and route. |
| WRO-L2-WC02 | Robotic Assembly Cell #2 | Kessler Automation KES-807 | B | Install connectors, tape and sleeve. |
| WRO-L2-WC03 | Harness Continuity Tester #3 | Calder Test Systems CAL-325 | B | Electrical continuity and hi-pot test. |
| WRO-L2-WC04 | Automated Packaging Line #4 | Kessler Automation KES-252 | C | Pack and label. |

Bottleneck note: the assembly cells.

### WRO-L3 Control Module Assembly
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| WRO-L3-WC01 | SMT Pick-and-Place #1 | Lumex Equipment LUM-664 | B | Place components on boards. |
| WRO-L3-WC02 | Reflow Oven #2 | Orion Thermal Systems ORI-955 | A | Solder reflow. |
| WRO-L3-WC03 | Automated Optical Inspection #3 | Calder Test Systems CAL-756 | B | Automated optical inspection of solder joints. |
| WRO-L3-WC04 | Robotic Assembly Cell #4 | Vantage Robotics VAN-794 | C | Assemble boards into housings. |
| WRO-L3-WC05 | End-of-Line Test Stand #5 | Calder Test Systems CAL-434 | C | Functional test. |

Bottleneck note: SMT placement.

## 6. Pune Fastener Plant (PNQ) - Pune, MH, India

### PNQ-L1 Cold Heading
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| PNQ-L1-WC01 | Wire Drawing Machine #1 | Ironbridge Industrial IRO-447 | B | Draw wire rod to size. |
| PNQ-L1-WC02 | Multi-Station Cold Header #2 | Nordberg Presses NOR-138 | A | Form fastener heads. |
| PNQ-L1-WC03 | Thread Rolling Machine #3 | Nordberg Presses NOR-221 | C | Roll threads. |
| PNQ-L1-WC04 | Optical Sorting Machine #4 | Calder Test Systems CAL-318 | C | Sort defects and mixed parts. |

Bottleneck note: cold header.

### PNQ-L2 Stamping
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| PNQ-L2-WC01 | Servo Coil Feeder #1 | Nordberg Presses NOR-787 | B | Feed and level coil. |
| PNQ-L2-WC02 | Progressive Stamping Press #2 | Nordberg Presses NOR-135 | A | Blank and form. |
| PNQ-L2-WC03 | Progressive Stamping Press #3 | Nordberg Presses NOR-763 | C | Pierce and finish forming. |
| PNQ-L2-WC04 | Robotic Deburr Cell #4 | Vantage Robotics VAN-238 | C | Remove burrs. |
| PNQ-L2-WC05 | Automated Packaging Line #5 | Kessler Automation KES-731 | B | Pack stampings. |

Bottleneck note: press changeover (die change) is the main loss; see SOP-PRD-014.

### PNQ-L3 Plating & Finishing
| Work center | Machine name | OEM / model | Crit. | Step description |
|---|---|---|---|---|
| PNQ-L3-WC01 | Parts Washer #1 | Brenner Finishing BRE-578 | C | Clean and degrease. |
| PNQ-L3-WC02 | Zinc-Nickel Plating Line #2 | Brenner Finishing BRE-510 | B | Electroplate. |
| PNQ-L3-WC03 | Cure Oven #3 | Orion Thermal Systems ORI-966 | A | Bake to relieve hydrogen embrittlement and cure. |
| PNQ-L3-WC04 | Optical Sorting Machine #4 | Calder Test Systems CAL-647 | C | Final visual sort. |

Bottleneck note: plating tank dwell time.

## 7. Using this reference

The process_flow order in this document matches the line configuration in the manufacturing data model. When a work center is down, upstream stations buffer until their output limit, and downstream stations starve. In OEE terms, stops at a bottleneck affect line output one-for-one; stops elsewhere are partly absorbed by buffers.

Related documents: SOP-PRD-001, PLN-PRD-003, GLS-PRD-001.
