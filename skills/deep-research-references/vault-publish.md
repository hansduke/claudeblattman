# Vault Publish — shared procedure

Invoked by `/deep-research` (Phase 5.5) and `/dr-synthesize` (Phase 5) to copy a finished
research brief into the Obsidian vault. **Default ON; suppressed by `--no-vault`.**

This is the single source of truth for vault publishing — both call sites resolve their
inputs and then run Steps A–F below. Step B is a *model* step (read the brief, fill semantic
fields); the rest is a bash skeleton that writes only what the model computed. **Run the bash
in Steps C–F verbatim** — the most common failure is a caller hand-rolling the frontmatter and
silently corrupting dollar figures (see the Step B warning).

## Inputs (resolve before calling)

- `BRIEF_FILE`  — absolute path to the publishable brief (synthesis preferred; see `deep-research.md` spec §1.2)
- `PROJECT_KEY` — e.g. `cdcr` / `ocs` / `working-notes`
- `TOPIC`, `DATE` (`$YYYY-MM-DD`), `RUN_ID`
- `VAULT_ROOT`  — from `config.md` (default `~/Documents/hans-vault`)
- `VAULT_FOLDER_OVERRIDE` — from `--vault`, else `""`

If `VAULT_ROOT` is empty/unset, **no-op** (publishing disabled) — print `VAULT_PUBLISH_SKIPPED: VAULT_ROOT unset` and return.

## Step A — choose destination folder (map below is the authority)

```bash
VAULT_ROOT="${VAULT_ROOT/#\~/$HOME}"
case "$PROJECT_KEY" in
  cdcr) VF="06 Reference/CDCR" ;;
  ocs)  VF="06 Reference/OCS" ;;
  *)    VF="06 Reference/Research" ;;
esac
[ -n "$VAULT_FOLDER_OVERRIDE" ] && VF="$VAULT_FOLDER_OVERRIDE"
DESTDIR="$VAULT_ROOT/$VF"; mkdir -p "$DESTDIR"
```

## Step B — model extracts semantic fields from BRIEF_FILE

Read `BRIEF_FILE` and produce these as **model outputs (not regex)**. Do not fabricate
beyond what the brief supports:

- `TITLE`       — from the first `# ` H1 (strip a trailing `: What …` tail if very long; keep < ~90 chars)
- `MAIN_IDEA`   — 1 sentence (steal from executive-summary bullet 1 or the brief's bottom-line line)
- `BOTTOM_LINE` — 1–3 sentences (the brief's own "Bottom line" if present)
- `TAGS`        — comma-joined `portfolio_tags` (domain tags from the topic + project key, e.g. `CDCR, aging-prisoners, sentencing`)
- `RELEVANCE`   — **exactly one of** `Essential` | `High` | `Medium` | `Low` (default `High`; `Essential` for principal-facing briefs). It is an ENUM, never a sentence.

> ⚠️ **CRITICAL — assign these via SINGLE-QUOTED heredocs, verbatim.** `MAIN_IDEA` and
> `BOTTOM_LINE` routinely contain `$` (dollar figures like `$49,016`), apostrophes (`LAO's`),
> and colons. If you build them with double quotes or a normal heredoc, the shell **expands
> `$49` to nothing and silently eats your figures**. The single-quoted heredoc delimiter
> (`<<'VPEOF'`) disables ALL expansion, and apostrophes are safe because nothing is quoted
> inside. Set every field this way, then run Steps C–F **exactly as written** — do not
> hand-roll the frontmatter or the INDEX writes.

```bash
# Fill each value LITERALLY between the markers (no escaping needed — single-quoted heredoc).
cat > /tmp/vp_title       <<'VPEOF'
<TITLE here>
VPEOF
cat > /tmp/vp_main_idea   <<'VPEOF'
<MAIN_IDEA here — dollar signs, apostrophes, colons all safe>
VPEOF
cat > /tmp/vp_bottom_line <<'VPEOF'
<BOTTOM_LINE here>
VPEOF
TITLE="$(cat /tmp/vp_title)"
MAIN_IDEA="$(cat /tmp/vp_main_idea)"
BOTTOM_LINE="$(cat /tmp/vp_bottom_line)"
TAGS='CDCR, aging-prisoners, sentencing'     # comma-joined; literal single quotes
RELEVANCE='High'                              # MUST be Essential|High|Medium|Low
```

## Step C — build the vault body

```bash
# BODY = brief content from the first H1 onward, with the project-internal
# '## Source Reports' block (if any) REMOVED (replaced by the callout in Step D).
# The skip flag MUST reset on the NEXT '## ' heading, not on '# ' (the H1). In a /dr-synthesize
# brief, '## Source Reports' is the FIRST section AFTER the H1, so an H1-reset never fires again
# and the entire body gets eaten — and because the surviving H1 leaves BODY non-empty, the no-H1
# fallback below never triggers (bug seen 2026-06-30: a 1.5 KB title-only brief was published).
BODY="$(awk '
  /^# /{p=1}
  !p{next}
  /^## Source Reports/{s=1; next}
  /^## /{s=0}
  {if(!s)print}
' "$BRIEF_FILE")"
# Fallback if there is no H1: strip YAML frontmatter, drop a leading '## Source Reports'
# section, keep the rest:
if [ -z "$BODY" ]; then
  BODY="$(awk 'BEGIN{fm=0;done=0} /^---$/{if(!done){fm=!fm; if(!fm)done=1; next}} done||!fm{print}' "$BRIEF_FILE" \
          | awk 'BEGIN{s=0} /^## Source Reports/{s=1;next} /^## /{if(s)s=0} {if(!s)print}')"
fi
```

## Step D — filename + write

Write the skeleton **exactly as below**. It is already injection-safe: every value is passed
as a quoted positional arg to `printf '...%s...' "$VAR"`, so `$`/apostrophes/colons in the
variables are never re-expanded or re-parsed. Do **not** substitute the values into the format
string. (For a single-arm publish rather than a synthesis, the `source:` line wording is
cosmetic — leave it.)

```bash
SAFE_TITLE="$(printf '%s' "$TITLE" | sed 's#[/:]# #g; s#  *# #g')"
DEST="$DESTDIR/${DATE} ${SAFE_TITLE} — Research Brief.md"
[ -f "$DEST" ] && echo "WARN overwriting existing $DEST"
SRCDIR="$(dirname "$BRIEF_FILE")"
{
  printf -- '---\n'
  printf 'title: "%s"\n' "$TITLE"
  printf 'date: %s\n' "$DATE"
  printf 'source: "Deep-research synthesis (run_id %s)"\n' "$RUN_ID"
  printf 'type: report-brief\nbrief_type: INTERNAL\n'
  printf 'portfolio_tags: [%s]\n' "$TAGS"
  printf 'relevance: %s\n' "$RELEVANCE"
  printf 'main_idea: "%s"\n' "$MAIN_IDEA"
  printf 'bottom_line: "%s"\n' "$BOTTOM_LINE"
  printf 'source_reports: "%s"\n' "$SRCDIR"
  printf 'run_id: %s\n' "$RUN_ID"
  printf 'drive_source: n/a\n'
  printf -- '---\n\n'
  printf '> [!info] Source reports\n> Synthesized from fully-cited deep-research arms in `%s` — each arm has its own numbered source block with access dates.\n\n' "$SRCDIR"
  printf '%s\n' "$BODY"
} > "$DEST"
echo "VAULT_PUBLISHED: $DEST"
```

## Step E — INDEX rows (reuse the existing INDEX vars)

```bash
echo "| $DATE | $TOPIC | vault | (synthesis) | $PROJECT_KEY | $DEST |" >> ~/research-archive/INDEX.md
jq -nc --arg date "$DATE" --arg topic "$TOPIC" --arg tool "vault" \
   --arg project "$PROJECT_KEY" --arg path "$DEST" --arg run_id "$RUN_ID" \
   '{date:$date,topic:$topic,tool:$tool,project:$project,path:$path,run_id:$run_id}' \
   >> ~/research-archive/INDEX.jsonl
```

`jq -nc` (compact) is mandatory — INDEX.jsonl is JSON-Lines (one object per physical line).
A bare `jq -n` pretty-prints across multiple lines and breaks every per-line `jq` consumer.

## Step F — verification gate (fail loud; do not skip)

After writing, prove the artifact is well-formed. If any check fails, fix the cause and
re-run Steps D–E (do not leave a corrupt brief in the vault).

```bash
ok=1
# 1. Frontmatter parses as YAML.
ruby -ryaml -rdate -e 'YAML.safe_load(File.read(ARGV[0]).split(/^---\s*$/)[1], permitted_classes:[Date])' "$DEST" \
  || { echo "FAIL: YAML did not parse"; ok=0; }
# 2. relevance is the enum, not a sentence.
grep -Eq '^relevance: (Essential|High|Medium|Low)$' "$DEST" || { echo "FAIL: relevance not in enum"; ok=0; }
# 3. $-figure corruption canary: a ' ,' or '(,' or '~M'/'~B' in frontmatter signals eaten dollar amounts.
awk '/^---$/{n++} n==1' "$DEST" | grep -Eq '[(, ],[0-9]|~[MB][ ),]' && { echo "FAIL: looks like \$-figures were shell-expanded"; ok=0; }
# 4. INDEX.jsonl last row parses standalone (compact JSONL).
tail -1 ~/research-archive/INDEX.jsonl | jq -e . >/dev/null 2>&1 || { echo "FAIL: INDEX.jsonl last row not valid JSON Line"; ok=0; }
[ "$ok" = 1 ] && echo "VAULT_PUBLISH_VERIFIED: $DEST" || echo "VAULT_PUBLISH_NEEDS_FIX: $DEST"
```

## Guard against double-publish

- When the caller is `/dr-synthesize`, it publishes and then writes `vault_published: <DEST>`
  into the synthesis frontmatter. The `/deep-research` dispatch path (Phase 5.5) must NOT
  re-publish: it checks for that key (or an already-existing dated vault file for this run_id)
  and skips if present.
- `--publish <file>` (standalone backfill) always publishes regardless of the guard — it is
  an explicit user action.
