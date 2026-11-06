"""One approved app note = one markdown file in its domain's notes volume — the only place a note lives.

    06_human_in_the_loop/01_sync_approved_actions   writes /Volumes/<catalog>/<landing>/app_notes_<domain>/NOTE-<id>.md
    the domain's Genie space                        has that volume attached; Agent mode searches the files

The file is what Genie reads, so everything that matters is in its TEXT: the priority line, what it is about, who
approved it and when. A small `key: value` header on top keeps the same facts machine-readable (parse()).

Priority is the human's own call when they submitted it, and it decides how much the note may change an answer:
    P1  an approved decision or override   → lead with it; it supersedes older recommendations in documents
    P2  important context                  → include it next to the numbers
    P3  FYI                                → mention only when it is directly relevant
"""
from __future__ import annotations

PRIORITY_MEANING = {"P1": "approved decision — supersedes older recommendations",
                    "P2": "important context", "P3": "for information"}

HEADER_KEYS = ("note_id", "action_id", "domain", "priority", "title", "entity_type", "entity_id", "created_by",
               "approved_by", "approved_ts", "routed_by", "routing_reason")


def render(n: dict, body: str) -> str:
    head = "\n".join(f"{k}: {str(n.get(k, '') or '').replace(chr(10), ' ')}" for k in HEADER_KEYS)
    return f"---\n{head}\n---\n\n# {n['note_id']} — {n['title']}\n\n" \
           f"**Priority {n['priority']}** ({PRIORITY_MEANING.get(n['priority'], '')})\n\n{body.strip()}\n"


def parse(text: str) -> dict:
    """Header fields + the full text. Files without a header (hand-written) still load, as P3 context."""
    out = {"note": text, "priority": "P3"}
    if text.startswith("---\n"):
        head, _, rest = text[4:].partition("\n---\n")
        out["note"] = rest.strip()                      # what Genie reads: the note itself, not the header
        for line in head.splitlines():
            k, sep, v = line.partition(": ")
            if sep and k in HEADER_KEYS:
                out[k] = v.strip()
    return out
