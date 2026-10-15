"""`type: dictionary` — Tyndale Open Bible Dictionary articles, by title (#272).

A step names its articles with `entries:` — titles, or ACAI's `{id, title}` pairs — or hands it a
whole `type: acai` result with `acai:`, and gets every article that result's entities name. One of
the two, never both.

The reading is `utils.dictionary`; this module resolves the keys, finds the registered dataset,
and puts the answer, with the credit its licence asks for, in the context.
"""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_dictionary_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    from llmflow import resources as _resources
    from llmflow.utils.dictionary import articles_for, declaration, titles_from_acai, titles_in

    name = step.get("name", "unnamed")
    logger.info(f"📖 Starting dictionary step: {name}")

    has_entries, has_acai = "entries" in step, "acai" in step
    if has_entries == has_acai:
        raise ValueError(
            f"dictionary step '{name}' takes `entries:` or `acai:`, and exactly one. `entries:` "
            "names articles by title; `acai:` takes a `type: acai` result and fetches every "
            "article its entities name."
        )

    declared = declaration()
    dataset = declared["dataset"]
    registration = _resources.dataset_registration(dataset)
    root = registration.get("path") if registration else None
    if not root:
        raise ValueError(
            f"dictionary step '{name}' reads the Tyndale Open Bible Dictionary from the dataset "
            f"{dataset!r}, which is not registered on this machine. Register a clone of "
            f"TyndaleOpen/tyndale-open-bible-dictionary: `sp dataset add {dataset} --path <clone>`."
        )

    if has_entries:
        entries = resolve(step["entries"], context)
        titles = titles_in(entries if isinstance(entries, list) else [entries])
    else:
        titles = titles_from_acai(resolve(step["acai"], context))

    found, missing = articles_for(titles, root)
    if missing:
        logger.warning(
            f"dictionary step '{name}': the Tyndale Open Bible Dictionary has no article titled "
            f"{', '.join(repr(title) for title in missing)}, so none is returned for "
            f"{'it' if len(missing) == 1 else 'them'}."
        )

    logger.info(f"   {len(found)} articles")
    handle_step_outputs(step, {"articles": found, "attribution": declared["attribution"]}, context)
