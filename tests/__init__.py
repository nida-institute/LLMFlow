# Capture the real C-level SystemExit before test_lint_exit.py can patch
# builtins.SystemExit with TracedSystemExit.  This module is loaded when Python
# first imports any module from the tests package — always before test_lint_exit
# is collected (alphabetical order guarantees another file comes first).
_real_system_exit = SystemExit
