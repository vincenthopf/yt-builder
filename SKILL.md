---
name: yt-builder
description: >
  Transform YouTube tutorials into structured build plans. Takes a YouTube URL,
  transcribes with AssemblyAI, extracts metadata and resources, researches the
  topic landscape, and produces an improved step-by-step build plan. Optionally
  executes the plan. Use when the user provides a YouTube tutorial URL and wants
  to build what the video teaches. Also triggered by /yt-builder command.
---

# YT Builder

Transform YouTube tutorials into structured, improved build plans — and optionally execute them.

## Quick Reference

```
Phase 0: Setup        → Check deps, AssemblyAI API key, validate URL
Phase 1: Extraction   → Run extract.py, launch 3 research agents
Phase 2: Analysis     → Structure instructions, merge research, flag gaps
Phase 3: Plan         → Present build plan, user chooses reference or execute
Phase 4: Execute      → Build the artifact (only if user chooses)
```

---

## Phase 0: Setup

Before anything else, verify the environment is ready.

### Check Dependencies

Run a quick check:
```bash
which yt-dlp && which ffmpeg && python3 -c "import assemblyai" 2>/dev/null && echo "OK" || echo "MISSING"
```

If anything is missing, tell the user and offer to run the init script:
```bash
bash <skill-dir>/scripts/init.sh
```

### Check AssemblyAI API Key

The skill requires an AssemblyAI API key. Check if it's set:
```bash
python3 -c "
import os
from pathlib import Path
# Check common .env locations
for p in [Path('~/.claude/skills/yt-builder/.env'), Path('.env'), Path('~/.env')]:
    p = p.expanduser()
    if p.is_file():
        for line in open(p):
            if 'ASSEMBLYAI_API_KEY' in line and 'your-api-key-here' not in line:
                print('configured'); exit()
if os.environ.get('ASSEMBLYAI_API_KEY', '') and os.environ['ASSEMBLYAI_API_KEY'] != 'your-api-key-here':
    print('configured'); exit()
print('missing')
"
```

If the key is missing, guide the user through setup:

1. "You need an AssemblyAI API key for transcription. It takes about 2 minutes:"
2. "Go to https://www.assemblyai.com/ and sign up (you get $50 in free credits)"
3. "Copy your API key from the dashboard"
4. "I'll create a .env file for you — just paste the key"

Once the user provides the key, write it to `<skill-dir>/.env`:
```
ASSEMBLYAI_API_KEY=<their-key>
```

### Validate URL

Check that the input looks like a YouTube URL (contains `youtube.com` or `youtu.be`). If not, tell the user and ask for a valid URL.

---

## Phase 1: Extraction

### Run the Extraction Script

```bash
python3 <skill-dir>/scripts/extract.py "YOUTUBE_URL" -o .yt-builder
```

For videos over 20 minutes, run this in the background. The script prints the working directory path to stdout.

The script creates `.yt-builder/<video-id>/` with:
- `metadata.json` — title, channel, duration, tags, categories
- `transcript.txt` — full transcript with speaker labels
- `transcript_timestamps.json` — utterances with timestamps
- `chapters.json` — video chapters with timestamps (may be empty)
- `description.txt` — raw video description
- `resources.json` — extracted GitHub repos, URLs, packages
- `research/` — empty directory for research agent outputs

### Read Initial Context

After extraction completes, read:
1. `metadata.json` — to understand what the video is about
2. `chapters.json` — to see if there's structural scaffolding
3. `resources.json` — to see what resources the creator provided
4. First ~200 lines of `transcript.txt` — to get enough context for research queries

Do NOT read the full transcript into context yet. You need the topic and tools, not the full content.

### Launch Research Agents

Launch 3 research sub-agents in parallel. Each writes its findings to a file in the `research/` directory. Use the Agent tool with `run_in_background: true` for all three.

**Agent 1 — Topic & Concept Landscape:**
```
Research the broader landscape around [TOPIC FROM VIDEO].
- What is this technology/approach and why does it matter?
- What are current best practices (as of today's date)?
- What are common architectures or patterns?
- What has changed recently that a tutorial might not reflect?

Write findings to: [WORK_DIR]/research/topic-landscape.md
Keep it concise — bullet points, not essays. Focus on what would help someone
build this correctly today, not what the tutorial might already cover.
```

**Agent 2 — Tools & Libraries:**
```
Research the specific tools and libraries mentioned in this tutorial: [LIST FROM METADATA/TRANSCRIPT].
For each tool/library:
- Current latest version
- Any breaking changes since the tutorial was published ([UPLOAD_DATE])
- Known issues or gotchas
- Better alternatives that have emerged since

Write findings to: [WORK_DIR]/research/tools-libraries.md
Focus on actionable information: version numbers, migration notes, deprecation warnings.
```

**Agent 3 — Related Approaches & Pitfalls:**
```
Research how others approach building [WHAT THE TUTORIAL BUILDS].
- What do other tutorials/guides recommend differently?
- What are the most common mistakes or pitfalls?
- Are there complementary resources (official docs, starter repos)?
- What do people in forums/discussions say about this approach?

Write findings to: [WORK_DIR]/research/related-approaches.md
Focus on practical warnings and tips that complement the tutorial.
```

---

## Phase 2: Analysis

Wait for all research agents to complete before starting analysis.

### Read All Inputs

Now read the full set of extracted data:
1. `transcript.txt` — the full transcript
2. `chapters.json` — structural scaffold (if available)
3. `resources.json` — creator-provided resources
4. `research/topic-landscape.md`
5. `research/tools-libraries.md`
6. `research/related-approaches.md`

### Detect Video Type

Determine whether this is a **tutorial video** (builds something step by step) or a **theory video** (explains concepts without building).

Signals of a tutorial:
- Imperative instructions ("install this", "create a file", "run this command")
- Code or config being described
- Sequential build steps
- GitHub repo in description

Signals of a theory video:
- Conceptual explanations without implementation
- Comparisons between approaches
- Architecture discussions
- No code or commands mentioned

### Extract Build Instructions (Tutorial Videos)

If chapters exist, use them as the primary structural scaffold:
- Each chapter becomes a section in the build plan
- Extract the specific instructions within each chapter's timestamp range
- Cross-reference chapter titles with actual transcript content

If no chapters exist, extract structure from the transcript:
- Identify natural breakpoints (topic changes, "now let's...", "next we...")
- Group related instructions into logical steps
- Impose sequential order even if the tutorial jumps around

For each step, extract:
- **What to do** — the concrete action (install X, create Y, configure Z)
- **Why** — the reasoning if given
- **Code/commands** — any specific code, commands, or config mentioned
- **Resources** — relevant links from description or research

### Handle Theory Videos

If the video is primarily theoretical:
1. Summarize the key concepts explained
2. Identify practical applications of those concepts
3. Suggest 1-3 concrete build projects that would apply the concepts
4. For each suggestion, outline what you would build, what tools you'd use, and why
5. Note which concepts from the video would be applied in each project

Frame this as: "This video explains [concepts]. Here's how you could apply them practically."

### Cross-Reference & Improve

For both video types:

**Version check:** Compare tools/versions mentioned in the tutorial against research findings. If the tutorial uses an old version, note the current version and any migration steps needed.

**Quality improvements:** Identify places where the tutorial's approach could be improved:
- Security issues (hardcoded secrets, insecure defaults)
- Deprecated APIs or packages
- Missing error handling that would cause real problems
- Better alternatives discovered through research
- Missing steps that the tutorial assumes the viewer knows

For each improvement, explain WHAT you're changing and WHY. This is the educational layer — the user should understand not just that the plan differs from the tutorial, but why the plan is better.

**Visual gap detection:** Flag moments where the transcript suggests information is being conveyed visually but not verbally:
- "as you can see here..."
- "click on this button..."
- "drag this over to..."
- "it should look like this..."
- References to specific UI elements without describing them
- Code being shown but not read aloud

Mark these as `[VISUAL GAP]` in the plan with a note about what information might be missing.

**Resource integration:** Check if the description contains a GitHub repo. If so:
- Note it prominently — the repo may contain the complete code
- The build plan should reference it as a verification source
- If the user executes, offer to clone it as a starting point or reference

---

## Phase 3: Plan

Present the structured build plan to the user. Write the plan to `.yt-builder/<video-id>/build-plan.md` AND present it in the conversation.

### Plan Format (Tutorial Videos)

```markdown
# Build Plan: [VIDEO TITLE]

**Source:** [VIDEO URL]
**Channel:** [CHANNEL NAME]
**Published:** [DATE] | **Duration:** [DURATION]

## Overview
[1-2 sentence summary of what this tutorial builds and the approach taken]

## Prerequisites
- [Required tools with specific versions]
- [Required accounts or API keys]
- [Required knowledge or setup]

## Resources from Video
- [GitHub repo if available]
- [Key links from description]

## Build Steps

### Step 1: [Step Title]
[What to do — specific, actionable instructions]

[Code/commands if applicable]

[VISUAL GAP] [if applicable — what information might be missing]

### Step 2: ...
[continue for all steps]

## Improvements Over Tutorial
- **[Improvement]**: [What was changed] — [Why it's better]
- ...

## Research Insights
- [Genuinely useful findings from research agents]
- [Version updates, alternatives, pitfalls to be aware of]

## Known Gaps
- [Visual information that couldn't be extracted]
- [Assumptions made due to missing information]
```

### Plan Format (Theory Videos)

```markdown
# Build Suggestions: [VIDEO TITLE]

**Source:** [VIDEO URL]
**Channel:** [CHANNEL NAME]

## Concepts Covered
[Summary of key concepts from the video]

## Practical Build Suggestions

### Suggestion 1: [Project Name]
**What:** [What you'd build]
**Why:** [Which concepts from the video this applies]
**How:** [High-level approach and tools]
**Steps:** [Ordered build steps]

### Suggestion 2: ...

## Resources
- [Relevant links from research and description]
```

### User Choice

After presenting the plan, ask the user:

"The build plan is ready. Would you like to:
1. **Use as reference** — keep the plan in `.yt-builder/` for your own implementation
2. **Execute** — I'll build it following this plan
3. **Modify** — adjust the plan before deciding"

---

## Phase 4: Execute

Only enter this phase if the user explicitly chooses to execute.

### Setup

- If a GitHub repo was found in the description, ask the user if they want to clone it as a starting point or build from scratch
- Create the project directory structure as outlined in the plan
- Install dependencies listed in prerequisites

### Build

Follow the build plan step by step:
- Execute each step in order
- After completing each major section, briefly note progress
- If a step involves a `[VISUAL GAP]`, use research findings and your own knowledge to fill in the most likely correct implementation. Note that you're inferring.
- If you hit a blocker you can't resolve, stop and explain the issue rather than guessing

### Verify

After building:
- Run any tests if the project has them
- Check for syntax errors in generated code
- Verify that file structure matches what the plan described
- Note anything that couldn't be verified automatically

---

## Error Handling

| Situation | Action |
|-----------|--------|
| extract.py fails with exit code 1 | Missing dependency — offer to run init.sh |
| extract.py fails with exit code 2 | Download failure — check URL, ask user to verify |
| extract.py fails with exit code 3 | Transcription failure — check AssemblyAI status |
| extract.py fails with exit code 4 | Missing API key — run guided onboarding |
| Transcript is very short (<100 words) | Video may be mostly visual — warn user about limited extraction |
| No chapters AND transcript is non-linear | Warn user that plan structure is best-effort |
| Research agents fail | Continue without research — note reduced quality |
| Video is not in English | Warn user — v1 is English-only, quality may be poor |

---

## Context Management

- All extracted data lives in `.yt-builder/<video-id>/` — never dump it all into context at once
- Research agents write to files, not to main context
- Read transcript in sections when analyzing (chapters help with this)
- The build plan is the only artifact that should be fully in context during Phase 3
- During execution (Phase 4), reference the plan file rather than keeping the full plan in context
