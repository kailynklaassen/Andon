# Databricks notebook source
# MAGIC %md
# MAGIC # Step 1b · Publish the domain documents (unstructured data) for Genie
# MAGIC
# MAGIC **What this does:** renders the 40 markdown documents in [`documents/`](./documents) to PDF and writes them to the
# MAGIC **one Unity Catalog volume per Genie space** (Genie builds one document index per volume):
# MAGIC
# MAGIC ```
# MAGIC /Volumes/<catalog>/mfg_landing/
# MAGIC   genie_docs_production/     SOPs, scheduling policy, process-flow reference, ops reviews, line-stop reports
# MAGIC   genie_docs_quality/        NCR & CAPA procedures, supplier quality agreement, SCAR, 8D, control plans
# MAGIC   genie_docs_maintenance/    OEM service manual, PM procedure, RCA, field service report, MOC, policies
# MAGIC   genie_docs_supply_chain/   supplier & carrier contracts, scorecard, escalation letter, SOPs, S&OP minutes
# MAGIC ```
# MAGIC
# MAGIC **Why this replaces the Knowledge Assistant:** Genie spaces can now answer from attached documents *alongside* SQL.
# MAGIC Each space gets only its own domain's documents, so "what does the OEM manual say the vibration limit is?" and
# MAGIC "what is GVL-L3-WC01's vibration this month?" are answered by the same Maintenance space — no separate RAG agent.
# MAGIC
# MAGIC Every number in these documents matches the generated data (see `documents/NARRATIVE_BIBLE.md` and
# MAGIC `documents/DATA_FACTS.md`), so document answers and SQL answers agree.
# MAGIC
# MAGIC ➡️ Step 3 attaches each folder to its Genie space via the API (needs the Volume Index preview — see Step 3b).

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC Most of the *why* in operations lives in documents (manuals, SOPs, contracts, root-cause reports), not tables. An agent that can only run SQL can say *what* happened but not *why* or *what the procedure says*.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Documents that agree with the data (same IDs, dates, numbers) — otherwise the agent gets contradictory evidence.
# MAGIC * One volume per Genie space, so each domain's documents stay in that domain's governance boundary.
# MAGIC
# MAGIC **Optional**
# MAGIC * The PDF styling; the number of documents.

# COMMAND ----------

# MAGIC %pip install -q markdown xhtml2pdf
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, os, markdown
from xhtml2pdf import pisa

SRC = f"{REPO_ROOT}/01_data_generation/documents"
CSS = """
@page { size: letter; margin: 2cm 1.8cm 2cm 1.8cm;
        @frame footer { -pdf-frame-content: footer; bottom: 0.8cm; margin-left: 1.8cm; margin-right: 1.8cm; height: 1cm; } }
body { font-family: Helvetica; font-size: 9.5pt; line-height: 1.35; color: #1f2933; }
h1 { font-size: 17pt; color: #0b3d5c; border-bottom: 2px solid #0b3d5c; padding-bottom: 4px; }
h2 { font-size: 12.5pt; color: #0b3d5c; margin-top: 14px; }
h3 { font-size: 10.5pt; color: #24577a; }
table { border: 0.5px solid #9aa5b1; margin: 6px 0; }
th { background-color: #e4ecf2; font-weight: bold; padding: 3px; border: 0.5px solid #9aa5b1; }
td { padding: 3px; border: 0.5px solid #cbd2d9; vertical-align: top; }
code { font-family: Courier; font-size: 8.5pt; }
.brand { font-size: 8pt; color: #7b8794; }
"""

def render(md_path: str, pdf_path: str) -> None:
    body = markdown.markdown(open(md_path).read(), extensions=["tables", "fenced_code", "sane_lists"])
    doc_id = os.path.basename(md_path).split("_")[0]
    html = f"""<html><head><style>{CSS}</style></head><body>
      <div class="brand">{COMPANY} · Internal document · {doc_id}</div>{body}
      <div id="footer" class="brand">{COMPANY} — {doc_id} — synthetic demo document</div></body></html>"""
    with open(pdf_path, "wb") as out:
        result = pisa.CreatePDF(html, dest=out)
    if result.err:
        raise RuntimeError(f"PDF render failed for {md_path}")

ensure_uc_objects()
written = []
for space in CFG["genie"]["spaces"]:
    folder = space["docs_folder"]
    dest = docs_path(folder)
    os.makedirs(dest, exist_ok=True)
    for md in sorted(glob.glob(f"{SRC}/{folder}/*.md")):
        if os.path.basename(md).startswith("_"):          # _eval_questions.md is for testing, not for Genie
            continue
        pdf = f"{dest}/{os.path.basename(md)[:-3]}.pdf"
        render(md, pdf)
        written.append((folder, os.path.basename(pdf), os.path.getsize(pdf)))
    print(f"✅ {folder:<13} {sum(1 for w in written if w[0] == folder)} PDFs → {dest}")

display(spark.createDataFrame(written, "genie_space STRING, file STRING, bytes LONG"))
