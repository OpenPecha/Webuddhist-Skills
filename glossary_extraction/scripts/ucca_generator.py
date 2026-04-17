import json
import logging
from typing import Tuple, Optional, AsyncGenerator, List, Dict, Any, Sequence, Union

from langchain_core.language_models import BaseChatModel
from datetime import datetime

from models.ucca import UCCASyntacticPackage
from ucca_format import render_layer3_markdown


logger = logging.getLogger("translation_api.ucca")


UCCA_SYNTACTIC_SCHEMA_JSON = json.dumps(UCCASyntacticPackage.model_json_schema(), indent=2)


UCCA_PROMPT_TEMPLATE = """
You are an expert in UCCA (Universal Conceptual Cognitive Annotation) syntactic layer annotation.
Your task is to parse the given input text and produce a **syntactic package** matching the
Layer 3 — Syntactic (UCCA) format used in translation notes.

The output MUST be a single JSON object conforming to this Pydantic schema:

{UCCA_SYNTACTIC_SCHEMA_JSON}

**Tree rules (ASCII tree)**
- The `tree` field is the root `UCCATreeNode` (typically label "H", full_name "Scene").
- Branch lines in the rendered tree are `Label: FullName` (e.g. `H: Scene`, `A: Participant`).
- Leaf lines are space-separated tokens on a child line under their branch (field `leaf_tokens`
  when that branch has no `children`).
- Multi-word phrases stay on one leaf line.
- Use Roman transliteration for leaf tokens: **IAST** for Sanskrit; **Wylie** for Tibetan when
  no Sanskrit parallel is given. Do not use Devanāgarī or Tibetan script in leaf lines.
- **Sanskrit compounds**: one leaf token unless commentary breaks the compound; then use nested
  `children` under that branch for members.
- If a syntactic unit spans multiple verses, set `syntactic_unit` to a list of verse/unit labels
  (e.g. verse ids); the tree should cover the full span.
- If commentaries support a clearly different tree, fill `divergence` with the alternative tree
  (ASCII), explanation, and mark key points with ⚑. The renderer will add the section heading.

**Node Key table (`node_key`)**
- One row per salient node (at least every branch in the tree; include leaves as needed for clarity).
- `node`: short id (usually the letter: H, A, P, …).
- `label`: full category name (Scene, Participant, …).
- `tokens`: the token span for that row (Roman transliteration).Tokens in IAST (Sanskrit), Romanised Pāli (Pāli), Wylie (Tibetan) — not source scripts
- `commentary_basis`: where this node is supported (e.g. a vault path with block anchor like
  `(1-Human-Sources/.../file.md#^id)`). Use the best citation you can infer from the supplied
  commentaries; if none, write `(inferred from primary text)`.

**Input text** may be Tibetan with optional English, Sanskrit parallel, etc.

Input Text:
{input_text}

Optional Contexts (may be empty):
{optional_contexts}

Return ONLY valid JSON (no markdown fences or commentary).
"""


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json") :]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```") :]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
    return cleaned.strip()


def _nonempty_strings(seq: Optional[Sequence[Union[str, None]]]) -> List[str]:
    if not seq:
        return []
    out: List[str] = []
    for x in seq:
        if x is None:
            continue
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def _build_optional_contexts(
    commentaries: Optional[Sequence[Union[str, None]]] = None,
    translations: Optional[Sequence[Union[str, None]]] = None,
) -> str:
    lines: List[str] = []
    for i, c in enumerate(_nonempty_strings(commentaries), start=1):
        lines.append(f"- Commentary {i}: {c}")
    for i, t in enumerate(_nonempty_strings(translations), start=1):
        lines.append(f"- Translation / parallel {i}: {t}")
    if not lines:
        return "(none provided)"
    return "\n".join(lines)


def _format_prompt(
    input_text: str,
    commentaries: Optional[Sequence[Union[str, None]]] = None,
    translations: Optional[Sequence[Union[str, None]]] = None,
) -> str:
    optional_contexts = _build_optional_contexts(commentaries, translations)
    return UCCA_PROMPT_TEMPLATE.format(
        input_text=input_text,
        UCCA_SYNTACTIC_SCHEMA_JSON=UCCA_SYNTACTIC_SCHEMA_JSON,
        optional_contexts=optional_contexts,
    )


def _merge_commentaries(
    commentaries: Optional[Sequence[Union[str, None]]],
    commentary_1: Optional[str],
    commentary_2: Optional[str],
    commentary_3: Optional[str],
) -> List[str]:
    if commentaries is not None:
        return _nonempty_strings(commentaries)
    return _nonempty_strings([commentary_1, commentary_2, commentary_3])


def _merge_translations(
    translations: Optional[Sequence[Union[str, None]]],
    sanskrit_text: Optional[str],
) -> List[str]:
    if translations is not None:
        return _nonempty_strings(translations)
    return _nonempty_strings([sanskrit_text] if sanskrit_text else [])


def _context_from_item(it: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    if it.get("commentaries") is not None:
        comms = _nonempty_strings(it["commentaries"])
    else:
        comms = _nonempty_strings(
            [it.get("commentary_1"), it.get("commentary_2"), it.get("commentary_3")]
        )
    if it.get("translations") is not None:
        trans = _nonempty_strings(it["translations"])
    else:
        trans = _merge_translations(None, it.get("sanskrit_text"))
    return comms, trans


def generate_ucca_graph(
    model: BaseChatModel,
    input_text: str,
    commentaries: Optional[Sequence[Union[str, None]]] = None,
    translations: Optional[Sequence[Union[str, None]]] = None,
    commentary_1: Optional[str] = None,
    commentary_2: Optional[str] = None,
    commentary_3: Optional[str] = None,
    sanskrit_text: Optional[str] = None,
) -> Tuple[str, UCCASyntacticPackage]:
    """
    Returns ``(layer3_markdown, package)``. The markdown string is suitable for gloss prompts
    and for inspection; persist a full vault note with :func:`ucca_format.ucca_syntactic_package_to_full_note`.
    """
    comms = _merge_commentaries(commentaries, commentary_1, commentary_2, commentary_3)
    trans = _merge_translations(translations, sanskrit_text)
    prompt = _format_prompt(
        input_text=input_text,
        commentaries=comms,
        translations=trans,
    )
    try:
        structured = model.with_structured_output(UCCASyntacticPackage)
        pkg = structured.invoke(prompt)
        if pkg is None:
            raise ValueError("Empty structured UCCA response")
    except Exception:
        response = model.invoke(prompt)
        raw = getattr(response, "content", str(response))
        cleaned = _strip_code_fences(raw)
        data = json.loads(cleaned)
        pkg = UCCASyntacticPackage.model_validate(data)
    layer3 = render_layer3_markdown(pkg)
    return layer3, pkg


async def stream_ucca_generation(
    model: BaseChatModel,
    items: List[Dict[str, Any]],
    batch_size: int = 5,
) -> AsyncGenerator[str, None]:
    def sse(event: Dict[str, Any]) -> str:
        event_with_ts = {"timestamp": datetime.now().isoformat(), **event}
        return f"data: {json.dumps(event_with_ts)}\n\n"

    yield sse({"type": "ucca_start", "status": "starting", "total_items": len(items)})
    aggregated_results: list[dict] = []

    for start in range(0, len(items), max(1, batch_size)):
        chunk = items[start : start + batch_size]
        for i, _ in enumerate(chunk, start=start):
            yield sse({"type": "ucca_item_start", "index": i, "status": "processing"})

        prompts = []
        for it in chunk:
            comms, trans = _context_from_item(it)
            prompts.append(
                _format_prompt(
                    input_text=it.get("input_text", ""),
                    commentaries=comms,
                    translations=trans,
                )
            )

        try:
            structured = model.with_structured_output(UCCASyntacticPackage)
            responses = await structured.abatch(prompts)
        except Exception:
            try:
                responses = await model.abatch(prompts)
            except Exception:
                responses = [model.invoke(p) for p in prompts]

        for offset, resp in enumerate(responses):
            idx = start + offset
            try:
                if resp is None:
                    raise ValueError("Empty response from LLM")
                if hasattr(resp, "model_dump"):
                    dumped = resp.model_dump() if resp is not None else None
                    if not dumped:
                        raise ValueError("Empty structured response")
                    pkg = UCCASyntacticPackage(**dumped)
                else:
                    raw = getattr(resp, "content", str(resp))
                    if not raw or raw.strip().lower() == "none":
                        raise ValueError("Empty raw response")
                    cleaned = _strip_code_fences(raw)
                    data = json.loads(cleaned)
                    pkg = UCCASyntacticPackage(**data)
                layer3 = render_layer3_markdown(pkg)
                item_result = {
                    "index": idx,
                    "ucca_syntactic": pkg.model_dump(),
                    "ucca_markdown": layer3,
                }
                aggregated_results.append(item_result)
                yield sse(
                    {
                        "type": "ucca_item_completed",
                        "index": idx,
                        "status": "completed",
                        "ucca_syntactic": item_result["ucca_syntactic"],
                        "ucca_markdown": layer3,
                    }
                )
            except Exception:
                try:
                    structured_single = model.with_structured_output(UCCASyntacticPackage)
                    parsed = structured_single.invoke(prompts[offset])
                    if parsed is None:
                        raise ValueError("Empty retry response from LLM")
                    if hasattr(parsed, "model_dump"):
                        dumped = parsed.model_dump()
                        pkg = UCCASyntacticPackage(**dumped)
                    else:
                        raw2 = getattr(parsed, "content", str(parsed))
                        if not raw2 or raw2.strip().lower() == "none":
                            raise ValueError("Empty retry raw response")
                        cleaned2 = _strip_code_fences(raw2)
                        data2 = json.loads(cleaned2)
                        pkg = UCCASyntacticPackage(**data2)
                    layer3 = render_layer3_markdown(pkg)
                    item_result = {
                        "index": idx,
                        "ucca_syntactic": pkg.model_dump(),
                        "ucca_markdown": layer3,
                    }
                    aggregated_results.append(item_result)
                    yield sse(
                        {
                            "type": "ucca_item_completed",
                            "index": idx,
                            "status": "completed",
                            "ucca_syntactic": item_result["ucca_syntactic"],
                            "ucca_markdown": layer3,
                        }
                    )
                except Exception as e2:
                    aggregated_results.append({"index": idx, "error": str(e2)})
                    yield sse(
                        {
                            "type": "ucca_item_error",
                            "index": idx,
                            "status": "failed",
                            "error": str(e2),
                        }
                    )

    yield sse({"type": "completion", "status": "completed", "results": aggregated_results})
