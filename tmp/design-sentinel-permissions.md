# Sentinel File Design: Avoiding Merge Conflicts

## Problem

We want to use a sentinel file to detect git clones (so we can auto-reapply file permissions), but this file could cause merge conflicts if multiple developers are using `sp` commands and the file changes frequently.

## Solution Options

### Option 1: Minimal Sentinel + Git Merge Strategy

**Sentinel file:** `content/.sp-permissions`

**Contents (minimal):**
```json
{
  "version": "1.0",
  "config_fingerprint": "sha256:abc123..."
}
```

**Only update when:**
- `content-stages.yaml` changes (rare event)
- First creation

**NOT updated on:**
- Individual file transitions (would cause constant conflicts)
- Permission reapplications

**Use `.gitattributes` merge strategy:**

Create `content/.gitattributes`:
```
.sp-permissions merge=ours
```

This tells git: "On merge conflicts, always take our branch's version."

**Why this works:**
- The sentinel's CONTENT doesn't matter for other developers
- Each dev's local sentinel gets checked/regenerated on every `sp` command anyway
- If the fingerprint is stale, permission reapplication happens automatically
- Conflicts are resolved automatically via `.gitattributes`

---

### Option 2: Ultra-Minimal Marker (RECOMMENDED)

**Sentinel file:** `content/.sp-permissions`

**Contents (minimal marker):**
```json
{"_marker": "sp"}
```

Just a marker file. The ONLY thing that matters is:
- **Does it exist?** → permissions have been set up
- **Is it writable?** → just cloned, reapply permissions

**All actual state lives in:**
- `.metadata.json` files (per-stage, line-delimited JSON to reduce conflicts)
- Individual file permissions (which get reapplied automatically)

**Advantages:**
- File content NEVER changes after creation
- Zero merge conflicts (everyone has identical content)
- Simple to implement
- Easy to understand

**Git tracking:**
```gitignore
# Don't track the sentinel (everyone creates their own)
content/.sp-permissions
```

Wait, that defeats the purpose! We need it tracked so post-clone it exists but is writable.

**Better approach:**
Track it, but never modify it. It's created once and never touched.

---

### Option 3: Per-Stage Sentinel Files (BEST FOR MULTI-DEV)

**Sentinel files:**
```
content/
  generated/.sp-stage
  editing/.sp-stage
  published/.sp-stage
```

**Contents:**
```json
{
  "stage": "editing",
  "permissions": "644"
}
```

**Benefits:**
- Conflicts only if developers work in same stage simultaneously (rare)
- Each stage independently tracks its permission state
- Easier to debug ("which stage has stale permissions?")
- Granular control
- Lower conflict probability (distributed across files)

**Git attributes:**
```
# content/.gitattributes
*/.sp-stage merge=ours
```

**When to check/reapply:**
- Check all stage sentinels on any `sp` command
- Only reapply permissions for stages where sentinel is writable
- More efficient than reapplying all permissions

---

### Option 4: No Sentinel - Check On-Demand

**Alternative approach:** Don't use a sentinel at all.

**On every `sp` command:**
1. Sample a few known files from each stage
2. Check if their permissions match expected (from config)
3. If mismatched → reapply all permissions for that stage

**Advantages:**
- No special files to track
- No merge conflicts ever
- Works even if someone manually changes permissions

**Disadvantages:**
- Slightly slower (checking file permissions)
- More complex logic
- No "first run" detection

---

## Recommendation

**Option 2 (Ultra-Minimal Marker) + gitattributes**

**Implementation:**

1. Create `content/.sp-permissions` on first `sp` command:
   ```json
   {"_marker": "sp"}
   ```

2. Set it to read-only (444)

3. On every `sp` command (before doing anything else):
   ```python
   sentinel = content_root / ".sp-permissions"

   if sentinel.exists() and os.access(sentinel, os.W_OK):
       # Sentinel is writable = just cloned
       logger.info("🔧 Detected git clone - reapplying file permissions...")
       reapply_all_permissions(content_root)
       os.chmod(sentinel, 0o444)
   elif not sentinel.exists():
       # First run
       create_sentinel(content_root)
       os.chmod(sentinel, 0o444)
   ```

4. Add to `content/.gitattributes`:
   ```
   .sp-permissions merge=ours
   ```

5. **Never modify the sentinel after creation** (no state updates)

**Why this wins:**
- Simple implementation
- File never changes → minimal conflict risk
- `.gitattributes` handles rare conflicts automatically
- Single file to manage (not per-stage)
- Clear semantics: "permissions have been initialized"

---

## Edge Cases

### Multiple devs transition same file simultaneously

**Scenario:** Dev A and Dev B both transition `mark-1-1-13` from `editing → published`

**Conflicts:**
- Both remove `editing/mark-1-1-13.*`
- Both add `published/mark-1-1-13.*`
- `.metadata.json` in both stages conflicts

**Solution:**
1. Git will conflict on the metadata files
2. Human resolves (standard git workflow)
3. Sentinel doesn't add extra conflicts (it's unchanged)
4. After merge, permissions are correct (both applied same permissions)

### Config changes between branches

**Scenario:** Branch A changes stage permissions in `content-stages.yaml`, Branch B doesn't

**After merge:**
- Config file merge resolved normally
- Sentinel exists but fingerprint is stale (if using Option 1)
- Next `sp` command detects config change and reapplies

With Option 2 (minimal marker), no fingerprint check needed:
- Just check: are current file permissions correct per current config?
- If not, reapply

### First dev creates sentinel, second dev clones

**Timeline:**
1. Dev A creates project, runs `sp transition` → sentinel created (444)
2. Dev A commits and pushes
3. Dev B clones → sentinel becomes writable (644)
4. Dev B runs `sp transition` → detects writable sentinel, reapplies permissions
5. Dev B's sentinel is now read-only (444) again
6. ✅ Works correctly

---

## Implementation Checklist

- [ ] Add `ensure_correct_permissions()` function
- [ ] Call on every `sp` command entry point
- [ ] Create sentinel file on first run
- [ ] Test: sentinel detection after git clone simulation
- [ ] Test: permissions reapply correctly
- [ ] Test: sentinel remains read-only after reapply
- [ ] Create `.gitattributes` with merge=ours
- [ ] Document in user guide: "Why .sp-permissions exists"
- [ ] Test: sentinel doesn't cause conflicts in real git workflow
