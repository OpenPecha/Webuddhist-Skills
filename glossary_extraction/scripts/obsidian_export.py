"""
Export gloss and UCCA outputs to Markdown for Obsidian.

Reads ``output/segment-*/gloss/*.json`` and UCCA from
``output/segment-*/ucca/*.md`` (preferred) or legacy ``*.json``.
Writes one ``.md`` per stem under
``obsidian/<vault_topic_path>/<segment>/gloss/<stem>.md`` and
``.../<segment>/ucca/<stem>.md``. Wikilinks pair files with the same basename when
both sides exist. Cross-links use vault-relative paths (forward slashes, no ``.md``).

Gloss JSON with ``Glossary.gla``, ``glb``, ``glc``, and ``free_translation`` is rendered
as **Layer 4 — Semantic Gloss**: a ``gloss`` code block for the Obsidian **Interlinear
Glossing** (ling-gloss) plugin, optional ``**Source:**``, and ``## Gloss Divergences``
when ``divergences`` is set. Legacy bullet ``glossary`` strings are still supported when
interlinear fields are absent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from models.ucca import UCCASyntacticPackage
from ucca_format import ucca_data_to_package, ucca_syntactic_package_to_full_note

_SOURCE_FM = "source: translation_scripts"

# ling-gloss (Obsidian Interlinear Glossing) uses \ft for the free-translation line.
_LING_GLOSS_FT = "\\ft"


def _interlinear_gloss_body(g: Dict[str, Any]) -> str | None:
    """Build ```gloss ... ``` body if gla, glb, glc, and free_translation are all non-empty."""
    gla = (g.get("gla") or "").strip()
    glb = (g.get("glb") or "").strip()
    glc = (g.get("glc") or "").strip()
    ft = (g.get("free_translation") or "").strip()
    if not (gla and glb and glc and ft):
        return None
    return (
        "```gloss\n"
        f"\\gla {gla}\n"
        f"\\glb {glb}\n"
        f"\\glc {glc}\n"
        f"{_LING_GLOSS_FT} {ft}\n"
        "```\n"
    )


def _frontmatter(lines: List[str]) -> str:
    body = "\n".join(lines)
    return f"---\n{body}\n---\n\n"


def _norm_vault_path(path: str) -> str:
    return "/".join(p for p in path.replace("\\", "/").split("/") if p)


def obsidian_wikilink_target(
    vault_topic_path: str,
    segment: str,
    *path_parts: str,
) -> str:
    """Vault-root path for ``[[...]]`` (no ``.md``), using forward slashes."""
    base = _norm_vault_path(vault_topic_path)
    rest = "/".join(_norm_vault_path(p) for p in path_parts if p)
    return f"{base}/{segment}/{rest}" if rest else f"{base}/{segment}"


def segment_base_dir(out_dir: Path, vault_topic_path: str, segment: str) -> Path:
    """``out_dir / <vault_topic_path> / <segment>`` as a single Path."""
    topic_parts = [out_dir, *_norm_vault_path(vault_topic_path).split("/"), segment]
    return Path(*topic_parts)


def segment_hub_path(out_dir: Path, vault_topic_path: str, segment: str) -> Path:
    """Segment index note: ``.../<topic>/<segment>/{segment}.md``."""
    return segment_base_dir(out_dir, vault_topic_path, segment) / f"{segment}.md"


def gloss_json_to_markdown(
    data: Dict[str, Any],
    segment: str,
    ucca_note: str,
    *,
    file_stem: str = "",
) -> str:
    """Build Obsidian-ready Markdown from a gloss JSON object."""
    parts: List[str] = []
    fm_lines = [
        _SOURCE_FM,
        "kind: gloss",
        f"segment: {segment}",
    ]
    if file_stem:
        fm_lines.append(f"source_file: {file_stem}")
    fm = _frontmatter(fm_lines)
    parts.append(fm)
    title = f"# Gloss — {segment} — {file_stem}\n\n" if file_stem else f"# Gloss — {segment}\n\n"
    parts.append(title)
    if ucca_note.strip():
        parts.append(f"→ [[{ucca_note}|UCCA]]\n\n")

    g = data.get("Glossary") or {}
    inter = _interlinear_gloss_body(g)
    if inter:
        parts.append("## Layer 4 — Semantic Gloss\n\n")
        parts.append(inter)
        src = (g.get("source_citation") or "").strip()
        if src:
            parts.append(f"\n**Source:** ({src})\n\n")
        div = (g.get("divergences") or "").strip()
        if div:
            parts.append("## Gloss Divergences\n\n")
            parts.append(f"{div}\n\n")
    else:
        glossary_raw = (g.get("glossary") or "").strip()
        if glossary_raw:
            parts.append("## Glossary\n\n")
            for line in glossary_raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("- "):
                    parts.append(f"{line}\n")
                else:
                    parts.append(f"- {line}\n")
            parts.append("\n")

    st = data.get("StandardizedText") or {}
    std_text = (st.get("standardized_text") or "").strip()
    note = (st.get("note") or "").strip()
    if std_text or note:
        parts.append("## Standardized text\n\n")
        if std_text:
            parts.append(f"{std_text}\n\n")
        if note:
            parts.append(f"{note}\n\n")

    analysis = data.get("analysis") or []
    if analysis:
        parts.append("## Term analysis\n\n")
        for item in analysis:
            term = (item.get("term") or "").strip()
            disc = item.get("discrepancyFound")
            details = (item.get("details") or "").strip()
            flag = " (discrepancy)" if disc else ""
            parts.append(f"### `{term}`{flag}\n\n")
            if details:
                parts.append(f"{details}\n\n")

    return "".join(parts).rstrip() + "\n"


def _ucca_render_subtree(
    node_id: str,
    by_id: Dict[str, Dict[str, Any]],
    depth: int,
) -> List[str]:
    lines: List[str] = []
    node = by_id.get(node_id)
    if not node:
        return lines
    indent = "  " * depth
    ntype = (node.get("type") or "").strip()
    desc = (node.get("descriptor") or "").strip()
    head = f"{indent}- **{ntype}** (`{node.get('id', '')}`)"
    if desc:
        head += f" — {desc}"
    lines.append(head + "\n")

    sub = indent + "  "
    text_bo = (node.get("text") or "").strip()
    if text_bo:
        lines.append(f"{sub}- **Tibetan:** {text_bo}\n")
    text_en = (node.get("english_text") or "").strip()
    if text_en:
        lines.append(f"{sub}- **English:** {text_en}\n")
    implicit = (node.get("implicit") or "").strip()
    if implicit:
        lines.append(f"{sub}- **Implicit:** {implicit}\n")

    for cid in node.get("children") or []:
        lines.extend(_ucca_render_subtree(cid, by_id, depth + 1))
    return lines


def ucca_json_to_markdown(
    data: Dict[str, Any],
    segment: str,
    gloss_note: str,
    *,
    file_stem: str = "",
) -> str:
    """Build Obsidian-ready Markdown from UCCA JSON (syntactic package or legacy graph)."""
    pkg = ucca_data_to_package(data)
    if pkg is not None:
        fm_lines = [
            _SOURCE_FM,
            "kind: ucca",
            f"segment: {segment}",
        ]
        if file_stem:
            fm_lines.append(f"source_file: {file_stem}")
        if pkg.syntactic_unit:
            fm_lines.append("syntactic_unit:")
            for u in pkg.syntactic_unit:
                fm_lines.append(f"  - {u}")
        title = (
            f"# UCCA — {segment} — {file_stem}\n\n"
            if file_stem
            else f"# UCCA — {segment}\n\n"
        )
        return ucca_syntactic_package_to_full_note(
            pkg,
            frontmatter_lines=fm_lines,
            title_line=title,
            gloss_wikilink=gloss_note,
        )

    nodes = data.get("nodes") or []
    by_id: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes if isinstance(n, dict) and n.get("id")}
    root_id = (data.get("root_id") or "").strip()
    if not root_id and by_id:
        roots = [nid for nid, n in by_id.items() if not (n.get("parent_id") or "").strip()]
        root_id = roots[0] if len(roots) == 1 else ""

    parts: List[str] = []
    fm_lines = [
        _SOURCE_FM,
        "kind: ucca",
        f"segment: {segment}",
    ]
    if file_stem:
        fm_lines.append(f"source_file: {file_stem}")
    fm = _frontmatter(fm_lines)
    parts.append(fm)
    title = f"# UCCA — {segment} — {file_stem}\n\n" if file_stem else f"# UCCA — {segment}\n\n"
    parts.append(title)
    if gloss_note.strip():
        parts.append(f"→ [[{gloss_note}|Gloss]]\n\n")

    if root_id and root_id in by_id:
        parts.append("## Structure\n\n")
        parts.extend(_ucca_render_subtree(root_id, by_id, 0))
        parts.append("\n")
    elif nodes:
        parts.append("## Structure\n\n")
        parts.append("_No root_id or hierarchy could be inferred; listing nodes._\n\n")
        for n in nodes:
            if not isinstance(n, dict):
                continue
            parts.append(f"- **`{n.get('id', '')}`** {n.get('type', '')} — {n.get('descriptor', '')}\n")

    return "".join(parts).rstrip() + "\n"


def hub_markdown_multi(
    segment: str,
    gloss_items: List[tuple[str, str]],
    ucca_items: List[tuple[str, str]],
) -> str:
    """Build hub note with lists of wikilinks ``(target, label)``."""
    fm = _frontmatter(
        [
            _SOURCE_FM,
            "kind: segment",
            f"segment: {segment}",
        ]
    )
    parts: List[str] = [fm, f"# Segment — {segment}\n\n"]
    if gloss_items:
        parts.append("## Gloss\n\n")
        for target, label in gloss_items:
            parts.append(f"- [[{target}|{label}]]\n")
        parts.append("\n")
    if ucca_items:
        parts.append("## UCCA\n\n")
        for target, label in ucca_items:
            parts.append(f"- [[{target}|{label}]]\n")
        parts.append("\n")
    return "".join(parts).rstrip() + "\n"


def hub_markdown(segment: str, gloss_wikilink: str, ucca_wikilink: str) -> str:
    """Single-pair hub; prefer :func:`hub_markdown_multi` when there are many files."""
    return hub_markdown_multi(
        segment,
        [(gloss_wikilink, "Gloss")],
        [(ucca_wikilink, "UCCA")],
    )


def _list_json_files(dir_path: Path) -> List[Path]:
    if not dir_path.is_dir():
        return []
    return sorted(dir_path.glob("*.json"))


def _ucca_sources_by_stem(ucca_dir: Path) -> Dict[str, Path]:
    """Prefer ``.md`` over ``.json`` when both exist for the same stem."""
    by_stem: Dict[str, Path] = {}
    if not ucca_dir.is_dir():
        return by_stem
    for p in sorted(ucca_dir.glob("*.json")):
        by_stem.setdefault(p.stem, p)
    for p in sorted(ucca_dir.glob("*.md")):
        by_stem[p.stem] = p
    return by_stem


_GLOSS_LINK_RE = re.compile(r"→ \[\[[^\]]+\|Gloss\]\]\s*\n\s*\n", re.MULTILINE)


def _replace_yaml_frontmatter(content: str, new_frontmatter_block: str) -> str:
    """``new_frontmatter_block`` is a full ``---\\n...\\n---\\n\\n`` string."""
    c = content.lstrip("\ufeff")
    if c.startswith("---"):
        idx = c.find("\n---", 3)
        if idx != -1:
            rest = c[idx + 4 :].lstrip("\n")
            return new_frontmatter_block + rest
    return new_frontmatter_block + c


def ucca_note_export_refresh(
    md_content: str,
    segment: str,
    gloss_wikilink: str,
    *,
    file_stem: str = "",
) -> str:
    """Rebuild YAML frontmatter and Gloss wikilink; keep the rest of a UCCA ``.md`` note."""
    fm_lines = [
        _SOURCE_FM,
        "kind: ucca",
        f"segment: {segment}",
    ]
    if file_stem:
        fm_lines.append(f"source_file: {file_stem}")
    new_fm = _frontmatter(fm_lines)
    body = _replace_yaml_frontmatter(md_content, new_fm)
    if gloss_wikilink.strip():
        link = f"→ [[{gloss_wikilink}|Gloss]]\n\n"
        if _GLOSS_LINK_RE.search(body):
            body = _GLOSS_LINK_RE.sub(link, body, count=1)
        else:
            # Insert after first heading block
            m = re.search(r"^(# [^\n]+\n\n)", body)
            if m:
                insert_at = m.end()
                body = body[:insert_at] + link + body[insert_at:]
            else:
                body = link + body
    else:
        body = _GLOSS_LINK_RE.sub("", body, count=1)
    return body.rstrip() + "\n"


def _iter_segment_dirs(output_root: Path) -> List[tuple[str, Path]]:
    """``(segment_name, path)`` for each ``segment-*`` directory under ``output_root``."""
    if not output_root.is_dir():
        return []
    pairs: List[tuple[str, Path]] = []
    for p in sorted(output_root.iterdir()):
        if p.is_dir() and p.name.startswith("segment-"):
            pairs.append((p.name, p))
    return pairs


def export_to_obsidian(
    project_root: Path | str,
    *,
    output_subdir: str = "output",
    obsidian_subdir: str = "obsidian",
    vault_topic_path: str = "2-authoritative-context/the way of budhisattva",
) -> Dict[str, List[Path]]:
    """
    Read JSON from ``output_subdir/segment-*/gloss/*.json`` and UCCA from
    ``.../ucca/*.md`` (preferred) or legacy ``.../ucca/*.json``.

    For each gloss ``<stem>.json`` / UCCA ``<stem>.md`` (or ``.json``), writes
    ``obsidian_subdir/<vault_topic_path>/<segment>/gloss/<stem>.md`` or
    ``.../ucca/<stem>.md``. A gloss note links to the UCCA note with the same
    ``<stem>`` when it exists; otherwise to the first UCCA note in that segment
    (if any). The same rule applies in reverse for UCCA → gloss.

    Writes ``<segment>/<segment>.md`` when the segment has at least one gloss or
    UCCA note, listing all generated links.

    Wikilinks use vault-relative paths (forward slashes, no ``.md``). Open
    ``obsidian_subdir`` as the vault root (or merge that tree into your vault).

    Returns a dict with keys ``gloss``, ``ucca``, ``hub`` listing written paths.
    """
    root = Path(project_root).resolve()
    output_root = root / output_subdir
    out_dir = root / obsidian_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    written_gloss: List[Path] = []
    written_ucca: List[Path] = []
    written_hub: List[Path] = []

    for seg, seg_dir in _iter_segment_dirs(output_root):
        gloss_dir = seg_dir / "gloss"
        ucca_dir = seg_dir / "ucca"
        gloss_files = _list_json_files(gloss_dir)
        ucca_by_stem = _ucca_sources_by_stem(ucca_dir)

        gloss_stems = {p.stem for p in gloss_files}
        ucca_stems = set(ucca_by_stem.keys())
        first_gloss_stem = gloss_files[0].stem if gloss_files else ""
        ucca_stems_sorted = sorted(ucca_by_stem.keys())
        first_ucca_stem = ucca_stems_sorted[0] if ucca_stems_sorted else ""

        base = segment_base_dir(out_dir, vault_topic_path, seg)
        gloss_items: List[tuple[str, str]] = []
        ucca_items: List[tuple[str, str]] = []

        for gp in gloss_files:
            stem = gp.stem
            pair_ucca = stem if stem in ucca_stems else first_ucca_stem
            ucca_wikilink = (
                obsidian_wikilink_target(vault_topic_path, seg, "ucca", pair_ucca)
                if pair_ucca
                else ""
            )
            dest = base / "gloss" / f"{stem}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(gp, encoding="utf-8") as f:
                gloss_data = json.load(f)
            md = gloss_json_to_markdown(
                gloss_data, seg, ucca_wikilink, file_stem=stem
            )
            dest.write_text(md, encoding="utf-8")
            written_gloss.append(dest)
            gloss_wl = obsidian_wikilink_target(vault_topic_path, seg, "gloss", stem)
            gloss_items.append((gloss_wl, stem))

        for stem in ucca_stems_sorted:
            up = ucca_by_stem[stem]
            pair_gloss = stem if stem in gloss_stems else first_gloss_stem
            gloss_wikilink = (
                obsidian_wikilink_target(vault_topic_path, seg, "gloss", pair_gloss)
                if pair_gloss
                else ""
            )
            dest = base / "ucca" / f"{stem}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if up.suffix.lower() == ".md":
                md_content = up.read_text(encoding="utf-8")
                md = ucca_note_export_refresh(
                    md_content, seg, gloss_wikilink, file_stem=stem
                )
            else:
                with open(up, encoding="utf-8") as f:
                    ucca_data = json.load(f)
                md = ucca_json_to_markdown(
                    ucca_data, seg, gloss_wikilink, file_stem=stem
                )
            dest.write_text(md, encoding="utf-8")
            written_ucca.append(dest)
            ucca_wl = obsidian_wikilink_target(vault_topic_path, seg, "ucca", stem)
            ucca_items.append((ucca_wl, stem))

        if gloss_items or ucca_items:
            hub_path = segment_hub_path(out_dir, vault_topic_path, seg)
            hub_path.parent.mkdir(parents=True, exist_ok=True)
            hub_path.write_text(
                hub_markdown_multi(seg, gloss_items, ucca_items),
                encoding="utf-8",
            )
            written_hub.append(hub_path)

    return {"gloss": written_gloss, "ucca": written_ucca, "hub": written_hub}


def _md_stems(dir_path: Path) -> List[str]:
    if not dir_path.is_dir():
        return []
    return sorted({p.stem for p in dir_path.glob("*.md")})


def write_obsidian_gloss_ucca_direct(
    *,
    project_root: Path | str,
    vault_topic_path: str,
    obsidian_subdir: str = "obsidian",
    segment_key: str,
    file_stem: str,
    gloss_data: Dict[str, Any],
    ucca_pkg: UCCASyntacticPackage,
) -> Dict[str, List[Path]]:
    """
    Write one gloss note, one UCCA note, and refresh the segment hub under
    ``<project_root>/<obsidian_subdir>/<vault_topic_path>/<segment_key>/`` without
    using intermediate ``output/.../gloss/*.json`` or ``output/.../ucca/*.md``.

    The hub lists all ``*.md`` stems present under that segment's ``gloss/`` and
    ``ucca/`` directories after this write (so repeated runs accumulate links).
    """
    root = Path(project_root).resolve()
    out_dir = root / obsidian_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    base = segment_base_dir(out_dir, vault_topic_path, segment_key)
    gloss_dir = base / "gloss"
    ucca_dir = base / "ucca"
    gloss_dir.mkdir(parents=True, exist_ok=True)
    ucca_dir.mkdir(parents=True, exist_ok=True)

    ucca_wl = obsidian_wikilink_target(vault_topic_path, segment_key, "ucca", file_stem)
    gloss_path = gloss_dir / f"{file_stem}.md"
    gloss_md = gloss_json_to_markdown(
        gloss_data, segment_key, ucca_wl, file_stem=file_stem
    )
    gloss_path.write_text(gloss_md, encoding="utf-8")

    gloss_wl = obsidian_wikilink_target(vault_topic_path, segment_key, "gloss", file_stem)
    fm_lines = [
        _SOURCE_FM,
        "kind: ucca",
        f"segment: {segment_key}",
        f"source_file: {file_stem}",
    ]
    if ucca_pkg.syntactic_unit:
        fm_lines.append("syntactic_unit:")
        for u in ucca_pkg.syntactic_unit:
            fm_lines.append(f"  - {u}")
    title = f"# UCCA — {segment_key} — {file_stem}\n\n"
    ucca_md = ucca_syntactic_package_to_full_note(
        ucca_pkg,
        frontmatter_lines=fm_lines,
        title_line=title,
        gloss_wikilink=gloss_wl,
    )
    ucca_path = ucca_dir / f"{file_stem}.md"
    ucca_path.write_text(ucca_md, encoding="utf-8")

    gloss_items: List[tuple[str, str]] = [
        (obsidian_wikilink_target(vault_topic_path, segment_key, "gloss", s), s)
        for s in _md_stems(gloss_dir)
    ]
    ucca_items: List[tuple[str, str]] = [
        (obsidian_wikilink_target(vault_topic_path, segment_key, "ucca", s), s)
        for s in _md_stems(ucca_dir)
    ]
    hub_path = segment_hub_path(out_dir, vault_topic_path, segment_key)
    hub_path.parent.mkdir(parents=True, exist_ok=True)
    hub_path.write_text(
        hub_markdown_multi(segment_key, gloss_items, ucca_items),
        encoding="utf-8",
    )

    return {
        "gloss": [gloss_path],
        "ucca": [ucca_path],
        "hub": [hub_path],
    }
