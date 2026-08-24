# Consumer Repo Conventions

## Scripture Pipelines dependency — do not touch

Consumer repos (ears-to-hear, discourse-flow, etc.) declare their Scripture Pipelines dependency in `pyproject.toml`. **Never modify this line for any reason.**

The correct form is an editable install so that changes to the local Scripture Pipelines dev tree flow through immediately without rebuilding the hatch environment. Agents have repeatedly "cleaned up" or reformatted this line and silently reverted it to a non-editable install, causing stale-install bugs.

If you are editing `pyproject.toml` in a consumer repo for any other reason, leave the Scripture Pipelines line exactly as you found it.

## Refreshing the hatch environment

If the Scripture Pipelines dependency has been accidentally installed as non-editable, or after any change to `pyproject.toml`, rebuild the env:

```bash
hatch env remove
hatch shell
```
