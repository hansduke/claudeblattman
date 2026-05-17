# Morning Briefing

*Adapted for Outlook calendar (PDF) + TickTick workflow*

Generate a comprehensive daily morning briefing combining calendar, TickTick tasks, weather, and goal alignment into a single view.

## Prerequisites

**Required:**
- **TickTick MCP** -- for task management, deadlines, and reminders
- **Outlook calendar** -- one of:
  - JSON sync via `sync_calendar.py` to Google Drive (preferred, auto-syncs from Surface Pro)
  - PDF export to `~/.claude-assistant/inbox/calendar.pdf` (manual fallback)

**Optional:**
- **email-search rig** -- for Email Highlights section (VIP inbox, action-needed, meeting prep context)
  - Location: `~/projects/code/email-search/`
  - Requires: Ollama running locally, index populated via nightly ingest
  - See `~/projects/code/email-search/email-rig.md` for integration details

**Recommended:**
- Config files (see First-Time Setup below):
  - `~/.claude-assistant/config/calendar-policy.md` -- working hours, city name, timezone, calendar paths
  - `~/.claude-assistant/config/goals.yaml` -- objectives and priorities for goal alignment
  - `~/.claude-assistant/config/email-policy.md` -- VIP sender list for email highlights

## First-Time Setup

1. **Create config directory:**
   ```bash
   mkdir -p ~/.claude-assistant/config
   mkdir -p ~/.claude-assistant/inbox
   mkdir -p ~/.claude-assistant/state
   mkdir -p ~/.claude-assistant/logs
   ```

2. **Create calendar-policy.md** with at minimum:
   ```markdown
   ## Working Hours
   - 8:00 AM to 6:00 PM

   ## Location
   - City: Sacramento
   - Timezone: America/Los_Angeles
   ```

3. **Create goals.yaml** (optional but recommended):
   ```yaml
   meta:
     quarter: "Q2-2026"
     push_level: moderate  # gentle | moderate | assertive
     next_review: "2026-06-15"

   objectives:
     - id: example-project
       name: "Example Project"
       weight: 0.30  # decimal weights should sum to 1.0
       status: active  # active | paused | dormant
       key_results:
         - id: kr-1
           description: "Complete phase 1 deliverables"
           progress: 0.0  # 0.0 to 1.0
           at_risk: false

   upcoming_deadlines:
     - date: "2026-06-01"
       description: "Report due to stakeholders"
       objective: example-project
   ```

4. **Calendar sync:**
   - **Preferred:** Run `sync_calendar.py` on Surface Pro -- syncs Outlook to `calendar.json` via Google Drive
   - **Fallback:** Export Outlook calendar to PDF and save to `~/.claude-assistant/inbox/calendar.pdf`

## Customization Points

| Setting | Where to Configure | Default |
|---------|-------------------|---------|
| **Calendar JSON path** | `calendar-policy.md` > Outlook Calendar | Google Drive sync path |
| **Calendar PDF path** | `calendar-policy.md` | `~/.claude-assistant/inbox/calendar.pdf` |
| **Weather city** | `calendar-policy.md` > Location > City | Omitted if not set |
| **Working hours** | `calendar-policy.md` > Working Hours | 8am-6pm |
| **Timezone** | `calendar-policy.md` > Timezone | America/Los_Angeles |
| **Goal alignment** | `goals.yaml` > objectives + key_results | Section omitted |
| **Deep work push level** | `goals.yaml` > meta.push_level | `moderate` |
| **Upcoming deadlines** | `goals.yaml` > upcoming_deadlines | Merged with TickTick |
| **VIP senders** | `email-policy.md` > VIP List (Tier 1 & 2) | Section omitted if no rig |
| **Email time window** | Hardcoded | 24 hours for inbox, 7 days for meeting prep |

## Arguments

`$ARGUMENTS` can include:
- *(none)* -- full briefing (markdown output)
- `pdf` -- generate PDF for reMarkable Color tablet
- `tomorrow` -- show tomorrow's schedule/tasks instead of today
- `no-tasks` -- skip the TickTick tasks phase
- `no-email` -- skip the Email Highlights phase

Multiple arguments can be combined: `pdf tomorrow`, `no-email no-tasks`, etc.

### PDF Output

When `pdf` argument is provided:
- Generates a bullet-journal style PDF optimized for reMarkable Color (4:3 ratio, high contrast colors)
- Output: `~/.claude-assistant/output/daily-YYYY-MM-DD.pdf`
- Requires: `pip install weasyprint jinja2`
- Uses template: `~/.claude-assistant/templates/daily-brief.html`

## Instructions

### Phase 1: Read Config Files

Read available config files. Missing files are not errors -- skip the corresponding sections.

1. Read `~/.claude-assistant/config/calendar-policy.md` -- extract working hours, city name, timezone
2. Read `~/.claude-assistant/config/goals.yaml` -- extract:
   - `meta.push_level` (gentle/moderate/assertive)
   - `objectives[]` with status=active, sorted by weight (highest first)
   - `key_results[]` within each objective, noting any with `at_risk: true`
   - `upcoming_deadlines[]` for hard deadline detection

If a config file is missing, note it internally and continue. The briefing adapts to available data.

### Phase 2: Calendar Data

Check for calendar data in order of preference:

**2a. Primary: Outlook JSON sync**
Check `~/Library/CloudStorage/GoogleDrive-michael.redding@gov.ca.gov/My Drive/email-search/calendar.json`

If the file exists and was modified within the last 24 hours, use it as the authoritative source. Parse the JSON to extract:
- All events for today (or tomorrow if `tomorrow` argument)
- Event times, titles, locations, and attendees
- All-day events

**2b. Fallback: PDF export**
If JSON is missing or stale (>24 hours old), check `~/.claude-assistant/inbox/calendar.pdf`.

Use the Read tool to read the PDF file and extract the same fields.

**Processing:**
- Sort by start time (all-day events first)
- Note any events that span multiple days

**Error reporting:**
- If JSON is stale: "Outlook calendar not synced (last sync: [date]) -- run sync_calendar.py on Surface Pro."
- If both missing: "No calendar data available -- sync calendar.json from Surface Pro or export PDF to ~/.claude-assistant/inbox/calendar.pdf"

### Phase 2.5: Email Highlights (skip if `no-email`)

Pull recent email context from the email-search rig. This phase is optional -- skip gracefully if the rig is unavailable or Ollama isn't running.

**2.5a. Check rig availability:**

Test that the email-search rig is working:
```bash
~/projects/code/email-search/.venv/bin/python -m src.search_cli --top 1 "test query" 2>/dev/null
```

Exit code interpretation:
- `0` -- rig is healthy, proceed
- `3` -- integrity failure; add note to briefing: "Email index needs repair -- run verify_integrity.py"
- `4` -- no index found; skip phase silently (ingest hasn't run yet)
- Any other error -- skip phase silently (Ollama may not be running)

If exit code ≠ 0 and ≠ 3, skip this entire phase without error message.

**2.5b. Load VIP sender list:**

Read `~/.claude-assistant/config/email-policy.md` if not already loaded in Phase 1.

Extract email addresses from the VIP List tables (Tier 1 and Tier 2). Build a list of VIP email patterns for matching.

If email-policy.md is missing or has no VIP entries, skip VIP matching but continue with action-needed detection.

**2.5c. Query VIP emails (last 24 hours):**

For each VIP sender (up to 10), run:
```bash
~/projects/code/email-search/.venv/bin/python -m src.search_cli \
    --since 24h --top 2 --folder Inbox "from [VIP name or email]"
```

Collect results, deduplicate by email ID.

**2.5d. Query action-needed emails:**

Search for emails with action keywords:
```bash
~/projects/code/email-search/.venv/bin/python -m src.search_cli \
    --since 24h --top 5 --folder Inbox "urgent OR deadline OR action needed OR review needed OR please respond OR EOD OR COB"
```

Filter results to exclude any already captured in VIP list.

**2.5e. Meeting prep context:**

Using attendee list from Phase 2 calendar data, identify unique attendee names/emails for today's meetings.

For each attendee (up to 5 most frequent across meetings), search for recent correspondence:
```bash
~/projects/code/email-search/.venv/bin/python -m src.search_cli \
    --since 7d --top 2 "from [attendee name]"
```

Pair each result with the meeting it's relevant to (match by attendee).

**2.5f. Compile Email Highlights:**

Build the Email Highlights data:
- **VIP count**: Number of unique VIP emails in last 24h
- **VIP emails**: List of {sender, subject, date, relative_time}
- **Action count**: Number of action-needed emails
- **Action emails**: List of {sender, subject, action_keyword}
- **Meeting context**: List of {meeting_title, meeting_time, attendee, thread_subject}

If all lists are empty, the section will show "No urgent emails in last 24 hours."

**Security note:** Do not write email body content to disk. Snippets from search results are acceptable for display only.

### Phase 3: TickTick Tasks (skip if `no-tasks`)

Query TickTick for tasks using the MCP tools.

**3a. Get all projects/lists:**
```
mcp__ticktick__get_projects
```

**3b. Get tasks due today:**
```
mcp__ticktick__get_tasks
```
Filter for tasks with due dates matching today (or tomorrow if `tomorrow` argument).

**3c. Get overdue tasks:**
Query for tasks with due dates before today.

**3d. Get high-priority tasks:**
Query for tasks marked as high priority (priority = 5 in TickTick).

TickTick priority values: 5 = High, 3 = Medium, 1 = Low, 0 = None.

**3e. Get Pending project tasks (for PDF output):**
Query tasks from the Pending project (ID: `69585988ebcdfd0000001486`):
```
mcp__ticktick__get_project_tasks with project_id="69585988ebcdfd0000001486"
```

**3f. Get quick wins (for PDF output):**
Identify quick-win tasks using these criteria:
- Tasks tagged "quick" in TickTick
- Tasks in an "Emails" project
- Tasks with "email" in the title (case-insensitive)

Search using:
```
mcp__ticktick__search_tasks with search_term="email"
mcp__ticktick__search_tasks with search_term="quick"
```

Extract for each task:
- Title
- Due date/time
- Priority level
- Project/list name
- Any tags

### Phase 4: Weather

Use WebSearch to query "[City] weather today" (city from calendar-policy.md) and extract a one-line summary including temperature, conditions, and precipitation chance.

Example: "Sacramento: 72F, sunny, 0% chance rain"

If WebSearch fails or no city configured, omit the weather line.

### Phase 5: Tomorrow Preview

Using calendar data from Phase 2 and TickTick tasks from Phase 3:

- **Normal days:** Show tomorrow's events and tasks due tomorrow
- **Fridays:** Replace with "Weekend Preview" showing Saturday AND Sunday

### Phase 6: Assemble & Display Briefing

#### Task Classification Logic

Classify each TickTick task into groups:

**HARD DEADLINES** -- Has hard-deadline keywords AND due within 3 days (including today). Also: any item marked high priority in TickTick (priority = 5).

Hard-deadline keywords: `due`, `deadline`, `submit`, `file`, `renew`, `pay`, `invoice`, `reimburse`, `grant`, `IRB`, `contract`, `review`, `letter`, `slides`, `deck`, `send`, `deliver`, `final`, `revision`

Match case-insensitive against task title and description.

**DUE TODAY** -- Due date = target date, not classified as hard deadline.

**OVERDUE** -- Due date before target date. Sort oldest first (most days overdue at top).

Number all items sequentially across groups (1, 2, 3...) so you can reference them by number in follow-up.

#### Free Time Calculation

- Working window: from calendar-policy.md (default 8:00 AM to 6:00 PM = 10 hours)
- Sum meeting durations from today's calendar events
- Free hours = working hours - total meeting hours
- Display as: **[N] hours free** (of [M] available, [start]-[end])

#### Overdue Truncation

Show a maximum of 10 overdue items (oldest first). If more than 10:
`... and [N] more overdue tasks in TickTick`

#### Goal Alignment

If goals.yaml was loaded:
- Compare today's calendar events against active objectives (match by objective name/id)
- Count goal-aligned vs admin/service meetings
- Identify top priority: highest-weight active objective with incomplete key_results
- Surface any key_results marked `at_risk: true`
- Check `upcoming_deadlines[]` for items within 7 days -- add to Hard Deadlines section
- If `meta.push_level >= moderate` AND >2 hours free: add a focus nudge with specific key_result
- If `meta.push_level = assertive` AND <2 hours free: add a deep work alert
- Keep to 3-5 lines

#### Briefing Template

Compose the briefing in this format. Omit sections with no data. Use tomorrow's date if `tomorrow` argument was provided.

```
# Morning Briefing -- [Day of Week], [Month] [Date], [Year]
[Weather one-liner, e.g., "Sacramento: 72F, sunny, 0% chance rain"]

## Suggested Priorities
[Generate 3-5 suggested priorities based on:]
1. Hard deadline items (highest urgency)
2. High-priority TickTick tasks
3. Today's meetings that need prep
4. Overdue items worth acting on today
5. Goal-aligned work (from goals.yaml key_results with lowest progress)
[Number them in suggested order of importance]

## Goal Alignment
- Today: [N] meetings ([M] align with goals, [K] are admin/service)
  - [event name] -> [objective name] (if aligned)
- [N] hours unscheduled -- top priority: [highest-weight objective with incomplete key_results]
[If any key_results have at_risk: true:]
  At risk: [key_result description] ([objective name])
[If meta.push_level >= moderate AND >2 hours free:]
  Focus nudge: [lowest-progress key_result from top objective]
[If meta.push_level = assertive AND <2 hours free:]
  !! Deep work alert: Less than 2 hours unscheduled today. Consider declining [lowest-priority meeting].

## Today's Schedule
- [time range]  [event name]
- [time range]  [event name]
- ...
[If no events: "No events scheduled today"]
**[N] hours free** (of [M] available, [start]-[end])

## Email Highlights
[If VIP emails found:]
**VIP inbox** ([N] emails):
- [sender]: [subject] ([relative time, e.g., "2h ago"])
- ...

[If action-needed emails found:]
**Action needed** ([N]):
- [subject] from [sender]
- ...

[If meeting attendees had recent threads:]
**Meeting prep**:
- [Meeting title] @ [time]: Recent thread with [attendee] -- "[subject snippet]"
- ...

[If email rig unavailable: omit entire section]
[If no highlights: "No urgent emails in last 24 hours."]

## Hard Deadlines
  1. [task name] ([project]) (due [relative date]) !!
  ...
[If none: omit entire section]

## Tasks Due Today
  N. [task name] ([project]) ([time if set])
  ...
[If none: omit section]

## Tomorrow Preview
- [Events tomorrow]
- [Tasks due tomorrow]
[If nothing tomorrow: "Nothing scheduled for tomorrow"]
[ON FRIDAYS: Replace with "Weekend Preview" showing Sat + Sun grouped by day]

## Overdue ([N] items)
  N. [task name] ([project]) (N days overdue)
  ... [max 10 items, oldest first]
[If >10: "... and [N] more overdue tasks in TickTick"]
[If none: omit section]

To adjust tasks: tell me "defer 3 to Monday" or "mark 5 complete"
```

## Error Handling

- **TickTick MCP unavailable**: Report "TickTick unavailable -- check MCP configuration." Skip task sections.
- **Calendar JSON stale**: Report last sync date, suggest running sync_calendar.py.
- **Calendar JSON missing + PDF missing**: Report both locations, ask user to sync or export.
- **Calendar unreadable**: Report error and continue with other sections.
- **WebSearch fails**: Omit weather line.
- **Config file missing**: Skip dependent sections, note in internal log.
- **goals.yaml malformed**: Skip goal alignment section, continue with briefing.
- **Email rig unavailable**: Skip Email Highlights section silently (graceful degradation).
- **Email index integrity failure**: Note in briefing: "Email index needs repair -- run verify_integrity.py". Skip email section.
- **Ollama not running**: Skip Email Highlights section silently.
- **email-policy.md missing**: Skip VIP matching, but still show action-needed emails if rig is available.

## Examples

```
/morning-brief                    # Full briefing (markdown)
/morning-brief pdf                # Generate PDF for reMarkable
/morning-brief pdf tomorrow       # Tomorrow's PDF
/morning-brief tomorrow           # Tomorrow's view (markdown)
/morning-brief no-tasks           # Calendar only, skip TickTick
/morning-brief no-email           # Skip email highlights (faster if Ollama is slow)
/morning-brief no-tasks no-email  # Calendar and weather only
```

### Phase 7: PDF Generation (if `pdf` argument)

If the `pdf` argument was provided, generate a bullet-journal style PDF instead of markdown output.

**7a. Build JSON data structure:**
```json
{
  "date": "YYYY-MM-DD",
  "weather": "Sacramento: 72F, sunny",
  "top_of_mind": [
    "Calendar summary or conflict alerts",
    "At-risk key results from goals.yaml",
    "Weather alerts if any"
  ],
  "email_highlights": {
    "vip_count": 3,
    "vip_emails": [
      {"sender": "Nathan Barankin", "subject": "RE: OCS board seat", "time": "2h ago"}
    ],
    "action_count": 1,
    "action_emails": [
      {"sender": "DOF", "subject": "Budget response needed by EOD"}
    ],
    "meeting_context": [
      {"meeting": "BSCC Call", "time": "10:00", "attendee": "Sujie Shin", "thread": "Fellow placement update"}
    ]
  },
  "today_urgent": [
    {"title": "Task name", "project": "Project", "overdue": true, "high_priority": true, "days_info": "3 days overdue"}
  ],
  "today_quick": [
    {"title": "Quick task", "project": "Emails"}
  ],
  "projects": [
    {"name": "Project Name", "task_count": 12}
  ],
  "due_items": [
    {"title": "Due task", "project": "Project", "overdue": false, "days_info": "due today"}
  ],
  "pending_items": [
    {"title": "Waiting on response"}
  ]
}
```

**7b. Section content rules:**

| Section | Content | Limit |
|---------|---------|-------|
| **top_of_mind** | Weather alerts, calendar conflicts, at-risk goals, VIP email alerts | 3-4 items |
| **email_highlights** | VIP emails, action-needed, meeting prep threads (from Phase 2.5) | 5 VIP, 3 action, 5 meeting |
| **today_urgent** | Hard deadlines + high priority tasks, sorted by urgency (overdue days × priority) | 8-10 items |
| **today_quick** | Tasks tagged "quick" OR email-related tasks | 5-6 items |
| **projects** | Active projects sorted by open task count (exclude Someday, Pending, closed projects) | 6-8 projects |
| **due_items** | Overdue + due today, sorted by days overdue (oldest first) | 8 items |
| **pending_items** | Tasks from Pending project | 6-8 items |

If email-search rig is unavailable, omit `email_highlights` from JSON entirely (template should handle missing key gracefully).

**7c. Generate PDF:**
Pipe the JSON to the generator script:
```bash
echo '$JSON_DATA' | python3 ~/.claude-assistant/scripts/generate-daily-pdf.py
```

**7d. Report output:**
After generation, report: "PDF generated: ~/.claude-assistant/output/daily-YYYY-MM-DD.pdf"

Optionally offer to open or copy to reMarkable if rmapi is configured.

## Performance Logging

After completing all phases, log this run:
```bash
echo "$(date +%Y-%m-%d),morning-brief,TOOL_CALLS,NOTES" >> ~/.claude-assistant/logs/skill-performance.csv
```
Replace TOOL_CALLS with approximate count of tool uses this run. Replace NOTES with brief volume info (e.g., "8 tasks 4 meetings pdf"). Do not skip this step.
