<p align="center">
  <img src="assets/banner.png" alt="YT Builder" width="100%" />
</p>

<p align="center">
  <strong>Turn YouTube tutorials into structured build plans — and optionally execute them.</strong>
</p>

<br />

<p align="center">
  <a href="https://github.com/vincenthopf/yt-builder/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/platform-macOS_%7C_Linux_%7C_Windows-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/transcription-AssemblyAI-0078FF?style=flat-square" alt="AssemblyAI" />
  <img src="https://img.shields.io/badge/skill-Claude_Code-6B4FBB?style=flat-square" alt="Claude Code Skill" />
</p>

<p align="center">
  <a href="#the-problem">Problem</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#how-it-works">How It Works</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#quick-start">Quick Start</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#the-pipeline">Pipeline</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#edge-cases">Edge Cases</a>
</p>

<br />

---

<br />

## The Problem

You find a YouTube tutorial. You watch 20 minutes. You mentally extract the steps. You open 6 tabs. You start building. You realize you missed something at minute 7. You scrub back. You pause. You type. You repeat.

**YouTube tutorials are the dominant format for learning how to build things — but video is a terrible medium for transferring buildable knowledge.**

YT Builder fixes the middle layer: it takes the tutorial, transcribes it with high accuracy, researches the broader landscape, and produces a **structured build plan** that's better than the tutorial itself.

<br />

## How It Works

```mermaid
graph LR
    A[YouTube URL] --> B[Transcribe]
    B --> C[Research]
    C --> D[Analyze]
    D --> E[Build Plan]
    E --> F[Execute]

    style A fill:#FF0000,stroke:#CC0000,color:#fff
    style B fill:#1a1a2e,stroke:#0078FF,color:#fff
    style C fill:#1a1a2e,stroke:#0078FF,color:#fff
    style D fill:#1a1a2e,stroke:#0078FF,color:#fff
    style E fill:#1a1a2e,stroke:#00C853,color:#fff
    style F fill:#1a1a2e,stroke:#444,color:#888,stroke-dasharray: 5 5
```

<table>
<tr>
<td width="50%">

**What you give it**

A YouTube tutorial URL.

**What you get back**

- Structured, step-by-step build plan
- Improvements over the tutorial with reasoning
- Current versions and alternatives from research
- Visual gap warnings where transcript is incomplete
- Resources extracted from video description
- Optional: the built artifact itself

</td>
<td width="50%">

**What makes it different**

- **Not just a transcript** — it extracts *instructions*
- **Research-enriched** — 3 parallel agents surface what the tutorial misses
- **Improved, not just reproduced** — security fixes, version updates, better practices
- **Educational** — explains *why* changes were made
- **Chapter-aware** — uses YouTube chapters as structural scaffolding

</td>
</tr>
</table>

<br />

## Quick Start

### Prerequisites

| Tool | Purpose |
|:-----|:--------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | The AI coding agent that runs the skill |
| [AssemblyAI API Key](https://www.assemblyai.com/) | High-accuracy transcription — $50 free credits on signup |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube audio download |
| [ffmpeg](https://ffmpeg.org/) | Audio processing |

### Install

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/vincenthopf/yt-builder.git ~/.claude/skills/yt-builder

# Install dependencies (idempotent, platform-aware)
bash ~/.claude/skills/yt-builder/scripts/init.sh

# Configure your AssemblyAI API key
cp ~/.claude/skills/yt-builder/.env.example ~/.claude/skills/yt-builder/.env
# Then edit .env and paste your key
```

### Use

In any Claude Code session:

```
/yt-builder https://www.youtube.com/watch?v=VIDEO_ID
```

Or paste a YouTube URL and say *"build what this tutorial teaches."*

<br />

## The Pipeline

<details>
<summary><kbd>Phase 0</kbd>&nbsp;&nbsp;Setup — Environment checks and guided onboarding</summary>

<br />

- Verifies `yt-dlp`, `ffmpeg`, and the AssemblyAI SDK are installed
- Checks for a valid AssemblyAI API key
- If anything is missing, walks you through setup step by step
- First-time onboarding completes in under 3 minutes

</details>

<details>
<summary><kbd>Phase 1</kbd>&nbsp;&nbsp;Extraction — Transcription, metadata, and parallel research</summary>

<br />

The `extract.py` script handles the mechanical work:

1. **Metadata fetch** via `yt-dlp --dump-json` — title, description, chapters, tags
2. **Description parsing** — extracts GitHub repos, npm packages, documentation links
3. **Audio download** — mp3 via yt-dlp
4. **Transcription** — AssemblyAI Universal 3 Pro with speaker diarization

Then Claude launches **3 research sub-agents in parallel**:

| Agent | Focus | Output |
|:------|:------|:-------|
| Topic Landscape | Broader context, best practices, recent changes | `research/topic-landscape.md` |
| Tools and Libraries | Current versions, breaking changes, alternatives | `research/tools-libraries.md` |
| Related Approaches | What others recommend, common pitfalls | `research/related-approaches.md` |

All outputs land in `.yt-builder/<video-id>/` — nothing bloats the main context.

</details>

<details>
<summary><kbd>Phase 2</kbd>&nbsp;&nbsp;Analysis — The hard part: transcript to instructions</summary>

<br />

This is where the real value lives. Claude:

- Uses **YouTube chapters** as structural scaffolding when available
- Extracts **ordered build instructions** from conversational narration
- Cross-references with **description resources** — GitHub repos, docs
- Merges **research findings** — flags version drift, suggests improvements
- Detects **visual gaps** where the tutorial shows something on screen that is never described verbally
- Identifies **improvements** over the tutorial with clear reasoning

For **theory videos** that explain concepts without building, it suggests practical implementations instead.

</details>

<details>
<summary><kbd>Phase 3</kbd>&nbsp;&nbsp;Plan — Structured build plan presented for review</summary>

<br />

```
Overview ─────────── what we're building and the approach
Prerequisites ────── tools, versions, accounts needed
Resources ────────── GitHub repos, docs from video description
Build Steps ──────── ordered, actionable, improved
  Step N ──────────── what to do, why, code/commands
  [VISUAL GAP] ────── flagged where info may be missing
Improvements ─────── what was changed and why
Research Insights ── version updates, alternatives, pitfalls
Known Gaps ───────── what couldn't be extracted from audio alone
```

You choose: **use as reference** or **execute**.

</details>

<details>
<summary><kbd>Phase 4</kbd>&nbsp;&nbsp;Execute — Build it (optional)</summary>

<br />

If you choose to execute, Claude:

- Sets up the project structure
- Follows the build plan step by step
- Uses description resources and clones GitHub repos if relevant
- Infers visual gaps using research and its own knowledge
- Verifies the build where possible

</details>

<br />

## Working Directory

All extracted data lives in `.yt-builder/<video-id>/`:

```
.yt-builder/
└── dQw4w9WgXcQ/
    ├── metadata.json               Video metadata
    ├── transcript.txt              Full transcript with speaker labels
    ├── transcript_timestamps.json  Timestamped utterances
    ├── chapters.json               Video chapters (if available)
    ├── description.txt             Raw video description
    ├── resources.json              Extracted URLs, repos, packages
    ├── build-plan.md               The structured build plan
    └── research/
        ├── topic-landscape.md      Broader context and best practices
        ├── tools-libraries.md      Version checks and alternatives
        └── related-approaches.md   Pitfalls and recommendations
```

<br />

## Configuration

Create a `.env` file in the skill directory:

```env
ASSEMBLYAI_API_KEY=your-key-here
```

> [!TIP]
> New accounts at [assemblyai.com](https://www.assemblyai.com/) get **$50 in free credits** — enough for dozens of tutorials.

<br />

## Edge Cases

| Scenario | Behavior |
|:---------|:---------|
| Tutorial with chapters | Chapters become the build plan skeleton — highest quality output |
| Tutorial without chapters | Structure inferred from transcript flow |
| Theory or concept video | Suggests practical build projects that apply the concepts |
| Visual-heavy tutorial | Flags `[VISUAL GAP]` markers where info is screen-only |
| Outdated tutorial | Research agents detect version drift and suggest updates |
| GitHub repo in description | Prominently noted, used as verification source |
| Non-English video | Warning issued — v1 is English-only |

<br />

## Standalone Extraction

The `extract.py` script can be used independently of the skill:

```bash
python3 scripts/extract.py "https://youtube.com/watch?v=..." [-o output-dir] [--keep-audio]
```

| Flag | Default | Description |
|:-----|:--------|:------------|
| `-o` | `.yt-builder` | Base output directory |
| `--keep-audio` | off | Retain the downloaded mp3 |

| Exit Code | Meaning |
|:----------|:--------|
| `0` | Success |
| `1` | Missing dependency |
| `2` | Download failure |
| `3` | Transcription failure |
| `4` | Missing API key |

<br />

## Roadmap

- [ ] Non-English tutorial support
- [ ] Playlist and batch processing
- [ ] Tutorial detection — classify video type before processing
- [ ] Visual information recovery via video frame extraction

<br />

---

<p align="center">
  <sub>Built as a <a href="https://docs.anthropic.com/en/docs/claude-code">Claude Code</a> skill. Paste a YouTube URL, get a build plan.</sub>
</p>
