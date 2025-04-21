
import subprocess

def call_llm(prompt_path_or_text, model="gpt-4o", tags=None, from_file=True):
    """
    Use the `llm` CLI to call a registered model with a prompt.
    If `from_file` is True, `prompt_path_or_text` is a path to a .gpt file.
    Otherwise it's a raw string prompt.
    """
    command = ["llm", "prompt", "-m", model]
    if tags:
        for tag in tags:
            command.extend(["--tag", tag])

    if from_file:
        command.extend(["-f", prompt_path_or_text])
    else:
        # For raw text, pass it as an argument after all options
        command.append(prompt_path_or_text)

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"LLM call failed: {result.stderr}")

    return result.stdout.strip()
