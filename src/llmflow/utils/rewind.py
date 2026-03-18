"""Utilities for managing rewind state using existing saveas artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from llmflow.exceptions import StepRewindError
from llmflow.modules.logger import Logger
from llmflow.utils.get_prefix_directory import get_prefix_directory

logger = Logger()


class StepRewindManager:
    """Rehydrate step outputs directly from their saveas files."""

    def __init__(self, *, rewind_to: Optional[str] = None) -> None:
        self.rewind_to = rewind_to
        self._rewind_complete = not bool(rewind_to)

    def record_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> None:  # pragma: no cover - retained for API parity
        context.pop("_last_saved_files", None)

    @property
    def in_rewind_phase(self) -> bool:
        """True while we are still replaying steps before the rewind target."""
        return bool(self.rewind_to) and not self._rewind_complete

    def should_replay(self, step_name: str, *, step: Dict[str, Any] | None = None) -> bool:
        if not self.rewind_to:
            return False
        if self._rewind_complete:
            return False
        # Steps with no saveas cannot be replayed from a file artifact.
        # Re-execute them normally so they populate context (e.g. passage_info)
        # before downstream saveas paths are resolved.
        if step is not None and not step.get("saveas"):
            return False
        return True

    def mark_target_reached(self, step_name: str) -> None:
        """Mark the rewind phase complete when the target step was re-executed
        (because it has no saveas) rather than replayed from a file."""
        if self.rewind_to and step_name == self.rewind_to:
            self._rewind_complete = True

    def replay_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> None:
        step_name = step.get("name", "unnamed")
        if not step.get("saveas"):
            raise StepRewindError(
                f"Step '{step_name}' cannot be rewound because it does not declare saveas",
                step_name=step_name,
                context=context,
            )

        outputs = step.get("outputs")
        if not outputs:
            raise StepRewindError(
                f"Step '{step_name}' must declare outputs to support rewind",
                step_name=step_name,
                context=context,
            )
        if isinstance(outputs, list):
            if len(outputs) != 1:
                raise StepRewindError(
                    f"Step '{step_name}' defines multiple outputs; rewind requires a single output",
                    step_name=step_name,
                    context=context,
                )
            target_output = outputs[0]
        else:
            target_output = outputs

        if step.get("append_to"):
            # TODO: Support rewind for for-each inner steps with append_to.
            # When saveas path is unique per iteration (contains a loop variable)
            # the artifact exists for each item and could be re-appended instead
            # of raising here.  See docs/TODO.md "Rewind: for-each inner step
            # support" for the full plan.  Do not remove this guard until that
            # work is complete.
            raise StepRewindError(
                f"Step '{step_name}' uses append_to which is not supported by rewind",
                step_name=step_name,
                context=context,
            )

        resolved_paths = self._resolve_save_paths(step, context)
        if not resolved_paths:
            raise StepRewindError(
                f"Unable to resolve saveas path for step '{step_name}'",
                step_name=step_name,
                context=context,
            )

        primary_path = Path(resolved_paths[0]).expanduser()
        if not primary_path.is_absolute():
            primary_path = Path.cwd() / primary_path

        if not primary_path.exists():
            raise StepRewindError(
                f"Saved artifact missing for step '{step_name}': {primary_path}",
                step_name=step_name,
                context=context,
            )

        content = primary_path.read_text(encoding="utf-8")
        # Attempt JSON parse so downstream steps receive the same type
        # (list, dict) they would have from a live run. Fall back to raw
        # string for non-JSON artifacts (markdown, plain text, etc.).
        # Honor output_type: json as an explicit signal; warn if it is set
        # but the artifact cannot be parsed.
        output_type = step.get("output_type", "")
        try:
            context[target_output] = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            if output_type == "json":
                logger.warning(
                    f"Step '{step_name}' declares output_type: json but artifact "
                    f"at {primary_path} is not valid JSON — storing as string"
                )
            context[target_output] = content
        logger.info(f"⏪ Replayed step '{step_name}' using {primary_path}")

        if step_name == self.rewind_to:
            self._rewind_complete = True

    def _resolve_save_paths(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        from llmflow.runner import resolve

        saveas_config = step.get("saveas")
        paths: List[str] = []

        if isinstance(saveas_config, str):
            path = resolve(saveas_config, context)
            self._ensure_path_resolved(path, saveas_config, step)
            paths.append(str(path))
            return paths

        if isinstance(saveas_config, dict):
            raw_path = saveas_config.get("path")
            path = resolve(raw_path, context)
            self._ensure_path_resolved(path, raw_path, step)

            group_cfg = saveas_config.get("group_by_prefix")
            if group_cfg:
                filename = Path(path).name
                if isinstance(group_cfg, int):
                    prefix_dir = get_prefix_directory(filename, prefix_length=group_cfg)
                else:
                    prefix_dir = get_prefix_directory(
                        filename,
                        prefix_length=group_cfg.get("prefix_length"),
                        prefix_delimiter=group_cfg.get("prefix_delimiter"),
                    )
                parent = Path(path).parent
                path = str((parent / prefix_dir / filename))

            paths.append(str(path))
            return paths

        raise StepRewindError(
            f"Unsupported saveas configuration for step '{step.get('name', 'unnamed')}'",
            step_name=step.get("name"),
            context=context,
        )

    def _ensure_path_resolved(self, value: Any, original: Any, step: Dict[str, Any]) -> None:
        path_str = str(value)
        if "${" in path_str or "{" in path_str:
            raise StepRewindError(
                f"Saveas path for step '{step.get('name', 'unnamed')}' contains unresolved variables: {original}",
                step_name=step.get("name"),
            )


__all__ = ["StepRewindManager"]
