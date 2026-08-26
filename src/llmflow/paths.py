"""Where the Scripture Pipelines store lives.

One function, because the answer is one fact. Eleven call sites across four modules each wrote
`Path.home() / ".sp"` before this, which is eleven encodings of one fact — the defect rule
`design-is-declarative` names: *"two encodings of one fact are the defect, because they agree
until they silently do not."*

`$SP_HOME` relocates the store. That earns its keep in three places:

- **The test suite (#207).** `sp init` installs disciplines and skills over the store, and every
  init test registers its pytest temp directory as a permanent project. The Captain cleaned 18
  junk registrations out of `~/.sp/projects/` on 2026-08-24; test runs the same day recreated 16.
  Idempotence cannot help — each temp directory is a genuinely new project, correctly registered
  — so the store itself has to move.
- **Containers and CI**, where a home directory is not a durable place to keep anything.
- **A machine where the store belongs elsewhere**, which was previously unrepresentable.

Redirecting `$HOME` would also have worked and reaches much too far: two test files locate the
Human at the Helm clone under `~/github/` and *skip* when it is absent, so moving `HOME` beneath
them would turn two real guards green while they check nothing. `$SP_HOME` touches only the store.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Environment variable that relocates the store. Unset in normal use.
SP_HOME_ENV = "SP_HOME"


def sp_home() -> Path:
    """The store directory — `$SP_HOME` if set, otherwise `~/.sp`.

    Resolved on every call rather than cached at import: a test that sets the variable after
    importing a module must still see it move, and caching would make the first importer decide
    for the whole process.
    """
    override = os.environ.get(SP_HOME_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sp"
