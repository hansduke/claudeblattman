# Session Capture

*v2.1 — Sub-project routing rewritten with CWD precedence (Rule 1) and topic-divergence guard (Rule 2). Step 0.5 consolidates all path resolution into a single Python pass — downstream steps reuse the cached values instead of re-walking the filesystem. v1.12 added non-destructive fallback when no active sub-project is set: writes session content to a project-root SESSION_LOG.md instead of overwriting any project-root HANDOFF.md the user maintains by hand.*

Captures key decisions, open questions, follow-ups, and working artifacts from the current session. Writes a structured entry to a session log and persists unsaved artifacts for cross-session continuity.

## Arguments

`$ARGUMENTS` can include:
- *(none)* — full capture (decisions + questions + follow-ups + context)
- `quick` — abbreviated capture (decisions + follow-ups only, no context summary)
- `project` — also write a project-level `HANDOFF.md` to the project root
- `project:name` — tag the entry with a specific project name
- `retro` — additionally run a watch-list check (looks for unresolved hypotheses, failed approaches, and patterns repeated across sessions)

## How Routing Works (v2.0)

`/done` decides where to write the handoff using two rules in priority order. Both prevent the most common misroute: stale state from a prior `/start-task` overrides the current working directory.

**Rule 1 — CWD precedence.** If you're working inside a sub-folder that has its own `HANDOFF.md`, route there regardless of any state file. The actual workspace beats whatever state was set days ago.

**Rule 2 — Fresh active state.** If no sub-folder HANDOFF, but there's an `active-subproject.json` file modified within the last 24 hours (or marked `permanent: true`), route to its folder — but only if the session topic actually overlaps with the state's task name. The divergence guard prevents silent misroutes when state is stale or pointing somewhere irrelevant.

**Neither rule fires.** Falls through to a non-destructive path: writes a project-root `SESSION_LOG.md` (append-only) and a global handoff. **Never overwrites a project-root `HANDOFF.md` you maintain by hand** — that requires explicit `/start-task` first.

## Instructions

### Step 0.5: Consolidated CWD Walk

All path resolution happens once, in a single Python subprocess. Downstream steps reference the cached values — they MUST NOT re-walk the filesystem.

```python
import os, sys, json, time

d = os.getcwd()
now = time.time()
result = {
    "SUBPROJECT_NAME": "",
    "SUBPROJECT_FOLDER": "",
    "ACTIVE_SUBPROJECT_JSON": "",
    "ACTIVE_SUBPROJECT_DATA": None,
    "STATE_MTIME_EPOCH": 0,
    "STATE_AGE_HOURS": -1,
    "PROJECT_ROOT": "",
    "PROJECT_CLAUDE_MD": "",
    "CWD_HANDOFF_PATH": "",
}

cwd = d
for _ in range(7):
    # active-subproject.json (used by Rule 2)
    asp = os.path.join(cwd, '.claude', 'active-subproject.json')
    if os.path.exists(asp) and not result["ACTIVE_SUBPROJECT_JSON"]:
        try:
            data = json.load(open(asp))
            result["ACTIVE_SUBPROJECT_JSON"] = asp
            result["ACTIVE_SUBPROJECT_DATA"] = data
            result["SUBPROJECT_NAME"] = data.get('task_name', '')
            result["SUBPROJECT_FOLDER"] = data.get('folder_relative', '')
            mtime = os.path.getmtime(asp)
            result["STATE_MTIME_EPOCH"] = mtime
            result["STATE_AGE_HOURS"] = (now - mtime) / 3600.0
        except Exception:
            pass

    # .claude/CLAUDE.md (project root marker)
    cmd = os.path.join(cwd, '.claude', 'CLAUDE.md')
    if os.path.exists(cmd) and not result["PROJECT_ROOT"]:
        result["PROJECT_ROOT"] = cwd
        result["PROJECT_CLAUDE_MD"] = cmd

    # HANDOFF.md at this level — only counts as "sub-folder HANDOFF" if we haven't reached PROJECT_ROOT yet.
    h = os.path.join(cwd, 'HANDOFF.md')
    if os.path.exists(h) and not result["CWD_HANDOFF_PATH"] and not result["PROJECT_ROOT"]:
        result["CWD_HANDOFF_PATH"] = h

    parent = os.path.dirname(cwd)
    if parent == cwd:
        break
    cwd = parent

print(json.dumps(result))
```

Parse the JSON. Cache the values. Subsequent steps reference:
- `SUBPROJECT_NAME`, `SUBPROJECT_FOLDER`, `ACTIVE_SUBPROJECT_DATA`, `STATE_AGE_HOURS` → Steps 3, 5a
- `PROJECT_ROOT`, `PROJECT_CLAUDE_MD` → Steps 5a, 5a.5
- `CWD_HANDOFF_PATH` → Step 5a Rule 1

If `SUBPROJECT_NAME` is empty: Step 3 omits the sub-project tag.
If `PROJECT_ROOT` is empty: Step 5a.5 falls through to Step 5b's global path.
If `CWD_HANDOFF_PATH` is empty: Step 5a Rule 1 doesn't fire; check Rule 2.

### Step 1: Identify Session Scope

Review the conversation history and determine:
- **Session topic(s):** What was worked on? (1-2 line summary)
- **Project(s) touched:** Match against known projects
- **Duration indicator:** Brief (< 10 exchanges), Medium (10-30), Extended (30+)

**Auto-quick for Brief sessions:** If duration is Brief AND no `project`, `retro`, or explicit flags were passed, apply `quick` mode semantics automatically. Saves 3-6 tool calls per Brief invocation. Do NOT auto-apply quick for Medium or Extended sessions.

### Step 2: Extract Session Content

Scan the conversation for:

**Decisions made** — configuration changes, skill edits, policy updates, approach selections, commitments.

**Approaches rejected** *(optional — only if the session pivoted away from a started approach):* `[Approach] — [why rejected]`

**Open questions** — unresolved items that need future attention, deferred items, blockers.

**Follow-ups** — concrete next steps for future sessions.

**Key artifacts created** — files written or modified.

### Step 2.7: Watch-list Check (opt-in)

Run only when the `retro` arg is present. Otherwise skip entirely. Procedure: scan for unresolved hypotheses, failed approaches, and behavioral patterns repeated across sessions. Append observations to a watch-list file (e.g., `~/.claude-assistant/working-notes/watch-list.md`).

### Step 2.5: Working Artifacts

**Skip if** ALL of: ≤5 exchanges, no files created/modified, no decisions logged, no agents spawned. Also skip in `quick` mode.

Scan for substantial working content not already saved to a file — restructuring plans, agent review outputs, draft content, detailed decision rationale. Do NOT save reproducible outputs.

For each artifact: save to `<project-root>/working-notes/` (if `project` arg and project root found) or `~/Documents/working-notes/`. Use `YYYY-MM-DD_description.md` naming.

Budget: consolidate to 1-3 files max.

### Step 3: Write Session Entry

Append to your global session log (e.g., `~/Documents/session-log.md`):

```markdown
---

## [YYYY-MM-DD HH:MM] — [SUBPROJECT_NAME] [Session topic summary]
SESSLOG:[YYYY-MM-DD HH:MM]

**Project(s):** [project names or "General"]
**Duration:** [Brief/Medium/Extended]

### Decisions
- [Decision 1]

### Open Questions
- [Question 1]

### Follow-ups
- [ ] [Action item 1]

### Artifacts
- [Created/Modified] `path/to/file` — [what changed]

[If not `quick`:]
### Context
[2-4 sentence summary of key context for the next session.]
```

If the file doesn't exist, create with header `# Session Log` + a brief description. **New entries go at the TOP** (reverse chronological).

**Sub-project tagging:** If `SUBPROJECT_NAME` was found in Step 0.5, include it in brackets before the topic. Otherwise omit the brackets entirely.

### Step 3.5: Project SESSION_LOG.md Append (opt-in)

**Skip if** the current project's `.claude/CLAUDE.md` does not contain `session_log: true`, or if no project root is found.

If `session_log: true` is set: append a session entry to `<PROJECT_ROOT>/SESSION_LOG.md` (chronological, oldest first — opposite of the global log).

### Step 4: Prune and Cleanup

**Session log pruning:**
1. Count lines in your session log
2. ≤1,500 lines → skip
3. >1,500 → archive entries older than 60 days to `session-log-archive.md`
4. **One-time migration:** if file exceeds 3,000 lines, archive ALL entries older than 30 days

**Working-notes cleanup:** Delete files in `working-notes/` older than 30 days. Skip if no `working-notes/` directory exists.

### Step 5: Write Handoff Note

#### 5a. Sub-folder routing (CWD precedence)

Two rules in priority order. Use cached values from Step 0.5.

**Rule 1 — CWD precedence.** If `CWD_HANDOFF_PATH` is non-empty, route there regardless of `active-subproject.json`.

1. `folder_path = os.path.dirname(CWD_HANDOFF_PATH)`.
2. Derive `task_name`: read the first non-empty H1 of `CWD_HANDOFF_PATH`. If it matches `^# Handoff — (.+)$`, use the capture group; else use folder basename title-cased.
3. **Overwrite logging:** Read first non-empty line of existing `CWD_HANDOFF_PATH`, append to global session log: `*Sub-folder handoff overwritten (cwd-precedence): [first-line]*`
4. Write `folder_path/HANDOFF.md` using the project-level template.
5. **Global handoff:** write to your global handoff file ONLY if infrastructure files were modified (skill files, agent files, config files). Otherwise skip.
6. **Return** — skip Rule 2.

**Rule 2 — Fresh active state.** If Rule 1 did NOT fire AND `ACTIVE_SUBPROJECT_DATA` is non-empty AND `STATE_AGE_HOURS` is between 0 and 24 (or `permanent: true` in state), route to the state's folder.

**Divergence guard:** Before committing, tokenize `ACTIVE_SUBPROJECT_DATA.task_name` and the session's Step 1 topic summary (lowercase, split on whitespace/hyphens/underscores/slashes, drop common stopwords). If the intersection of the two token sets is **empty** → divergent session.

**Divergent path:**
1. Do NOT overwrite `folder_path/HANDOFF.md`. Leave the state folder's HANDOFF untouched.
2. Fall through to Step 5a.5.
3. **Surface a breadcrumb in the Step 6 summary:**
   ```
   ⚠ State/session divergence detected
     Active sub-project: [state.task_name] ([state.folder_relative])
     Session topic:      [Step 1 topic summary]
     State HANDOFF preserved; session captured in <PROJECT_ROOT>/SESSION_LOG.md.
   ```

**Normal Rule 2 path (intersection non-empty):**
1. Read `folder_path`, `task_name`, `folder_relative` from state.
2. Overwrite logging (same as Rule 1).
3. Write `folder_path/HANDOFF.md`.
4. Global handoff: same infrastructure-only rule.
5. Return.

**Neither rule fired:**
- No CWD HANDOFF AND no state file → fall through to Step 5a.5.
- State exists but stale (>24h, not permanent) → fall through.

#### 5a.5. CWD-fallback routing (no active sub-project) — non-destructive

When neither Rule 1 nor Rule 2 fires:

1. **Do NOT touch project-root `HANDOFF.md`** — leave any existing file at `CWD_HANDOFF_PATH` exactly as-is. A project-root HANDOFF.md the user maintains by hand is theirs to manage; `/done` will not overwrite it without an explicit `/start-task`.

2. **Capture session content in project-root `SESSION_LOG.md` instead** (append-only, reverse-chronological). Target: `<PROJECT_ROOT>/SESSION_LOG.md`. If `PROJECT_ROOT` is empty, skip and fall through to Step 5b.

3. If `SESSION_LOG.md` doesn't exist, create with the canonical header.

4. **Prepend the session entry** using the same block format as Step 3.

5. **Fall through to Step 5b** — the global handoff still gets written.

6. **Step 6 summary:** show `Handoff (scoped): <PROJECT_ROOT>/SESSION_LOG.md [via: cwd-project-log] [appended]` and `Project HANDOFF.md: preserved (no active sub-project — run /start-task to write a scoped HANDOFF)`.

**Why this design:** the destructive code path (silently overwriting project-root HANDOFF.md) is removed, not guarded. No prompt-dismissal or transcription error can restore the failure mode. Cross-session context is still captured via append-only SESSION_LOG.md.

#### 5b. Standard handoff (all other cases)

Generate the handoff note (≤30 lines) and overwrite `~/.claude/handoff.md` (or your equivalent) for SessionStart-hook resumption.

**Key rules:**
- Max 30 lines (Working Artifacts lines don't count — they're pointers)
- Working Artifacts section only appears when artifacts were saved
- Use **absolute paths** in Key Files; **checkboxes** for Next Steps
- In `quick` mode: omit the Context section
- Active Decisions: only decisions constraining the *next* session
- Include `SESSLOG:[YYYY-MM-DD HH:MM]` cross-reference

```markdown
# Handoff — [YYYY-MM-DD]
SESSLOG:[YYYY-MM-DD HH:MM]

## Session Topic
[1-line summary]

## Active Decisions
- [Decision constraining next session]

## Key Files
- [absolute path to important file]

## Next Steps
- [ ] [Most important next step]
- [ ] [Other follow-ups]

## Working Artifacts
- [path/to/artifact] — [what it contains]

## Context
[1-2 sentences for the next session to pick up seamlessly]
```

**Overwrite logging:** Before overwriting, if the existing file is non-empty, append to the global session log: `*Previous handoff overwritten: [topic from old handoff]*`.

### Step 6: Summary

```
────────────────────
SESSION CAPTURED
────────────────────
Topic: [summary]
Decisions: [N] | Questions: [N] | Follow-ups: [N] | Artifacts: [N]
[If working artifacts saved:] Working artifacts saved: [N] files → [directory path]
[If pruning ran:] Pruned: [N] entries → session-log-archive.md
[If retro flag fired:] Watch-list: [M new, K incremented]
Logged to: session-log.md
Handoff (scoped): [path]  [via: sub-project / cwd-project-log / global]  [written / appended / skipped]
Handoff (global): [path] [written / skipped]
[If v1.12 cwd-fallback path fired:] Project HANDOFF.md: preserved (no active sub-project — run /start-task to write a scoped HANDOFF)

[If divergence detected:]
⚠ State/session divergence — see breadcrumb above

[If open questions exist:]
⚠ [N] open questions — pick these up next session

[If Duration is Extended and retro flag was NOT used:]
ℹ Extended session — if hypotheses or patterns repeated across sessions, re-run with: /done retro

[If follow-ups exist:]
Next time: [most important follow-up item]
────────────────────
```

## Customization Points

- **Log file location:** Default `~/Documents/session-log.md`. Adjust to your preferred location.
- **Handoff file location:** Default `~/.claude/handoff.md` (read by SessionStart hook). Adjust if your hook reads from elsewhere.
- **Working-notes directory:** Default `~/Documents/working-notes/`. Adjust as needed.
- **Archive retention:** 60-day prune threshold or 1,500-line trigger — adjust per your tolerance.
- **Sub-project routing:** Requires the optional `/start-task` skill to populate `.claude/active-subproject.json`. Without it, only Rule 1 (CWD precedence) and Step 5a.5 (project-root SESSION_LOG.md) fire — both work fine without state files.

## Error Handling

- **No substantive content:** "Nothing to capture — session was too brief." Exit.
- **Session log write fails:** Display the entry in the terminal so you can manually save it.

## Design Notes

- **Complements session-closing patterns** — those suggest *improvements* (new skills, rules, agents). This skill captures *artifacts* (decisions, questions, follow-ups).
- **No MCP tools needed** — pure filesystem operation.
- **Skip-gate audit:** When working artifact scan is skipped, the reason is logged. Grep for `SKIPPED artifact scan` to detect over-firing.
- **SESSLOG cross-references:** Both session log entries and handoff notes include `SESSLOG:[YYYY-MM-DD HH:MM]` for grep-able traceability.

## Log Performance

```bash
echo "$(date +%Y-%m-%d),done,TOOL_CALLS,NOTES" >> ~/.claude-assistant/logs/skill-performance.csv
```

Replace TOOL_CALLS with best estimate and NOTES with brief summary (e.g., "3-decisions-2-followups-handoff").
