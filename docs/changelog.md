---
hide:
  - navigation
description: What's new on claudeblattman.com — April 2026 content update covering session discipline, sub-project routing, the meeting loop, weekly review, /recall, and dial-back prompting.
---

# What's New — April 2026

A month of workflow improvements, batched into two launches. Launch 1 is live below. Launch 2 follows in 2–3 weeks once a couple of pieces have earned their keep.

!!! tip "TL;DR"
    Three threads run through this update:

    1. **Session discipline** — how to run long work across `/rewind`, `/compact`, `/clear`, `/done`, and plan mode without losing context.
    2. **Sub-project routing** — multi-task projects that don't collapse under their own sprawl.
    3. **The boring daily workflow that earns its keep** — meeting loop, weekly review, `/recall` for searching past sessions, and why I stripped ceremonial emphasis from my skills.

---

## How the pieces fit

A normal workflow day on this stack:

1. **Morning** — `/morning-brief` runs before I sit down. I open the inbox; triage labels are already applied.
2. **First call** — `/pre-meeting-brief` pulls context from WhatsApp, Gmail, Granola, and Google Docs. I read it on the way.
3. **During the call** — Granola records. Claude Code stays idle.
4. **After the call** — `/post-meeting` drafts the follow-up email with decisions and action items extracted from the transcript.
5. **Between calls** — deep in a paper or proposal. When the session fills up, `/rewind` for wrong paths, `/compact <hint>` for stale exploration, `/done` when it's time to hand off to another machine.
6. **Stuck on something I've solved before?** — `/recall` searches every past Claude Code and Codex transcript. Usually finds the answer in the second or third result.
7. **Week end** — `/weekly-review` synthesizes project updates across transcripts, emails, and Google Docs. Takes an hour, covers a week.

Each piece has its own page below.

---

## Launch 1 — shipping this week

### Session management

How to run long sessions without losing your place. Decision matrix for `/rewind` vs `/compact <hint>` vs `/clear` vs starting fresh. Covers the four `/rewind` restore modes, when compaction hints actually steer the summary, and the real hook names (there's no `PostCompact` hook — compaction-aware reinjection ties to `SessionStart`). [Read more →](essentials/session-management.md)

### Sub-project routing

When a project has three or four parallel workstreams — say, a paper, a grant revision, a trip itinerary, and an RA pipeline — I don't want their context bleeding into each other. `/start-task` plus `.claude/active-subproject.json` handle the routing. Handoffs land in the right folder, and SessionStart knows which sub-task is active. [Read more →](workflows/sub-project-routing.md)

### Meeting workflow end-to-end

A four-step loop that replaces about 20 minutes of manual work per meeting. `/pre-meeting-brief` pulls context before. Granola records during. `/post-meeting` extracts decisions and action items after and drafts the follow-up email. [Read more →](workflows/meeting-workflow.md)

### Weekly review

The 3-marker system (done / in-progress / blocked) with batch updates and Granola transcript handling. Synthesizes a week of multi-project work in about an hour. Output is a single document I can hand to an RA, a collaborator, or future-me. [Read more →](workflows/weekly-review.md)

### `/recall` — search every past session

SQLite FTS5 full-text search with BM25 ranking over local Claude Code and Codex JSONL transcripts. Same-machine only. Installed it because I kept solving the same problem twice. Skill by [arjunkmrm](https://github.com/arjunkmrm) (MIT). [Read more →](workflows/recall.md)

### Dial-back discipline

Why I stripped `CRITICAL`, `YOU MUST`, and `ABSOLUTELY` from most of my skills. Ceremonial emphasis overtriggers Claude 4.5+ in tool-use paths and degrades output quality. The fix is positive examples instead of negative rules, and saving emphatic language for genuinely blocking security or data concerns. [Read more →](build-your-own/dial-back-discipline.md)

### Prompt architecture (partial — expanded)

Three new sections on the [Prompt Engineering](essentials/prompting.md) page: long-content ordering (put the document at the top, question at the bottom), system-vs-user prompt separation, and reusable constraint blocks (anti-hallucination, anti-bloat, scope guard, structured uncertainty, voice preservation). The full package — including a prompt-preferences template download — ships in Launch 2.

---

## Launch 2 — 2–3 weeks out

Gated on live-run validation and voice-pack sanitization. Shapes and scope may shift before publication.

- **Voice pack system** — register overlays (core voice + proposal + public writing + email) plus a critic-agent that flags drift at the line level. Shown as a complete pack with sanitized downloads.
- **Build your own reviewer** — the critic-agent pattern. Starts with one critic (voice or writing), then scales to a five-persona council for adoption decisions. Minimum 3-of-5 to proceed, retry once on rate limits, synthesis in the main agent because subagents can't nest.
- **Tips pipeline** — `/tips-scout` → `/tips-bookmarks` → `/tips-curate` → `/tips-integrate` with the five-persona council and auto-apply top three. Includes the "what broke on the first live run" section once there's real data behind it.
- **Prompt architecture (full)** — the complete page update with the [prompt-preferences template](downloads/index.md#templates) as a download you can paste into any project.

---

## Stay updated

- **[Email updates](https://buttondown.email/claudeblattman)** — low volume, easy opt-out.
- **[GitHub](https://github.com/chrisblattman/claudeblattman)** — star if useful; the repo is public.
- **[Feedback](mailto:claudeblattman+feedback@gmail.com?subject=Feedback)** — what's missing, what's wrong, what's confusing.
