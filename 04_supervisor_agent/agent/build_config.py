"""
Build supervisor_config.yaml — the ONLY place the agent learns about KK's Parts.
===============================================================================

    demo_config.yml (supervisor section)  +  genie_space_registry (Step 3)  +  system_prompt.md
                                      ──►  supervisor_config.yaml  ──►  foreman.py

Used by 04_supervisor_agent/02_deploy_agent_app and 03_evaluate_supervisor (in a notebook, registry read with Spark)
and, for local development, by running this file directly (registry read through a SQL warehouse with your CLI profile):

    DATABRICKS_CONFIG_PROFILE=<profile> python build_config.py
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

HERE = Path(__file__).parent


def build(cfg: dict, registry: list[dict], company: str) -> dict:
    sup = cfg["supervisor"]
    prompt = (HERE / "system_prompt.md").read_text().format(
        company=company, domains=", ".join(r["title"] for r in registry),
        start_date=cfg["data"]["start_date"], end_date=cfg["data"]["end_date"])
    return {
        "router_llm": sup["router_llm"],                              # fast: which experts, what to ask them
        "answer_llm": sup["answer_llm"],                              # strong: the answer itself
        "system_prompt": prompt,
        "max_iterations": sup["max_iterations"],
        "max_tool_rounds": sup.get("max_tool_rounds", 2),             # rounds of Genie calls before Foreman must answer
        "genie_timeout_seconds": sup["genie_timeout_seconds"],
        "genie_spaces": [{k: r[k] for k in ("domain_key", "title", "space_id", "description")} for r in registry],
    }


def write(config: dict) -> Path:
    path = HERE / "supervisor_config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False, width=120))
    return path


if __name__ == "__main__":                                         # local development
    from databricks.sdk import WorkspaceClient

    root = HERE.parents[1]
    cfg = yaml.safe_load((root / "config" / "demo_config.yml").read_text())
    w = WorkspaceClient()
    wid = cfg["workspace"].get("warehouse_id") or os.environ.get("DATABRICKS_WAREHOUSE_ID") or next(
        x.id for x in w.warehouses.list() if x.name == cfg["workspace"]["warehouse_name"])
    table = f"{cfg['workspace']['catalog']}.{cfg['workspace']['schemas']['gold']}.genie_space_registry"
    res = w.statement_execution.execute_statement(warehouse_id=wid, statement=f"SELECT * FROM {table}", wait_timeout="30s")
    cols = [c.name for c in res.manifest.schema.columns]
    registry = [dict(zip(cols, row)) for row in res.result.data_array]
    print(f"wrote {write(build(cfg, registry, cfg['company']['name']))} ({len(registry)} Genie spaces)")
