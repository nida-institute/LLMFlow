# GUI Output Access Design Brainstorm

**Status:** Design exploration
**Created:** April 2, 2026
**Related Issue:** See latest issue about GUI output accessibility

---

## Core Problem

Pipelines write files. GUI runs pipelines. Users can't get to the files without leaving the GUI.

**The workflow gap:**
```
User runs pipeline in GUI
  → Pipeline completes successfully
  → User sees completion message
  → User switches to Finder/terminal
  → User manually navigates to output directory
  → User opens files
```

**What we want:**
```
User runs pipeline in GUI
  → Pipeline completes
  → User clicks "Open Output" or file link
  → Files open in user's preferred tools
```

---

## Design Principles

### 1. User Tools Over Custom Viewers
Don't build a markdown renderer or JSON viewer — users have tools they like. Open files in **their** editors, not ours.

### 2. One Click to Access
No copy-paste paths, no terminal commands. Mouse click → file opens.

### 3. Cross-Platform from Day One
macOS, Windows, Linux all have different file-opening commands. Handle all three.

### 4. Respect User Workflow
Some users want VS Code. Some want Finder. Some want default apps. Support multiple access patterns.

---

## Brainstorming: Access Patterns

### Pattern A: "Open Containing Folder"
**What:** Button that opens the output directory in system file manager
**Pros:**
- Simplest to implement (one command per platform)
- Familiar pattern (GitHub does this with releases)
- Lets user use their file manager UI
- No path security concerns (just open a directory)

**Cons:**
- Requires user to find the specific file in the folder
- Not great if pipeline writes many files across subdirectories

**Implementation:**
```python
# Backend endpoint: POST /api/open-folder
import subprocess, platform

def open_folder(path):
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", path])
    elif system == "Windows":
        subprocess.run(["explorer", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])
```

**When to use:** MVP. Gets users 80% of the way there with minimal code.

---

### Pattern B: "Click File to Open"
**What:** Display list of created files, click any to open in default app
**Pros:**
- Direct access to specific files
- Familiar web pattern (file downloads)
- Can group by step or output type

**Cons:**
- Need to resolve `${variable}` paths at runtime
- Need to track all created files during execution
- Security: validate paths are safe to open
- Complex for pipelines that write hundreds of files

**Implementation sketch:**
```python
# During step execution in executor.py:
def _save_output(self, content, save_config):
    resolved_path = self._resolve_path(save_config["path"])
    # ... write file ...
    self.output_files.append({
        "step": self.current_step,
        "path": resolved_path,
        "relative": os.path.relpath(resolved_path, self.project_root)
    })

# Send to frontend:
socket.emit("step_complete", {
    "step": step_name,
    "output_files": self.output_files
})

# Backend endpoint: POST /api/open-file {"path": "..."}
def open_file(path):
    # Validate path is within project
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(self.project_root):
        raise SecurityError("Path outside project")

    # Open with system default
    if platform.system() == "Darwin":
        subprocess.run(["open", abs_path])
    # ... etc
```

**When to use:** Phase 2, after MVP proves the concept.

---

### Pattern C: "Reveal in Finder/Explorer"
**What:** Right-click file → "Reveal in Finder" (like browsers do with downloads)
**Pros:**
- Combines benefits of A and B
- Shows file in context of its directory
- Familiar UX pattern from browsers/IDEs

**Cons:**
- Requires context menu implementation
- Platform-specific reveal commands differ from open commands

**Platform commands:**
```bash
# macOS: reveal file in Finder
open -R /path/to/file.md

# Windows: reveal in Explorer with file selected
explorer /select,"C:\path\to\file.md"

# Linux: open parent dir (no native "reveal" in most file managers)
xdg-open $(dirname /path/to/file.md)
```

**When to use:** Enhancement after Pattern B works.

---

### Pattern D: "VS Code Integration"
**What:** Detect VS Code environment, offer "Open in VS Code" option
**Pros:**
- Deep integration with common workflow
- Can open file at specific line if we track that
- Users already have VS Code open when using GUI

**Cons:**
- Only helps VS Code users
- Requires VS Code API detection
- Complexity for marginal benefit (Pattern B covers this)

**Implementation:**
```javascript
// Frontend detection:
const inVSCode = typeof acquireVsCodeApi !== 'undefined';

// If in VS Code, use vscode.open command
if (inVSCode) {
    vscode.postMessage({
        command: 'open',
        path: filePath
    });
}
```

**When to use:** Nice-to-have after core patterns work.

---

## Brainstorming: Path Resolution

### Challenge: Template Variables
Pipelines use `saveas: "outputs/${passage}.md"` — we need actual paths.

### Solution 1: Track During Execution
Modify `run_step()` to capture resolved paths when writing files:

```python
# In runner.py, when handling saveas:
resolved_path = resolve(save_config["path"], context)
# ... write file ...
context["_output_files"] = context.get("_output_files", [])
context["_output_files"].append(resolved_path)
```

Then pass `context["_output_files"]` to GUI at end of execution.

**Pros:**
- Accurate — we track exactly what was written
- Works for all `saveas` forms (string, dict, list)

**Cons:**
- Adds tracking overhead to runner
- Need to propagate through executor → server → frontend

---

### Solution 2: Parse YAML and Resolve Afterward
After pipeline completes, re-parse YAML and resolve all `saveas` paths with final context.

**Pros:**
- No runtime changes to executor
- Can do this entirely in server.py

**Cons:**
- Might miss dynamically-created paths
- Re-resolution could differ from actual execution
- Complex for `append_to` cases (multiple iterations, same file)

**Verdict:** Solution 1 is more reliable.

---

## Brainstorming: UI Patterns

### Option 1: Simple Success Message with Button
```
✅ Pipeline completed successfully!

[Open Output Folder]
```

**Pros:** Dead simple, works immediately
**Cons:** No file-level detail

---

### Option 2: Expandable File List
```
✅ Pipeline completed successfully!

📁 Output files (3):
  ▸ outputs/leaders_guide/019_leaders_guide.md
  ▸ outputs/exegetical/psalm19_culture.json
  ▸ outputs/debug/pipeline_log.txt

[Open Output Folder]
```

**Pros:** Users see what was created
**Cons:** Verbose for pipelines with many files

---

### Option 3: Per-Step File Display
```
Step: generate_leaders_guide ✅
  📄 019_leaders_guide.md

Step: generate_exegetical_culture ✅
  📄 psalm19_culture.json
```

**Pros:** Shows file in context of step that created it
**Cons:** UI clutter if many steps

---

### Option 4: Tabbed View
```
[Execution Log] [Output Files]

Output Files:
  📄 019_leaders_guide.md     [Open] [Reveal]
  📄 psalm19_culture.json     [Open] [Reveal]
  📄 pipeline_log.txt         [Open] [Reveal]
```

**Pros:** Clean separation, scalable to many files
**Cons:** Requires more UI work

---

## Recommended Implementation Plan

### Phase 1: MVP (1-2 hours)
1. **Backend:** `POST /api/open-folder` endpoint
   - Takes `{"path": "output/dir"}`
   - Validates path is within project
   - Calls system command to open folder

2. **Executor:** Track primary output directory
   - Infer from first `saveas` path or pipeline `output_dir` variable
   - Pass to frontend in completion event

3. **Frontend:** Add "Open Output Folder" button to completion UI
   - Calls `/api/open-folder` on click
   - Shows in success message

**Deliverable:** Users can click one button to see their outputs in Finder/Explorer.

---

### Phase 2: File List (2-4 hours)
1. **Executor:** Track all resolved output paths
   - Modify `_handle_saveas()` to append to `self.output_files`
   - Include step name, relative path, file type

2. **Server:** Add `POST /api/open-file` endpoint
   - Validates path
   - Opens with system default app

3. **Frontend:** Display file list in completion UI
   - Show relative paths grouped by step
   - Click to open, hover for full path

**Deliverable:** Users can click any output file to open it.

---

### Phase 3: Enhanced UX (nice-to-have)
- Right-click → "Reveal in Finder/Explorer"
- Copy path to clipboard option
- Filter files by type (markdown, JSON, etc.)
- VS Code integration if running in VS Code

---

## Open Questions

1. **Output directory inference:** Use pipeline `output_dir` variable or first `saveas` parent directory?

2. **Multiple output directories:** If pipeline writes to 3 different top-level folders, show 3 "Open Folder" buttons?

3. **Temporary files:** Should we track files that aren't in `saveas` (e.g., `.log` files)?

4. **Long file lists:** If pipeline writes 500 files (e.g., one per verse), show all or summarize?

5. **File watching:** Should GUI auto-refresh if files change on disk after pipeline completes?

6. **Permissions:** What if output directory requires elevated permissions?

---

## Security Considerations

### Path Validation
Always validate that paths to open are within the project directory:

```python
def validate_path(requested_path, project_root):
    abs_requested = os.path.abspath(requested_path)
    abs_root = os.path.abspath(project_root)

    if not abs_requested.startswith(abs_root):
        raise SecurityError("Path outside project")

    if not os.path.exists(abs_requested):
        raise FileNotFoundError(f"Path does not exist: {requested_path}")

    return abs_requested
```

### Symlink Attack Prevention
Check for symlinks that escape the project:

```python
real_path = os.path.realpath(abs_requested)
if not real_path.startswith(abs_root):
    raise SecurityError("Symlink escape attempt")
```

### Command Injection
Never construct shell commands with user input:

```python
# BAD
os.system(f"open {user_path}")  # Injection risk!

# GOOD
subprocess.run(["open", user_path])  # No shell interpretation
```

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Open folder on macOS (Finder)
- [ ] Open folder on Windows (Explorer)
- [ ] Open folder on Linux (file manager)
- [ ] Open .md file in default app
- [ ] Open .json file in default app
- [ ] Try path outside project (should fail)
- [ ] Try non-existent path (should fail)
- [ ] Pipeline with no outputs (no files to show)
- [ ] Pipeline with 100+ outputs (UI scalability)

### Automated Tests
```python
def test_open_folder_validates_path():
    with pytest.raises(SecurityError):
        open_folder("/etc/passwd")

def test_tracks_output_files():
    executor = PipelineExecutor(...)
    executor.run()
    assert len(executor.output_files) > 0
    assert all("path" in f for f in executor.output_files)
```

---

## Alternative Approaches Considered

### Embedded File Viewer
**Idea:** Show file contents in GUI (markdown renderer, JSON tree viewer)
**Rejected because:**
- Adds complexity for marginal benefit
- Users have better tools already
- Doesn't work for all file types (images, USFM, etc.)
- Maintenance burden (keep renderers updated)

### Copy Path to Clipboard
**Idea:** Button to copy file path for user to paste elsewhere
**Rejected as primary solution because:**
- Extra step (copy → switch to terminal → paste)
- Doesn't help non-technical users
- Good as supplementary feature, not primary UX

### Download Files to Browser
**Idea:** Serve files via HTTP, let browser download them
**Rejected because:**
- Files are already on user's local disk
- Creates duplicate files in Downloads folder
- Breaks reference to original location (for editing/updating)

---

## Success Metrics

How do we know this feature works well?

1. **Usage:** % of pipeline runs where user clicks output access feature
2. **Support reduction:** Fewer "where are my files?" questions
3. **Workflow speed:** Time from completion to viewing first output file
4. **Error rate:** How often do file-open operations fail?

Target: >70% of users click output access within 30 seconds of completion.

---

## Future Enhancements

- **Smart file grouping:** Group related files (e.g., all chapters of a book)
- **Preview thumbnails:** Small preview for image/PDF outputs
- **Quick actions:** "Email this file", "Share via Dropbox", etc.
- **Output history:** Browse outputs from previous pipeline runs
- **Diff viewer:** Compare outputs from two different runs
- **Paratext integration:** "Open in Paratext" for USFM outputs

---

## References

- GitHub Desktop: "Show in Finder/Explorer" for cloned repos
- VS Code: File explorer with click-to-open
- Browser downloads: Right-click → "Show in Folder"
- Sublime Text: "Reveal in Finder" command
