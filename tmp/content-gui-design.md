# Content Lifecycle GUI - User Experience Design

## Problem

The content lifecycle system (generated → editing → published) involves:
- Stage transitions (`sp transition`)
- Status checking (`sp content status`)
- Git operations (commit, push, pull)
- Permission management
- Metadata tracking
- Requirement validation

**This is too complex for non-technical users** (editors, translators, content creators).

## Proposed Solution: `sp content gui`

Launch a web-based GUI for content lifecycle management.

### Core Features

#### 1. Dashboard View
```
┌─────────────────────────────────────────────────┐
│ Content Lifecycle Dashboard                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Generated (47 files)    →    Editing (1 file)  →    Published (12 files)  │
│  ┌───────────────┐         ┌───────────────┐       ┌───────────────┐    │
│  │ mark-1-1-13   │  Send → │ mark-2-1-12   │ Pub → │ mark-3-1-6    │    │
│  │ mark-1-14-20  │         └───────────────┘   │   │ mark-3-7-12   │    │
│  │ mark-2-13-17  │                             │   └───────────────┘    │
│  │ ...           │                                                        │
│  └───────────────┘                                                        │
│                                                                           │
│  [Refresh]  [Settings]  [Help]                                           │
└─────────────────────────────────────────────────┘
```

#### 2. File Detail View
```
┌─────────────────────────────────────────────────┐
│ mark-1-1-13 (Editing Stage) ✏️                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Status: In Editing                             │
│  Editor: jane@example.com                       │
│  Last Modified: 2026-04-03 10:15:00            │
│  Source: generated/mark/mark-1-1-13.md         │
│                                                 │
│  Git Status: ⚠️ Uncommitted changes             │
│                                                 │
│  Actions:                                       │
│  [Preview] [Edit in VS Code] [Compare]         │
│  [Commit Changes] [Publish to Final]           │
│                                                 │
│  Validation: ✅ All checks passed               │
│  - Schema valid                                 │
│  - Metadata complete                            │
│  - No empty sections                            │
└─────────────────────────────────────────────────┘
```

#### 3. Transition Wizard
```
┌─────────────────────────────────────────────────┐
│ Publish mark-1-1-13 to Final                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  Step 1: Pre-flight Checks                     │
│  ✅ File exists in editing stage                │
│  ✅ Metadata complete (editor, last_modified)   │
│  ❌ Uncommitted changes                         │
│                                                 │
│  Required Action:                               │
│  Commit Message: ____________________________    │
│  [Commit Changes]                               │
│                                                 │
│  Step 2: Review Changes                         │
│  [Not yet available - commit first]             │
│                                                 │
│  [Cancel] [Next →]                              │
└─────────────────────────────────────────────────┘
```

#### 4. Integrated Git UI
```
┌─────────────────────────────────────────────────┐
│ Git Status                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  Branch: main                                   │
│  Remote: ↑ 2 ahead, ↓ 1 behind                 │
│                                                 │
│  Uncommitted Changes (3 files):                 │
│  M  editing/mark/mark-1-1-13.md                │
│  M  editing/mark/.metadata.json                │
│  A  editing/mark/mark-2-1-12.md                │
│                                                 │
│  Commit Message: ___________________________    │
│  [Commit] [Commit & Push]                      │
│                                                 │
│  Recent Commits:                                │
│  a7b8c92  chore: publish mark-1-1-13           │
│  3f4e567  edit: improve mark-2-1-12            │
│                                                 │
│  [Pull] [Push] [Sync]                          │
└─────────────────────────────────────────────────┘
```

### Technical Implementation

**Architecture:**
```
Browser
  ↓
http://localhost:5050/content
  ↓
Flask Backend (sp content gui)
  ↓
- content_transition.py (transitions)
- git commands (via subprocess)
- file system operations
- metadata management
```

**Similar to existing `sp gui` for pipelines, but focused on content lifecycle.**

### User Personas

#### Persona 1: Editor (Jane)
- **Technical level:** Low (knows Markdown, not git)
- **Needs:**
  - See what files need editing
  - Preview content before publishing
  - Simple "Send to Published" button
  - Clear error messages if something blocks publishing

#### Persona 2: Project Lead (Jonathan)
- **Technical level:** High (comfortable with CLI and git)
- **Needs:**
  - Overview of pipeline state
  - Ability to revert bad publishes
  - See who edited what
  - Debug permission issues

#### Persona 3: Translator (María)
- **Technical level:** Medium (knows files/folders, not command line)
- **Needs:**
  - Edit content in her preferred editor (Word, Google Docs)
  - Simple workflow: download → edit → upload → publish
  - Visual diff to see what changed

### Key UX Principles

1. **Visual status indicators** - Color-coded stages, icons for status
2. **Prevent mistakes** - Disable invalid transitions, show requirements
3. **Progressive disclosure** - Simple by default, advanced features hidden
4. **Undo-friendly** - Easy rollback, clear before/after previews
5. **Integrated help** - Tooltips, help text, examples

### Implementation Phases

**Phase 1: MVP (Core Functionality)**
- Dashboard with file listing per stage
- Transition wizard with requirement checks
- File preview (Markdown rendering)
- Basic git status display

**Phase 2: Git Integration**
- Commit UI
- Push/pull buttons
- Conflict detection and resolution helpers
- Branch visualization

**Phase 3: Advanced Features**
- Side-by-side diff viewer
- Inline editing (simple text editor)
- External editor integration (open in VS Code)
- Batch operations (publish multiple files)
- History/timeline view

**Phase 4: Collaboration**
- Multi-user indicator (who's editing what)
- Comments/review system
- Approval workflow
- Notifications

### Alternative: VS Code Extension

Instead of web GUI, could build **VS Code extension** with similar features:
- Sidebar panel showing content stages
- Right-click file → "Send to Editing"
- Inline status indicators in file tree
- Integrated with VS Code's git UI

**Pros:**
- Native git integration
- Better editor experience
- No separate server needed

**Cons:**
- Requires VS Code (not accessible to all users)
- More complex to develop
- Harder to distribute

### Recommendation

**Start with web GUI (`sp content gui`)** because:
1. Accessible to non-technical users (no IDE required)
2. Can run on remote server for team access
3. Reuses existing `sp gui` infrastructure
4. More visual/friendly for content creators
5. Later, can add VS Code extension for developers who prefer it

---

## Command Signature

```bash
# Launch GUI
sp content gui [OPTIONS]

Options:
  --host TEXT        Host address (default: 127.0.0.1)
  --port INTEGER     Port number (default: 5050)
  --content-root     Path to content/ directory
  --no-browser       Don't auto-open browser
  --readonly         Launch in read-only mode (view only, no transitions)
```

## Related Issues

- [ ] Design GUI mockups
- [ ] Implement Flask routes for content operations
- [ ] Add real-time file watching (auto-refresh on changes)
- [ ] Add permission management UI
- [ ] Add metadata editor
- [ ] Add schema validation display
- [ ] Document deployment for team servers
