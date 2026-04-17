"""
Run the main.ipynb workflow in one step: fetch edition content and related
commentaries/translations, generate UCCA and gloss with the configured LLM, and
write Obsidian-ready markdown (no intermediate ``output/...`` JSON or UCCA MD).

Execute from the translation_scripts repo root (or any cwd); paths are resolved
relative to ``--project-root``.

Human/agent docs: ``skill/glossary_extraction/SKILL.md`` and ``references/``.

Example::

    python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \\
        --edition-id rs02tl3E89TH6VKVhI8bB \\
        --indices 3 \\
        --vault-topic-path \"2-authoritative-context/The Way of Boddhisattva\"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


def _repo_root() -> Path:
    scripts = Path(__file__).resolve().parent
    glossary_extraction = scripts.parent
    skill_dir = glossary_extraction.parent
    root = skill_dir.parent
    return root


def _ensure_import_path() -> Path:
    root = _repo_root()
    scripts = Path(__file__).resolve().parent
    glossary_extraction = scripts.parent
    for p in (scripts, glossary_extraction, root):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    return root


_REPO = _ensure_import_path()

import pecha_api as api  # noqa: E402
from gloss import generate_gloss  # noqa: E402
import model as model_mod  # noqa: E402
from obsidian_export import write_obsidian_gloss_ucca_direct  # noqa: E402
from segment_parser import parse_related_segments, parse_segmentations  # noqa: E402
import ucca_generator  # noqa: E402


def get_context_from_each_segment(
    edition_id: str, segment: Dict[str, Any]
) -> Tuple[Any, List[str], List[str]]:
    segment_start = segment["start"]
    segment_end = segment["end"]
    content = api.get_text_content(
        edition_id=edition_id, span_start=segment_start, span_end=segment_end
    )
    related = api.get_related_segments(
        edition_id,
        span_start=segment_start,
        span_end=segment_end,
    )
    commentaries, translations = parse_related_segments(related)
    commentaries_list = [c["text"] for c in commentaries]
    translations_list = [t["text"] for t in translations]
    return content, commentaries_list, translations_list


def run_for_edition(
    *,
    edition_id: str,
    model_name: str,
    project_root: Path,
    obsidian_subdir: str,
    vault_topic_path: str,
    segment_indices: Optional[Set[int]],
    file_stem_suffix: str,
) -> List[Dict[str, Any]]:
    router = model_mod.get_model_router()
    llm = router.get_model(model_name)

    segmentations = api.get_segmentations(edition_id)
    parsed = parse_segmentations(segmentations)
    results: List[Dict[str, Any]] = []

    for index, segment in enumerate(parsed):
        if segment_indices is not None and index not in segment_indices:
            continue

        content, commentaries_list, translations_list = get_context_from_each_segment(
            edition_id, segment
        )
        ucca = ucca_generator.generate_ucca_graph(
            model=llm,
            input_text=content,
            commentaries=commentaries_list,
            translations=translations_list,
        )
        layer3_md, pkg = ucca
        _raw_json, gloss_dict = generate_gloss(
            model=llm,
            source_text=content,
            ucca_interpretation=layer3_md,
        )

        seg_key = f"segment-{index}"
        stem = f'{segment["id"]}{file_stem_suffix}'
        written = write_obsidian_gloss_ucca_direct(
            project_root=project_root,
            vault_topic_path=vault_topic_path,
            obsidian_subdir=obsidian_subdir,
            segment_key=seg_key,
            file_stem=stem,
            gloss_data=gloss_dict,
            ucca_pkg=pkg,
        )
        results.append(
            {
                "segment_index": index,
                "segment_id": segment["id"],
                "written": {k: [str(p) for p in v] for k, v in written.items()},
            }
        )

    return results


def _parse_indices(spec: Optional[str]) -> Optional[Set[int]]:
    if spec is None or not str(spec).strip():
        return None
    out: Set[int] = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Pecha edition to UCCA and gloss, then Obsidian markdown (direct).",
    )
    p.add_argument("--edition-id", required=True, help="Edition UUID on the Pecha API.")
    p.add_argument(
        "--indices",
        default=None,
        help="Comma-separated 0-based segment indices to process (default: all).",
    )
    p.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repo or vault parent directory (default: cwd).",
    )
    p.add_argument(
        "--obsidian-subdir",
        default="obsidian",
        help="Directory under project-root where the vault tree is written.",
    )
    p.add_argument(
        "--vault-topic-path",
        default="2-authoritative-context/The Way of Boddhisattva",
        help="Topic folder inside the obsidian vault (forward slashes).",
    )
    p.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Model name accepted by the project model router.",
    )
    p.add_argument(
        "--stem-suffix",
        default="-full",
        help="Suffix after segment id for note filenames (notebook used '-full').",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse segmentations and print chosen indices only; no API/LLM calls.",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    project_root = args.project_root.resolve()
    indices = _parse_indices(args.indices)

    if args.dry_run:
        segmentations = api.get_segmentations(args.edition_id)
        parsed = parse_segmentations(segmentations)
        chosen = [
            (i, seg["id"])
            for i, seg in enumerate(parsed)
            if indices is None or i in indices
        ]
        print(json.dumps({"segments": chosen}, indent=2))
        return 0

    out = run_for_edition(
        edition_id=args.edition_id,
        model_name=args.model,
        project_root=project_root,
        obsidian_subdir=args.obsidian_subdir,
        vault_topic_path=args.vault_topic_path,
        segment_indices=indices,
        file_stem_suffix=args.stem_suffix,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
