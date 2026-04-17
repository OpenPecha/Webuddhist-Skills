"""
Render Layer 3 — Syntactic (UCCA) as Markdown from ``UCCASyntacticPackage``.

Used by ``ucca_generator`` (for saved notes and gloss context) and ``obsidian_export``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from models.ucca import UCCASyntacticPackage, UCCATreeNode

_UCCA_LABEL_REFERENCE = """**UCCA label set**

| Label | Full name | Label | Full name |
| --- | --- | --- | --- |
| H | Scene | E | Elaborator |
| P | Process | N | Connector |
| A | Participant | T | Terminus |
| D | Adverbial | Q | Quantifier |
| R | Relator | L | Linker |
| F | Function | C | Center |
| G | Ground | | |
"""


def _escape_table_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def render_ucca_ascii_tree(root: UCCATreeNode) -> str:
    lines: List[str] = [f"{root.label}: {root.full_name}"]
    children = root.children
    for i, child in enumerate(children):
        lines.extend(_render_tree_child(child, "", i == len(children) - 1))
    if root.leaf_tokens and not children:
        lines.append(f"└── {root.leaf_tokens.strip()}")
    return "\n".join(lines)


def _render_tree_child(node: UCCATreeNode, prefix: str, is_last: bool) -> List[str]:
    branch = "└── " if is_last else "├── "
    lines: List[str] = [f"{prefix}{branch}{node.label}: {node.full_name}"]
    ext = "    " if is_last else "│   "
    new_prefix = prefix + ext
    subs = node.children
    if node.leaf_tokens and not subs:
        lines.append(f"{new_prefix}└── {node.leaf_tokens.strip()}")
    else:
        for i, s in enumerate(subs):
            lines.extend(_render_tree_child(s, new_prefix, i == len(subs) - 1))
        if node.leaf_tokens and subs:
            lines.append(f"{new_prefix}└── {node.leaf_tokens.strip()}")
    return lines


def render_layer3_markdown(pkg: UCCASyntacticPackage, *, include_label_reference: bool = True) -> str:
    parts: List[str] = [
        "## Layer 3 — Syntactic (UCCA)\n\n",
        "**Tree**\n",
        render_ucca_ascii_tree(pkg.tree),
        "\n\n",
        "**Node Key**\n\n",
        "| Node | Label | Tokens | Commentary basis |\n",
        "| --- | --- | --- | --- |\n",
    ]
    for row in pkg.node_key:
        parts.append(
            f"| {_escape_table_cell(row.node)} | {_escape_table_cell(row.label)} | "
            f"{_escape_table_cell(row.tokens)} | {_escape_table_cell(row.commentary_basis)} |\n"
        )
    if include_label_reference:
        parts.append("\n")
        parts.append(_UCCA_LABEL_REFERENCE)
    if pkg.divergence and pkg.divergence.strip():
        parts.append("\n## UCCA Divergence\n\n")
        parts.append(pkg.divergence.strip())
        parts.append("\n")
    return "".join(parts).rstrip() + "\n"


def ucca_syntactic_package_to_full_note(
    pkg: UCCASyntacticPackage,
    *,
    frontmatter_lines: List[str],
    title_line: str,
    gloss_wikilink: str = "",
) -> str:
    """Full Obsidian note: YAML frontmatter, title, optional gloss link, Layer 3 body."""
    fm_body = "\n".join(frontmatter_lines)
    header = f"---\n{fm_body}\n---\n\n"
    parts: List[str] = [header, title_line.rstrip("\n") + "\n\n"]
    if gloss_wikilink.strip():
        parts.append(f"→ [[{gloss_wikilink}|Gloss]]\n\n")
    parts.append(render_layer3_markdown(pkg))
    return "".join(parts).rstrip() + "\n"


def ucca_data_to_package(data: Dict[str, Any]) -> Optional[UCCASyntacticPackage]:
    """If ``data`` is a syntactic package dict, parse it; otherwise return None."""
    if not isinstance(data, dict):
        return None
    if "tree" in data and "node_key" in data:
        try:
            return UCCASyntacticPackage.model_validate(data)
        except Exception:
            return None
    return None
