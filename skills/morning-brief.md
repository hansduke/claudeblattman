# Morning Briefing

*Adapted for Outlook calendar (PDF) + TickTick workflow*

Generate a comprehensive daily morning briefing combining calendar, TickTick tasks, weather, and goal alignment into a single view.

## Prerequisites

**Required:**
- **TickTick MCP** -- for task management, deadlines, and reminders
- **Outlook calendar PDF** -- exported daily to `~/.claude-assistant/inbox/calendar.pdf`

**Recommended:**
- Config files (see First-Time Setup below):
  - `~/.claude-assistant/config/calendar-policy.md` -- working hours, city name, timezone
  - `~/.claude-assistant/config/goals.yaml` -- objectives and priorities for goal alignment

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
   push_level: moderate  # gentle | moderate | assertive
   objectives:
     - name: "Example project"
       weight: high
       status: active
       next_step: "Draft section 3"
   ```

4. **Daily calendar export:** Each morning, export your Outlook calendar to PDF and save to `~/.claude-assistant/inbox/calendar.pdf`

## Customization Points

| Setting | Where to Configure | Default |
|---------|-------------------|---------|
| **Weather city** | `calendar-policy.md` > Location > City | Omitted if not set |
| **Working hours** | `calendar-policy.md` > Working Hours | 8am-6pm |
| **Timezone** | `calendar-policy.md` > Timezone | America/Los_Angeles |
| **Goal alignment** | `goals.yaml` > objectives | Section omitted |
| **Deep work push level** | `goals.yaml` > push_level | `moderate` |

## Arguments

`$ARGUMENTS` can include:
- *(none)* -- full briefing
- `tomorrow` -- show tomorrow's schedule/tasks instead of today
- `no-tasks` -- skip the TickTick tasks phase

Multiple arguments can be combined: `tomorrow no-tasks`, etc.

## Instructions

### Phase 1: Read Config Files

Read available config files. Missing files are not errors -- skip the corresponding sections.

1. Read `~/.claude-assistant/config/calendar-policy.md` -- extract working hours, city name, timezone
2. Read `~/.claude-assistant/config/goals.yaml` -- extract objectives, push_level, active priorities

If a config file is missing, note it internally and continue. The briefing adapts to available data.

### Phase 2: Calendar Data

Read the Outlook calendar PDF from `~/.claude-assistant/inbox/calendar.pdf`.

Use the Read tool to read the PDF file. Extract:
- All events for today (or tomorrow if `tomorrow` argument)
- Event times, titles, and any attendee/location info visible
- All-day events

**Processing:**
- Sort by start time (all-day events first)
- Note any events that span multiple days

If the PDF is missing or unreadable, report: "Calendar PDF not found at ~/.claude-assistant/inbox/calendar.pdf -- please export from Outlook."

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
Query for tasks marked as high priority (priority = 1 or 2 in TickTick).

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

**HARD DEADLINES** -- Has hard-deadline keywords AND due within 3 days (including today). Also: any item marked high priority in TickTick (priority 1 or 2).

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
- Compare today's calendar events against active objectives
- Count goal-aligned vs admin/service meetings
- Identify top priority from highest-weight active objective
- If `push_level >= moderate` AND >2 hours free: add a focus nudge
- If `push_level = assertive` AND <2 hours free: add a deep work alert
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
5. Goal-aligned work (from goals.yaml)
[Number them in suggested order of importance]

## Goal Alignment
- Today: [N] meetings ([M] align with goals, [K] are admin/service)
  - [event name] -> [objective name] (if aligned)
- [N] hours unscheduled -- top priority: [specific next step from goals.yaml]
[If push_level >= moderate AND >2 hours free:]
  Focus nudge: [specific actionable next step on top-priority task]
[If push_level = assertive AND <2 hours free:]
  !! Deep work alert: Less than 2 hours unscheduled today. Consider declining [lowest-priority meeting].

## Today's Schedule
- [time range]  [event name]
- [time range]  [event name]
- ...
[If no events: "No events scheduled today"]
**[N] hours free** (of [M] available, [start]-[end])

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
- **Calendar PDF missing**: Report location and ask user to export from Outlook.
- **Calendar PDF unreadable**: Report error and continue with other sections.
- **WebSearch fails**: Omit weather line.
- **Config file missing**: Skip dependent sections, note in internal log.
- **goals.yaml malformed**: Skip goal alignment section, continue with briefing.

## Examples

```
/morning-brief                    # Full briefing
/morning-brief tomorrow           # Tomorrow's view
/morning-brief no-tasks           # Calendar only, skip TickTick
```

## Performance Logging

After completing all phases, log this run:
```bash
echo "$(date +%Y-%m-%d),morning-brief,TOOL_CALLS,NOTES" >> ~/.claude-assistant/logs/skill-performance.csv
```
Replace TOOL_CALLS with approximate count of tool uses this run. Replace NOTES with brief volume info (e.g., "8 tasks 4 meetings"). Do not skip this step.
