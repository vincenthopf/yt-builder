<p align="center">
  <img src="assets/banner.png" alt="YT Builder Banner" width="100%" />
</p>

<h1 align="center">YT Builder</h1>

<p align="center">
  <strong>Turn YouTube tutorials into structured build plans — and optionally execute them.</strong>
</p>

<p align="center">
  <a href="#-how-it-works"><img src="https://img.shields.io/badge/How_It_Works-blue?style=for-the-badge" alt="How It Works" /></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-green?style=for-the-badge" alt="Quick Start" /></a>
  <a href="#-the-pipeline"><img src="https://img.shields.io/badge/Pipeline-red?style=for-the-badge" alt="Pipeline" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Skill-blueviolet?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQxIDAtOC0zLjU5LTgtOHMzLjU5LTggOC04IDggMy41OSA4IDgtMy41OSA4LTggOHoiLz48L3N2Zz4=" alt="Claude Code Skill" />
  <img src="https://img.shields.io/badge/Transcription-AssemblyAI-blue?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQxIDAtOC0zLjU5LTgtOHMzLjU5LTggOC04IDggMy41OSA4IDgtMy41OSA4LTggOHoiLz48L3N2Zz4=" alt="AssemblyAI" />
  <img src="https://img.shields.io/badge/Platform-macOS_%7C_Linux_%7C_Windows-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
</p>

<br />

---

<br />

## The Problem

You find a YouTube tutorial. You watch 20 minutes. You mentally extract the steps. You open 6 tabs. You start building. You realize you missed something at minute 7. You scrub back. You pause. You type. You repeat.

**YouTube tutorials are the dominant format for learning how to build things — but video is a terrible medium for transferring buildable knowledge.**

YT Builder fixes the middle layer: it takes the tutorial, transcribes it with high accuracy, researches the broader landscape, and produces a **structured build plan** that's better than the tutorial itself.

<br />

## ✨ How It Works

```
YouTube URL  ──→  Transcribe  ──→  Research  ──→  Analyze  ──→  Build Plan  ──→  Execute
                  (AssemblyAI)     (3 agents)     (Claude)      (structured)     (optional)
```

<table>
<tr>
<td width="50%">

### What you give it
A YouTube tutorial URL

### What you get back
- Structured, step-by-step build plan
- Improvements over the tutorial (with reasoning)
- Current versions & alternatives from research
- Visual gap warnings where transcript is incomplete
- Resources extracted from video description
- Optional: the built artifact itself

</td>
<td width="50%">

### What makes it different
- **Not just a transcript** — it extracts *instructions*
- **Research-enriched** — 3 parallel agents surface what the tutorial misses
- **Improved, not just reproduced** — security fixes, version updates, better practices
- **Educational** — explains *why* changes were made
- **Chapter-aware** — uses YouTube chapters as structural scaffolding

</td>
</tr>
</table>

<br />

## 🚀 Quick Start

### Prerequisites

| Tool | Purpose |
|------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | The AI coding agent that runs the skill |
| [AssemblyAI API Key](https://www.assemblyai.com/) | High-accuracy transcription ($50 free credits) |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube audio download |
| [ffmpeg](https://ffmpeg.org/) | Audio processing |

### Install

```bash
# Clone the skill into your Claude Code skills directory
git clone https://github.com/vincenthopf/yt-builder.git ~/.claude/skills/yt-builder

# Run the dependency installer
bash ~/.claude/skills/yt-builder/scripts/init.sh

# Add your AssemblyAI API key
cp ~/.claude/skills/yt-builder/.env.example ~/.claude/skills/yt-builder/.env
# Edit .env and add your key
```

### Use

In any Claude Code session:

```
/yt-builder https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Or just paste a YouTube URL and say "build what this tutorial teaches."

<br />

## 🔬 The Pipeline

<details>
<summary><strong>Phase 0: Setup</strong> — Environment checks & guided onboarding</summary>

<br />

- Verifies `yt-dlp`, `ffmpeg`, and AssemblyAI SDK are installed
- Checks for AssemblyAI API key
- If anything is missing, walks you through setup step by step
- First-time onboarding completes in under 3 minutes

</details>

<details>
<summary><strong>Phase 1: Extraction</strong> — Transcription + metadata + parallel research</summary>

<br />

The `extract.py` script handles the mechanical work:

1. **Metadata fetch** via `yt-dlp --dump-json` — title, description, chapters, tags
2. **Description parsing** — extracts GitHub repos, npm packages, documentation links
3. **Audio download** — mp3 via yt-dlp
4. **Transcription** — AssemblyAI Universal 3 Pro with speaker diarization

Then Claude launches **3 research sub-agents in parallel**:

| Agent | Focus | Writes to |
|-------|-------|-----------|
| Topic Landscape | Broader context, best practices, recent changes | `research/topic-landscape.md` |
| Tools & Libraries | Current versions, breaking changes, alternatives | `research/tools-libraries.md` |
| Related Approaches | What others recommend, common pitfalls | `research/related-approaches.md` |

All outputs land in `.yt-builder/<video-id>/` — nothing bloats the main context.

</details>

<details>
<summary><strong>Phase 2: Analysis</strong> — The hard part: transcript → instructions</summary>

<br />

This is where the real value lives. Claude:

- Uses **YouTube chapters** as structural scaffolding (when available)
- Extracts **ordered build instructions** from conversational narration
- Cross-references with **description resources** (GitHub repos, docs)
- Merges **research findings** — flags version drift, suggests improvements
- Detects **visual gaps** where the tutorial shows something on screen that's never described verbally
- Identifies **improvements** over the tutorial with clear reasoning

For **theory videos** (concepts without building), it suggests practical implementations instead.

</details>

<details>
<summary><strong>Phase 3: Plan</strong> — Structured build plan presented for review</summary>

<br />

The build plan includes:

```
├── Overview — what we're building and the approach
├── Prerequisites — tools, versions, accounts needed
├── Resources — GitHub repos, docs from video description
├── Build Steps — ordered, actionable, improved
│   ├── Step N — what to do, why, code/commands
│   └── [VISUAL GAP] — flagged where info may be missing
├── Improvements — what was changed and why
├── Research Insights — version updates, alternatives, pitfalls
└── Known Gaps — what couldn't be extracted from audio alone
```

You choose: **use as reference** or **execute**.

</details>

<details>
<summary><strong>Phase 4: Execute</strong> — Build it (optional)</summary>

<br />

If you choose to execute, Claude:

- Sets up the project structure
- Follows the build plan step by step
- Uses description resources (clones GitHub repos if relevant)
- Infers visual gaps using research + knowledge
- Verifies the build where possible

</details>

<br />

## 📁 Working Directory

Everything lives in `.yt-builder/<video-id>/`:

```
.yt-builder/
└── dQw4w9WgXcQ/
    ├── metadata.json              # Video metadata (title, channel, tags)
    ├── transcript.txt             # Full transcript with speaker labels
    ├── transcript_timestamps.json # Timestamped utterances
    ├── chapters.json              # Video chapters (if available)
    ├── description.txt            # Raw video description
    ├── resources.json             # Extracted URLs, GitHub repos, packages
    ├── build-plan.md              # The structured build plan
    └── research/
        ├── topic-landscape.md     # Broader context & best practices
        ├── tools-libraries.md     # Version checks & alternatives
        └── related-approaches.md  # What others recommend & pitfalls
```

<br />

## ⚙️ Configuration

Create a `.env` file in the skill directory:

```env
# Required
ASSEMBLYAI_API_KEY=your-key-here
```

Get your key at [assemblyai.com](https://www.assemblyai.com/) — new accounts get **$50 in free credits**.

<br />

## 🧠 How It Handles Edge Cases

| Scenario | Behavior |
|----------|----------|
| **Tutorial with chapters** | Chapters become the build plan skeleton — highest quality output |
| **Tutorial without chapters** | Structure inferred from transcript flow |
| **Theory/concept video** | Suggests practical build projects that apply the concepts |
| **Visual-heavy tutorial** | Flags `[VISUAL GAP]` markers where info is screen-only |
| **Old tutorial** | Research agents detect version drift and suggest updates |
| **GitHub repo in description** | Prominently noted, used as verification source |
| **Non-English video** | Warning — v1 is English-only |

<br />

## 🔧 Extraction Script

The `extract.py` script can also be used standalone:

```bash
python3 scripts/extract.py "https://youtube.com/watch?v=..." [-o output-dir] [--keep-audio]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-o` | `.yt-builder` | Base output directory |
| `--keep-audio` | off | Retain the downloaded mp3 |

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Missing dependency |
| 2 | Download failure |
| 3 | Transcription failure |
| 4 | Missing API key |

<br />

## 🗺️ Roadmap

- [ ] Non-English tutorial support
- [ ] Playlist / batch processing
- [ ] Tutorial detection (classify video type before processing)
- [ ] Visual information recovery via video frame extraction

<br />

## 📄 License

MIT

<br />

---

<p align="center">
  <sub>Built as a <a href="https://docs.anthropic.com/en/docs/claude-code">Claude Code</a> skill — paste a YouTube URL, get a build plan.</sub>
</p>
