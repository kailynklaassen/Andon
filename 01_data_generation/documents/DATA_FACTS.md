# Data Facts — computed from the generated data (seed 42)

Use these numbers instead of inventing values. Fiscal quarters: Q1 Oct–Dec 2025, Q2 Jan–Mar 2026, Q3 Apr–Jun 2026, Q4 Jul–Sep 2026.

## Lines and ideal cycle times

| line_id   | line_name               |   ideal_cycle_time_s |   work_center_count |
|:----------|:------------------------|---------------------:|--------------------:|
| CLB-L1    | Valve Body Machining    |               102.81 |                   5 |
| CLB-L2    | Pump Assembly           |                99.84 |                   5 |
| CLB-L3    | Cylinder Fabrication    |                96.63 |                   5 |
| GVL-L1    | Gear Hobbing            |               150.86 |                   5 |
| GVL-L2    | Heat Treat              |               119.91 |                   5 |
| GVL-L3    | Gearbox Assembly        |               156.52 |                   6 |
| MTY-L1    | Casting Finishing       |               174.47 |                   4 |
| MTY-L2    | Housing Machining       |               173.21 |                   5 |
| MTY-L3    | Paint & Coat            |               165.78 |                   4 |
| WRO-L1    | Wire Cut & Crimp        |                25.35 |                   4 |
| WRO-L2    | Harness Assembly        |                29.4  |                   4 |
| WRO-L3    | Control Module Assembly |                29.11 |                   5 |
| PNQ-L1    | Cold Heading            |                 3.25 |                   4 |
| PNQ-L2    | Stamping                |                 3.39 |                   5 |
| PNQ-L3    | Plating & Finishing     |                 2.82 |                   4 |

## All work centers (exact names, OEM, model, criticality)

| machine_id   | machine_name                       | machine_type         | oem                    | model   | criticality   |   pm_interval_days |
|:-------------|:-----------------------------------|:---------------------|:-----------------------|:--------|:--------------|-------------------:|
| CLB-L1-WC01  | CNC Vertical Mill #1               | CNC_MILL             | Hartwell Machine Tools | HAR-279 | A             |                 30 |
| CLB-L1-WC02  | CNC Vertical Mill #2               | CNC_MILL             | Sato Precision         | SAT-214 | C             |                 30 |
| CLB-L1-WC03  | Robotic Deburr Cell #3             | DEBURR_CELL          | Vantage Robotics       | VAN-430 | B             |                 60 |
| CLB-L1-WC04  | Parts Washer #4                    | WASH_STATION         | Brenner Finishing      | BRE-302 | B             |                 60 |
| CLB-L1-WC05  | Coordinate Measuring Machine #5    | CMM_INSPECTION       | Calder Test Systems    | CAL-774 | B             |                 90 |
| CLB-L2-WC01  | Servo Press-Fit Station #1         | PRESS_FIT            | Nordberg Presses       | NOR-660 | C             |                 45 |
| CLB-L2-WC02  | Robotic Assembly Cell #2           | ASSEMBLY_CELL        | Kessler Automation     | KES-356 | B             |                 60 |
| CLB-L2-WC03  | Robotic Assembly Cell #3           | ASSEMBLY_CELL        | Vantage Robotics       | VAN-794 | C             |                 60 |
| CLB-L2-WC04  | End-of-Line Test Stand #4          | TEST_STAND           | Calder Test Systems    | CAL-133 | A             |                 60 |
| CLB-L2-WC05  | Automated Packaging Line #5        | PACKAGING            | Kessler Automation     | KES-861 | B             |                 60 |
| CLB-L3-WC01  | Automatic Band Saw #1              | SAW_CELL             | Ironbridge Industrial  | IRO-464 | B             |                 45 |
| CLB-L3-WC02  | CNC Turning Center #2              | CNC_LATHE            | Sato Precision         | SAT-742 | B             |                 30 |
| CLB-L3-WC03  | Robotic MIG Welder #3              | ROBOTIC_WELDER       | Vantage Robotics       | VAN-243 | B             |                 45 |
| CLB-L3-WC04  | Paint Booth #4                     | PAINT_BOOTH          | Brenner Finishing      | BRE-439 | A             |                 60 |
| CLB-L3-WC05  | End-of-Line Test Stand #5          | TEST_STAND           | Calder Test Systems    | CAL-205 | C             |                 60 |
| GVL-L1-WC01  | CNC Turning Center #1              | CNC_LATHE            | Sato Precision         | SAT-484 | C             |                 30 |
| GVL-L1-WC02  | CNC Gear Hobber #2                 | GEAR_HOBBER          | Nordberg Gear Systems  | NOR-619 | A             |                 45 |
| GVL-L1-WC03  | CNC Gear Hobber #3                 | GEAR_HOBBER          | Nordberg Gear Systems  | NOR-137 | B             |                 45 |
| GVL-L1-WC04  | Robotic Deburr Cell #4             | DEBURR_CELL          | Vantage Robotics       | VAN-228 | B             |                 60 |
| GVL-L1-WC05  | Coordinate Measuring Machine #5    | CMM_INSPECTION       | Calder Test Systems    | CAL-923 | C             |                 90 |
| GVL-L2-WC01  | Parts Washer #1                    | WASH_STATION         | Brenner Finishing      | BRE-108 | B             |                 60 |
| GVL-L2-WC02  | Carburizing Furnace #2             | HEAT_TREAT_FURNACE   | Orion Thermal Systems  | ORI-692 | A             |                 60 |
| GVL-L2-WC03  | Carburizing Furnace #3             | HEAT_TREAT_FURNACE   | Orion Thermal Systems  | ORI-749 | B             |                 60 |
| GVL-L2-WC04  | Oil Quench Tank #4                 | QUENCH_TANK          | Orion Thermal Systems  | ORI-967 | B             |                 90 |
| GVL-L2-WC05  | Automatic Hardness Tester #5       | HARDNESS_TESTER      | Calder Test Systems    | CAL-375 | B             |                 90 |
| GVL-L3-WC01  | CNC Horizontal Machining Center #1 | CNC_MACHINING_CENTER | Hartwell Machine Tools | HAR-119 | A             |                 30 |
| GVL-L3-WC02  | CNC Horizontal Machining Center #2 | CNC_MACHINING_CENTER | Sato Precision         | SAT-184 | C             |                 30 |
| GVL-L3-WC03  | Servo Press-Fit Station #3         | PRESS_FIT            | Nordberg Presses       | NOR-333 | B             |                 45 |
| GVL-L3-WC04  | Robotic Assembly Cell #4           | ASSEMBLY_CELL        | Kessler Automation     | KES-426 | B             |                 60 |
| GVL-L3-WC05  | End-of-Line Test Stand #5          | TEST_STAND           | Calder Test Systems    | CAL-988 | B             |                 60 |
| GVL-L3-WC06  | Automated Packaging Line #6        | PACKAGING            | Kessler Automation     | KES-931 | B             |                 60 |
| MTY-L1-WC01  | Automatic Band Saw #1              | SAW_CELL             | Ironbridge Industrial  | IRO-367 | B             |                 45 |
| MTY-L1-WC02  | Shot Blast Cabinet #2              | SHOT_BLAST           | Ironbridge Industrial  | IRO-950 | C             |                 30 |
| MTY-L1-WC03  | CNC Vertical Mill #3               | CNC_MILL             | Sato Precision         | SAT-743 | A             |                 30 |
| MTY-L1-WC04  | Coordinate Measuring Machine #4    | CMM_INSPECTION       | Calder Test Systems    | CAL-247 | C             |                 90 |
| MTY-L2-WC01  | CNC Horizontal Machining Center #1 | CNC_MACHINING_CENTER | Hartwell Machine Tools | HAR-956 | A             |                 30 |
| MTY-L2-WC02  | CNC Horizontal Machining Center #2 | CNC_MACHINING_CENTER | Hartwell Machine Tools | HAR-310 | B             |                 30 |
| MTY-L2-WC03  | CNC Horizontal Machining Center #3 | CNC_MACHINING_CENTER | Sato Precision         | SAT-523 | C             |                 30 |
| MTY-L2-WC04  | Parts Washer #4                    | WASH_STATION         | Brenner Finishing      | BRE-921 | B             |                 60 |
| MTY-L2-WC05  | Helium Leak Tester #5              | LEAK_TESTER          | Calder Test Systems    | CAL-613 | B             |                 90 |
| MTY-L3-WC01  | Parts Washer #1                    | WASH_STATION         | Brenner Finishing      | BRE-321 | B             |                 60 |
| MTY-L3-WC02  | Paint Booth #2                     | PAINT_BOOTH          | Brenner Finishing      | BRE-143 | B             |                 60 |
| MTY-L3-WC03  | Cure Oven #3                       | CURE_OVEN            | Orion Thermal Systems  | ORI-841 | A             |                 60 |
| MTY-L3-WC04  | Automated Packaging Line #4        | PACKAGING            | Kessler Automation     | KES-850 | C             |                 60 |
| WRO-L1-WC01  | Automatic Wire Cut & Strip #1      | WIRE_CUTTER          | Lumex Equipment        | LUM-401 | A             |                 45 |
| WRO-L1-WC02  | Terminal Crimp Press #2            | CRIMP_PRESS          | Lumex Equipment        | LUM-486 | B             |                 30 |
| WRO-L1-WC03  | Terminal Crimp Press #3            | CRIMP_PRESS          | Lumex Equipment        | LUM-697 | B             |                 30 |
| WRO-L1-WC04  | Crimp Pull Tester #4               | PULL_TESTER          | Calder Test Systems    | CAL-954 | C             |                 90 |
| WRO-L2-WC01  | Robotic Assembly Cell #1           | ASSEMBLY_CELL        | Vantage Robotics       | VAN-250 | A             |                 60 |
| WRO-L2-WC02  | Robotic Assembly Cell #2           | ASSEMBLY_CELL        | Kessler Automation     | KES-807 | B             |                 60 |
| WRO-L2-WC03  | Harness Continuity Tester #3       | CONTINUITY_TESTER    | Calder Test Systems    | CAL-325 | B             |                 90 |
| WRO-L2-WC04  | Automated Packaging Line #4        | PACKAGING            | Kessler Automation     | KES-252 | C             |                 60 |
| WRO-L3-WC01  | SMT Pick-and-Place #1              | SMT_PLACER           | Lumex Equipment        | LUM-664 | B             |                 30 |
| WRO-L3-WC02  | Reflow Oven #2                     | REFLOW_OVEN          | Orion Thermal Systems  | ORI-955 | A             |                 60 |
| WRO-L3-WC03  | Automated Optical Inspection #3    | AOI_INSPECTION       | Calder Test Systems    | CAL-756 | B             |                 90 |
| WRO-L3-WC04  | Robotic Assembly Cell #4           | ASSEMBLY_CELL        | Vantage Robotics       | VAN-794 | C             |                 60 |
| WRO-L3-WC05  | End-of-Line Test Stand #5          | TEST_STAND           | Calder Test Systems    | CAL-434 | C             |                 60 |
| PNQ-L1-WC01  | Wire Drawing Machine #1            | WIRE_DRAWER          | Ironbridge Industrial  | IRO-447 | B             |                 45 |
| PNQ-L1-WC02  | Multi-Station Cold Header #2       | COLD_HEADER          | Nordberg Presses       | NOR-138 | A             |                 30 |
| PNQ-L1-WC03  | Thread Rolling Machine #3          | THREAD_ROLLER        | Nordberg Presses       | NOR-221 | C             |                 45 |
| PNQ-L1-WC04  | Optical Sorting Machine #4         | OPTICAL_SORTER       | Calder Test Systems    | CAL-318 | C             |                 90 |
| PNQ-L2-WC01  | Servo Coil Feeder #1               | COIL_FEEDER          | Nordberg Presses       | NOR-787 | B             |                 60 |
| PNQ-L2-WC02  | Progressive Stamping Press #2      | STAMPING_PRESS       | Nordberg Presses       | NOR-135 | A             |                 30 |
| PNQ-L2-WC03  | Progressive Stamping Press #3      | STAMPING_PRESS       | Nordberg Presses       | NOR-763 | C             |                 30 |
| PNQ-L2-WC04  | Robotic Deburr Cell #4             | DEBURR_CELL          | Vantage Robotics       | VAN-238 | C             |                 60 |
| PNQ-L2-WC05  | Automated Packaging Line #5        | PACKAGING            | Kessler Automation     | KES-731 | B             |                 60 |
| PNQ-L3-WC01  | Parts Washer #1                    | WASH_STATION         | Brenner Finishing      | BRE-578 | C             |                 60 |
| PNQ-L3-WC02  | Zinc-Nickel Plating Line #2        | PLATING_TANK         | Brenner Finishing      | BRE-510 | B             |                 60 |
| PNQ-L3-WC03  | Cure Oven #3                       | CURE_OVEN            | Orion Thermal Systems  | ORI-966 | A             |                 60 |
| PNQ-L3-WC04  | Optical Sorting Machine #4         | OPTICAL_SORTER       | Calder Test Systems    | CAL-647 | C             |                 90 |

## OEE by plant by fiscal quarter

| plant_id   | q       |   availability |   performance |   quality |   oee |       good_units |
|:-----------|:--------|---------------:|--------------:|----------:|------:|-----------------:|
| CLB        | FY26 Q1 |          0.97  |         0.868 |     0.994 | 0.837 | 152321           |
| CLB        | FY26 Q2 |          0.969 |         0.867 |     0.994 | 0.835 | 147952           |
| CLB        | FY26 Q3 |          0.928 |         0.867 |     0.987 | 0.794 | 142627           |
| CLB        | FY26 Q4 |          0.923 |         0.868 |     0.981 | 0.786 | 143102           |
| GVL        | FY26 Q1 |          0.964 |         0.866 |     0.989 | 0.826 | 106721           |
| GVL        | FY26 Q2 |          0.966 |         0.868 |     0.989 | 0.828 | 104147           |
| GVL        | FY26 Q3 |          0.902 |         0.859 |     0.985 | 0.762 |  97621           |
| GVL        | FY26 Q4 |          0.867 |         0.844 |     0.981 | 0.718 |  93665           |
| MTY        | FY26 Q1 |          0.964 |         0.867 |     0.988 | 0.825 |  87547           |
| MTY        | FY26 Q2 |          0.969 |         0.87  |     0.988 | 0.833 |  86006           |
| MTY        | FY26 Q3 |          0.912 |         0.854 |     0.974 | 0.759 |  79468           |
| MTY        | FY26 Q4 |          0.874 |         0.847 |     0.96  | 0.711 |  75460           |
| PNQ        | FY26 Q1 |          0.967 |         0.87  |     0.995 | 0.837 |      4.84642e+06 |
| PNQ        | FY26 Q2 |          0.967 |         0.871 |     0.995 | 0.838 |      4.72096e+06 |
| PNQ        | FY26 Q3 |          0.97  |         0.868 |     0.995 | 0.838 |      4.78748e+06 |
| PNQ        | FY26 Q4 |          0.971 |         0.87  |     0.995 | 0.84  |      4.86885e+06 |
| WRO        | FY26 Q1 |          0.966 |         0.87  |     0.992 | 0.833 | 543529           |
| WRO        | FY26 Q2 |          0.971 |         0.869 |     0.992 | 0.837 | 530768           |
| WRO        | FY26 Q3 |          0.967 |         0.869 |     0.99  | 0.832 | 535245           |
| WRO        | FY26 Q4 |          0.958 |         0.867 |     0.984 | 0.818 | 532780           |

## OEE by plant FY26

| plant_id   |   availability |   performance |   quality |   oee |       good_units |
|:-----------|---------------:|--------------:|----------:|------:|-----------------:|
| CLB        |          0.948 |         0.867 |     0.989 | 0.813 | 586002           |
| GVL        |          0.924 |         0.86  |     0.986 | 0.783 | 402154           |
| MTY        |          0.93  |         0.86  |     0.978 | 0.782 | 328481           |
| PNQ        |          0.969 |         0.87  |     0.995 | 0.838 |      1.92237e+07 |
| WRO        |          0.965 |         0.869 |     0.989 | 0.83  |      2.14232e+06 |

## GVL-L3 monthly good units & OEE

| m       |   availability |   performance |   quality |   oee |   good_units |
|:--------|---------------:|--------------:|----------:|------:|-------------:|
| 2025-10 |          0.961 |         0.867 |     0.989 | 0.824 |        10948 |
| 2025-11 |          0.949 |         0.866 |     0.989 | 0.813 |         9819 |
| 2025-12 |          0.976 |         0.871 |     0.989 | 0.841 |        11167 |
| 2026-01 |          0.954 |         0.87  |     0.988 | 0.819 |        10740 |
| 2026-02 |          0.939 |         0.871 |     0.988 | 0.808 |         9483 |
| 2026-03 |          0.978 |         0.868 |     0.985 | 0.836 |        10672 |
| 2026-04 |          0.913 |         0.847 |     0.978 | 0.757 |         9657 |
| 2026-05 |          0.831 |         0.834 |     0.971 | 0.673 |         8476 |
| 2026-06 |          0.76  |         0.815 |     0.963 | 0.596 |         7608 |
| 2026-07 |          0.717 |         0.796 |     0.958 | 0.547 |         7267 |
| 2026-08 |          0.769 |         0.786 |     0.952 | 0.575 |         7245 |
| 2026-09 |          0.679 |         0.77  |     0.947 | 0.495 |         6323 |

## Downtime minutes share by reason, by quarter (all plants)

| q       |   Changeover |   Equipment Failure |   Material Shortage |   No Operator |   Planned Maintenance |   Quality Hold |
|:--------|-------------:|--------------------:|--------------------:|--------------:|----------------------:|---------------:|
| FY26 Q1 |         40.6 |                16.6 |                 2.3 |           4.3 |                  29.6 |            6.6 |
| FY26 Q2 |         43   |                13.9 |                 3   |           3.6 |                  28.5 |            8.1 |
| FY26 Q3 |         22.2 |                12.2 |                24.2 |           3   |                  16.4 |           22   |
| FY26 Q4 |         18.2 |                15.2 |                27.2 |           1.3 |                  12.6 |           25.5 |

## Material-shortage events on MTY-L2 in June 2026

| downtime_event_id   | start_ts   | duration_minutes   | reason_detail   | related_po_number   |
|---------------------|------------|--------------------|-----------------|---------------------|

## Supplier on-time & PPM FY26

| supplier_id   | supplier_name           |   receipts |   on_time |   ppm |
|:--------------|:------------------------|-----------:|----------:|------:|
| SUP-1002      | Keystone Foundry        |         71 |     0.972 |   347 |
| SUP-1004      | Allegheny Bar Products  |        229 |     0.943 |   230 |
| SUP-1006      | Rhein Stahl Service     |         74 |     0.878 |   121 |
| SUP-1007      | Brightline Castings     |        314 |     0.713 |  1361 |
| SUP-1008      | Sentinel Bearings       |         60 |     0.933 |   120 |
| SUP-1009      | Kyoei Bearing Co.       |         92 |     0.924 |   139 |
| SUP-1010      | Delta Seal Technologies |         70 |     0.914 |   276 |
| SUP-1011      | ProFlow Fittings        |         26 |     1     |   274 |
| SUP-1012      | Ohio Valley Hydraulics  |         58 |     0.931 |   261 |
| SUP-1013      | Vistula Cable Works     |         34 |     0.882 |   229 |
| SUP-1014      | NordWire GmbH           |         59 |     0.881 |   391 |
| SUP-1015      | Pacific Semicon Supply  |         22 |     0.864 |   352 |
| SUP-1016      | Arrowpoint Electronics  |         24 |     1     |   196 |
| SUP-1017      | Danube Connectors       |         50 |     0.9   |   309 |
| SUP-1018      | Deccan Wire Industries  |         21 |     0.857 |   334 |
| SUP-1019      | Sahyadri Steel Wire     |         24 |     0.792 |   220 |
| SUP-1020      | ChemCoat Solutions      |        165 |     0.939 |    95 |
| SUP-1021      | Lusitania Finishes      |         98 |     0.888 |   320 |
| SUP-1022      | Midwest Corrugated      |        120 |     0.925 |    88 |
| SUP-1023      | EuroPack Logistics      |        151 |     0.934 |   342 |
| SUP-1025      | Konkan Packaging        |        121 |     0.926 |   432 |

## Supplier on-time & PPM by quarter (castings suppliers)

| supplier_name       | q       |   receipts |   on_time |   ppm |
|:--------------------|:--------|-----------:|----------:|------:|
| Brightline Castings | FY26 Q1 |         67 |     0.925 |   306 |
| Brightline Castings | FY26 Q2 |         82 |     0.89  |   205 |
| Brightline Castings | FY26 Q3 |         87 |     0.644 |  1950 |
| Brightline Castings | FY26 Q4 |         78 |     0.423 |  2745 |
| Keystone Foundry    | FY26 Q1 |         16 |     1     |   440 |
| Keystone Foundry    | FY26 Q2 |         18 |     0.944 |   394 |
| Keystone Foundry    | FY26 Q3 |         18 |     0.944 |   308 |
| Keystone Foundry    | FY26 Q4 |         19 |     1     |   260 |

## Brightline monthly on-time & PPM

| mo      |   receipts |   on_time |   ppm |
|:--------|-----------:|----------:|------:|
| 2025-10 |         10 |     1     |   178 |
| 2025-11 |         27 |     0.926 |   241 |
| 2025-12 |         30 |     0.9   |   397 |
| 2026-01 |         28 |     0.821 |   203 |
| 2026-02 |         26 |     0.885 |   221 |
| 2026-03 |         28 |     0.964 |   195 |
| 2026-04 |         29 |     1     |   167 |
| 2026-05 |         28 |     0.5   |  2353 |
| 2026-06 |         30 |     0.433 |  3046 |
| 2026-07 |         28 |     0.5   |  2694 |
| 2026-08 |         28 |     0.464 |  2645 |
| 2026-09 |         22 |     0.273 |  2910 |

## Porosity NCRs & COPQ by month (from 2026-05)

| mo      |   ncrs |   copq_usd |
|:--------|-------:|-----------:|
| 2026-05 |     56 |     170056 |
| 2026-06 |     86 |     362466 |
| 2026-07 |     74 |     293750 |
| 2026-08 |     84 |     368388 |
| 2026-09 |     80 |     485585 |

## Porosity NCRs after 2026-05-01 by plant & source

| plant_id   | source              |   ncr_id |
|:-----------|:--------------------|---------:|
| CLB        | In-Process          |       79 |
| CLB        | Incoming Inspection |       39 |
| GVL        | Incoming Inspection |       51 |
| MTY        | In-Process          |      168 |
| MTY        | Incoming Inspection |       43 |

## GVL-L3 'Bore out of tolerance' NCRs by month

| mo      |   ncr_id |
|:--------|---------:|
| 2025-12 |        1 |
| 2026-03 |        3 |
| 2026-04 |       10 |
| 2026-05 |       14 |
| 2026-06 |       10 |
| 2026-07 |       24 |
| 2026-08 |       15 |
| 2026-09 |       17 |

## Top defect codes by plant (NCR count, FY26)

| plant_id   | defect_code              |   ncr_id |
|:-----------|:-------------------------|---------:|
| CLB        | Porosity                 |      137 |
| CLB        | Damage in transit        |       23 |
| CLB        | Dimensional              |       19 |
| GVL        | Bore out of tolerance    |      102 |
| GVL        | Porosity                 |       73 |
| GVL        | Burr                     |       20 |
| MTY        | Porosity                 |      242 |
| MTY        | Bore out of tolerance    |       31 |
| MTY        | Leak at test             |       24 |
| PNQ        | Damage in transit        |       25 |
| PNQ        | Thread defect            |       24 |
| PNQ        | Plating thickness        |       20 |
| WRO        | Crimp height out of spec |       26 |
| WRO        | Damage in transit        |       15 |
| WRO        | Documentation            |       12 |

## NCR count & COPQ by plant by quarter

| plant_id   | q       |   ncrs |         copq_usd |
|:-----------|:--------|-------:|-----------------:|
| CLB        | FY26 Q1 |     26 |  17094           |
| CLB        | FY26 Q2 |     36 |  73691           |
| CLB        | FY26 Q3 |     73 | 261508           |
| CLB        | FY26 Q4 |     96 | 633746           |
| GVL        | FY26 Q1 |     27 | 295631           |
| GVL        | FY26 Q2 |     41 | 317362           |
| GVL        | FY26 Q3 |     81 |      1.10131e+06 |
| GVL        | FY26 Q4 |    115 |      1.41067e+06 |
| MTY        | FY26 Q1 |     48 | 198959           |
| MTY        | FY26 Q2 |     38 | 158434           |
| MTY        | FY26 Q3 |    113 | 405046           |
| MTY        | FY26 Q4 |    172 | 697661           |
| PNQ        | FY26 Q1 |     36 |  15179           |
| PNQ        | FY26 Q2 |     42 |  20730           |
| PNQ        | FY26 Q3 |     40 |  19472           |
| PNQ        | FY26 Q4 |     41 |  23799           |
| WRO        | FY26 Q1 |     10 |   4571           |
| WRO        | FY26 Q2 |     25 |  13474           |
| WRO        | FY26 Q3 |     24 |  14611           |
| WRO        | FY26 Q4 |     40 |  25670           |

## First pass yield by plant by quarter (good/total)

| plant_id   | q       |    fpy |
|:-----------|:--------|-------:|
| CLB        | FY26 Q1 | 0.994  |
| CLB        | FY26 Q2 | 0.9941 |
| CLB        | FY26 Q3 | 0.9872 |
| CLB        | FY26 Q4 | 0.981  |
| GVL        | FY26 Q1 | 0.9889 |
| GVL        | FY26 Q2 | 0.9887 |
| GVL        | FY26 Q3 | 0.9847 |
| GVL        | FY26 Q4 | 0.9809 |
| MTY        | FY26 Q1 | 0.9878 |
| MTY        | FY26 Q2 | 0.9876 |
| MTY        | FY26 Q3 | 0.9745 |
| MTY        | FY26 Q4 | 0.9598 |
| PNQ        | FY26 Q1 | 0.9946 |
| PNQ        | FY26 Q2 | 0.9946 |
| PNQ        | FY26 Q3 | 0.9946 |
| PNQ        | FY26 Q4 | 0.9946 |
| WRO        | FY26 Q1 | 0.9918 |
| WRO        | FY26 Q2 | 0.9918 |
| WRO        | FY26 Q3 | 0.9897 |
| WRO        | FY26 Q4 | 0.9845 |

## WRO-L1 crimp height: mean, Cpk, defect rate by period & shift

| after   | shift   |   mean_mm |    cpk |   defect_rate |
|:--------|:--------|----------:|-------:|--------------:|
| False   | A       |    1.6525 | 1.3369 |        0.0121 |
| False   | B       |    1.6525 | 1.335  |        0.0139 |
| False   | C       |    1.6524 | 1.3305 |        0.0151 |
| True    | A       |    1.6526 | 1.344  |        0.0143 |
| True    | B       |    1.6525 | 1.3401 |        0.0149 |
| True    | C       |    1.6779 | 0.3251 |        0.1359 |

## CAPA register (storyline CAPAs + counts)

| capa_id       | title                                                  | root_cause_category       | plant_id   | supplier_id   | opened_date   | due_date   |   closed_date | status      | owner_id   |   effectiveness_verified |
|:--------------|:-------------------------------------------------------|:--------------------------|:-----------|:--------------|:--------------|:-----------|--------------:|:------------|:-----------|-------------------------:|
| CAPA-2026-101 | SCAR: casting porosity from Brightline Castings        | Supplier                  | MTY        | SUP-1007      | 2026-05-25    | 2026-07-24 |           nan | Overdue     | E30336     |                      nan |
| CAPA-2026-102 | Crimp height variation on WRO-L1-WC02 night shift      | Method / Work Instruction | WRO        | nan           | 2026-07-08    | 2026-08-22 |           nan | In Progress | E30487     |                      nan |
| CAPA-2026-103 | Bore position drift on GVL-L3-WC01 (spindle condition) | Machine                   | GVL        | nan           | 2026-05-24    | 2026-07-23 |           nan | Open        | E30201     |                      nan |

Routine CAPAs by status: {'Closed': 27, 'In Progress': 3}

## PM compliance by plant and line

| plant_id   | line_id   |   done |
|:-----------|:----------|-------:|
| CLB        | CLB-L1    |  0.953 |
| CLB        | CLB-L2    |  0.971 |
| CLB        | CLB-L3    |  0.975 |
| GVL        | GVL-L1    |  0.86  |
| GVL        | GVL-L2    |  0.806 |
| GVL        | GVL-L3    |  0.767 |
| MTY        | MTY-L1    |  0.872 |
| MTY        | MTY-L2    |  0.939 |
| MTY        | MTY-L3    |  0.96  |
| PNQ        | PNQ-L1    |  0.914 |
| PNQ        | PNQ-L2    |  1     |
| PNQ        | PNQ-L3    |  0.957 |
| WRO        | WRO-L1    |  1     |
| WRO        | WRO-L2    |  1     |
| WRO        | WRO-L3    |  0.944 |

## Breakdowns (Corrective+Emergency) & cost by plant FY26

| plant_id   |   breakdowns |   parts |   contractor |
|:-----------|-------------:|--------:|-------------:|
| CLB        |           48 |   55020 |         2106 |
| GVL        |           83 |  154038 |       149373 |
| MTY        |           44 |   69806 |         5217 |
| PNQ        |           38 |   69246 |            0 |
| WRO        |           48 |   75588 |        10660 |

## GVL-L3-WC01 work orders since 2026-03-15 (all)

| work_order_id   | work_order_type   | failure_mode         | created_ts          | completed_ts        | status    |   labor_hours |   parts_cost_usd |   contractor_cost_usd |
|:----------------|:------------------|:---------------------|:--------------------|:--------------------|:----------|--------------:|-----------------:|----------------------:|
| WO-900286       | Preventive        | nan                  | 2026-03-29 22:00:00 | 2026-03-30 01:25:58 | Completed |          5.03 |           520.97 |                  0    |
| WO-900287       | Preventive        | nan                  | 2026-04-28 14:00:00 | 2026-04-28 15:21:26 | Completed |          1.99 |           548.34 |                  0    |
| WO-900288       | Emergency         | coolant pump failure | 2026-04-28 06:33:00 | 2026-04-28 21:19:20 | Completed |         20.39 |          3570.54 |               1128.08 |
| WO-900289       | Emergency         | spindle bearing wear | 2026-05-05 02:57:27 | 2026-05-05 15:20:27 | Completed |         16.79 |           697.36 |               3841.78 |
| WO-900290       | Corrective        | spindle bearing wear | 2026-05-18 16:24:14 | 2026-05-18 21:15:52 | COMPLETED |          8.94 |          1506.55 |                  0    |
| WO-900291       | Preventive        | nan                  | 2026-05-28 14:00:00 | 2026-05-28 15:38:20 | Completed |          2.06 |           130.33 |                  0    |
| WO-900292       | Emergency         | spindle bearing wear | 2026-05-30 21:21:22 | 2026-05-31 08:01:28 | Completed |         14.44 |          1635.8  |               1981.89 |
| WO-900293       | Emergency         | spindle bearing wear | 2026-06-08 12:22:27 | 2026-06-09 01:37:24 | Completed |         21.08 |          5646.16 |               5407.72 |
| WO-900294       | Emergency         | spindle bearing wear | 2026-06-24 20:24:31 | 2026-06-25 10:04:39 | completed |         19.89 |          4569.25 |                  0    |
| WO-900295       | Emergency         | spindle bearing wear | 2026-06-26 06:20:06 | 2026-06-26 15:25:13 | completed |         18.48 |          4581.67 |               5871    |
| WO-900296       | Preventive        | nan                  | 2026-06-27 00:00:00 | nan                 | deferred  |          0    |             0    |                  0    |
| WO-900297       | Emergency         | tool changer fault   | 2026-06-29 07:12:56 | 2026-06-29 17:47:51 | COMPLETED |         17.91 |          5062.24 |                  0    |
| WO-900298       | Preventive        | nan                  | 2026-07-06 07:00:00 | 2026-07-06 08:10:55 | Completed |          1.29 |           599.55 |                  0    |
| WO-900299       | Emergency         | spindle bearing wear | 2026-07-07 19:26:16 | 2026-07-08 03:11:16 | completed |         10.83 |          2999.24 |              11195.2  |
| WO-900300       | Emergency         | spindle bearing wear | 2026-07-09 12:13:30 | 2026-07-10 01:39:17 | completed |         21.76 |          3628    |                  0    |
| WO-900301       | Emergency         | spindle bearing wear | 2026-07-13 09:35:57 | 2026-07-13 16:14:05 | completed |         10.05 |          5520.71 |              11428.9  |
| WO-900302       | Emergency         | spindle bearing wear | 2026-07-16 00:17:31 | 2026-07-16 12:11:24 | COMPLETED |         20.08 |           847.5  |               8754.47 |
| WO-900303       | Emergency         | spindle bearing wear | 2026-07-22 01:45:47 | 2026-07-22 08:30:35 | Completed |          8.08 |           843.47 |              10439.4  |
| WO-900304       | Emergency         | coolant pump failure | 2026-07-27 22:10:21 | 2026-07-28 06:08:33 | completed |          9.29 |          6128.79 |               7706.68 |
| WO-900305       | Emergency         | spindle bearing wear | 2026-07-28 14:24:36 | 2026-07-29 03:29:59 | completed |         18.51 |          3873.99 |               6178.17 |
| WO-900306       | Preventive        | nan                  | 2026-08-05 14:00:00 | 2026-08-05 15:53:21 | Completed |          2.78 |           479.91 |                  0    |
| WO-900307       | Emergency         | spindle bearing wear | 2026-08-12 22:38:23 | 2026-08-13 06:37:49 | Completed |         13.97 |          1488.31 |                  0    |
| WO-900308       | Emergency         | spindle bearing wear | 2026-08-15 04:47:56 | 2026-08-15 19:08:46 | Completed |         21.61 |          2274.62 |              10954.2  |
| WO-900309       | Emergency         | spindle bearing wear | 2026-08-20 20:56:40 | 2026-08-21 03:02:30 | completed |          7.67 |          5311.92 |               5994.65 |
| WO-900310       | Corrective        | spindle bearing wear | 2026-08-21 06:42:22 | 2026-08-21 10:47:15 | Completed |          6.88 |          1321.87 |               6700.5  |
| WO-900311       | Emergency         | spindle bearing wear | 2026-08-26 12:54:36 | 2026-08-27 02:06:44 | Completed |         26.64 |          4736.71 |               5606.32 |
| WO-900312       | Emergency         | spindle bearing wear | 2026-08-29 18:51:31 | 2026-08-30 07:58:40 | COMPLETED |         16.68 |          1643.42 |                  0    |
| WO-900313       | Emergency         | spindle bearing wear | 2026-09-01 11:05:15 | 2026-09-01 20:06:58 | Completed |         18.95 |          1548.68 |                  0    |
| WO-900314       | Preventive        | nan                  | 2026-09-04 00:00:00 | nan                 | DEFERRED  |          0    |             0    |                  0    |
| WO-900315       | Emergency         | tool changer fault   | 2026-09-05 19:14:40 | 2026-09-05 23:43:17 | Completed |          6.49 |          4098.07 |                  0    |
| WO-900316       | Emergency         | spindle bearing wear | 2026-09-08 02:09:31 | 2026-09-08 09:16:50 | COMPLETED |          9.02 |          5382.41 |               5283.73 |
| WO-900317       | Emergency         | spindle bearing wear | 2026-09-08 15:57:51 | 2026-09-09 01:55:45 | Completed |         14.4  |          3730.16 |               8150.35 |
| WO-900318       | Corrective        | spindle bearing wear | 2026-09-10 14:40:28 | 2026-09-10 19:14:17 | Completed |          5.06 |          1325.15 |              11487.5  |
| WO-900319       | Corrective        | spindle bearing wear | 2026-09-11 13:24:42 | 2026-09-11 17:42:40 | COMPLETED |          8.07 |          1749.25 |                  0    |
| WO-900320       | Preventive        | nan                  | 2026-09-13 14:00:00 | 2026-09-13 16:19:05 | Completed |          2.68 |            42.28 |                  0    |
| WO-900321       | Emergency         | spindle bearing wear | 2026-09-15 17:31:09 | 2026-09-15 22:40:47 | completed |          9.11 |          1173.26 |                  0    |
| WO-900322       | Emergency         | spindle bearing wear | 2026-09-18 15:24:44 | 2026-09-19 02:49:58 | COMPLETED |         23.89 |          5383.77 |              10334.2  |
| WO-900323       | Emergency         | spindle bearing wear | 2026-09-19 09:38:02 | 2026-09-19 23:36:25 | completed |         17.49 |          4125.21 |               7849.61 |

## Carrier on-time by month (carrier due date)

| mo      |   BlueLine Express |   Coastal Intermodal |   EuroSprint Cargo |   Pacific Rim Forwarding |   Rhine-Maas Transport |   Ridgeway Freight |   Summit Logistics |   TransAmerica Truckload |
|:--------|-------------------:|---------------------:|-------------------:|-------------------------:|-----------------------:|-------------------:|-------------------:|-------------------------:|
| 2025-10 |              0.989 |                0.947 |              0.929 |                    0.86  |                  0.978 |              0.794 |              0.943 |                    0.926 |
| 2025-11 |              0.969 |                0.919 |              0.926 |                    0.865 |                  0.943 |              0.69  |              0.936 |                    0.939 |
| 2025-12 |              0.972 |                0.966 |              0.957 |                    0.827 |                  0.89  |              0.751 |              0.962 |                    0.914 |
| 2026-01 |              0.967 |                0.963 |              0.946 |                    0.919 |                  0.896 |              0.801 |              0.934 |                    0.955 |
| 2026-02 |              0.993 |                0.952 |              0.952 |                    0.849 |                  0.933 |              0.785 |              0.952 |                    0.942 |
| 2026-03 |              0.969 |                0.944 |              0.92  |                    0.94  |                  0.917 |              0.795 |              0.951 |                    0.945 |
| 2026-04 |              0.982 |                0.926 |              0.913 |                    0.925 |                  0.938 |              0.817 |              0.953 |                    0.938 |
| 2026-05 |              0.962 |                0.936 |              0.955 |                    0.94  |                  0.986 |              0.82  |              0.936 |                    0.955 |
| 2026-06 |              0.958 |                0.898 |              0.902 |                    0.83  |                  0.948 |              0.798 |              0.951 |                    0.922 |
| 2026-07 |              0.96  |                0.917 |              0.921 |                    0.811 |                  0.955 |              0.737 |              0.933 |                    0.907 |
| 2026-08 |              0.981 |                0.918 |              0.846 |                    0.964 |                  0.975 |              0.724 |              0.928 |                    0.958 |
| 2026-09 |              0.992 |                0.894 |              0.897 |                    0.837 |                  0.956 |              0.733 |              0.972 |                    0.921 |

## Freight spend by carrier by month at DC-MEM (USD)

| mo      |   BlueLine Express |   Coastal Intermodal |   Ridgeway Freight |   Summit Logistics |   TransAmerica Truckload |
|:--------|-------------------:|---------------------:|-------------------:|-------------------:|-------------------------:|
| 2025-10 |              46320 |                50146 |             158404 |              53460 |                   144188 |
| 2025-11 |             104272 |                72402 |             252846 |              99206 |                   223052 |
| 2025-12 |              83290 |                77514 |             263396 |             126917 |                   222277 |
| 2026-01 |              69444 |                76385 |             272515 |             137869 |                   190245 |
| 2026-02 |              73640 |                80228 |             202371 |             107164 |                   200356 |
| 2026-03 |              62529 |                77477 |             261823 |             130290 |                   166567 |
| 2026-04 |              83450 |                83019 |             259937 |             119975 |                   238231 |
| 2026-05 |              97631 |                72087 |             273696 |             116131 |                   205163 |
| 2026-06 |              87673 |                69127 |             266048 |             128943 |                   206430 |
| 2026-07 |              94670 |                73400 |             247473 |             128244 |                   198448 |
| 2026-08 |              82249 |                72046 |             282956 |              94029 |                   232878 |
| 2026-09 |              74683 |                81651 |             193782 |             152499 |                   177888 |

## DC-MEM shipment share by carrier

| carrier_name           |   proportion |
|:-----------------------|-------------:|
| Ridgeway Freight       |        0.382 |
| TransAmerica Truckload |        0.195 |
| Summit Logistics       |        0.183 |
| BlueLine Express       |        0.126 |
| Coastal Intermodal     |        0.116 |

## Apex Agricultural Equipment (CUST-2001) OTIF by carrier & by month

| carrier_name           |   n |   on_time |   otif |
|:-----------------------|----:|----------:|-------:|
| BlueLine Express       |  77 |     0.987 |  0.961 |
| Coastal Intermodal     |  62 |     0.984 |  0.968 |
| Ridgeway Freight       | 240 |     0.917 |  0.883 |
| Summit Logistics       | 122 |     0.975 |  0.918 |
| TransAmerica Truckload | 145 |     0.986 |  0.966 |

| mo      |   n |   otif |
|:--------|----:|-------:|
| 2025-10 |  34 |  0.941 |
| 2025-11 |  59 |  0.966 |
| 2025-12 |  54 |  0.87  |
| 2026-01 |  52 |  0.981 |
| 2026-02 |  56 |  0.946 |
| 2026-03 |  61 |  0.852 |
| 2026-04 |  49 |  0.98  |
| 2026-05 |  51 |  0.922 |
| 2026-06 |  58 |  0.879 |
| 2026-07 |  46 |  0.978 |
| 2026-08 |  66 |  0.939 |
| 2026-09 |  60 |  0.883 |

## Customer OTIF by DC FY26

| ship_from_warehouse_id   |   otif |
|:-------------------------|-------:|
| DC-MEM                   |  0.919 |
| DC-RNO                   |  0.942 |
| DC-RTM                   |  0.945 |

## Stockout item-days by warehouse by quarter

| warehouse_id   |   FY26 Q1 |   FY26 Q2 |   FY26 Q3 |   FY26 Q4 |
|:---------------|----------:|----------:|----------:|----------:|
| WH-CLB         |         4 |        13 |        52 |        56 |
| WH-GVL         |         1 |        16 |        59 |        79 |
| WH-MTY         |         3 |         6 |        49 |        54 |
| WH-PNQ         |         8 |         1 |         2 |         9 |
| WH-WRO         |         7 |         9 |         8 |        10 |
