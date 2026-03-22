#!/usr/bin/env python3
"""YouTube tutorial extraction pipeline.

Downloads audio, transcribes via AssemblyAI, and extracts structured metadata
from a YouTube video. All outputs are written to a working directory.

Progress/decisions go to stderr. The output directory path goes to stdout.

Cross-platform: works on macOS, Linux, and Windows.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs


# --- Utilities ---

def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def find_env_file() -> "Path | None":
    """Check skill dir .env, then cwd .env, then home .env."""
    candidates = [
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_env() -> None:
    """Load .env file into os.environ."""
    env_file = find_env_file()
    if not env_file:
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def check_dependencies() -> None:
    """Verify required tools are installed."""
    missing = []
    for cmd in ("yt-dlp", "ffmpeg"):
        if not shutil.which(cmd):
            missing.append(cmd)

    if missing:
        log(f"Error: Missing dependencies: {', '.join(missing)}")
        log("Run the init script first: bash <skill-dir>/scripts/init.sh")
        sys.exit(1)

    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        log("Error: ASSEMBLYAI_API_KEY not set")
        log("Set it in .env or run: export ASSEMBLYAI_API_KEY=your-key")
        log("Get a key at https://www.assemblyai.com/ ($50 free credits)")
        sys.exit(4)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    parsed = urlparse(url)

    # youtu.be/VIDEO_ID
    if parsed.hostname and "youtu.be" in parsed.hostname:
        return parsed.path.lstrip("/").split("/")[0]

    # youtube.com/watch?v=VIDEO_ID
    if parsed.hostname and "youtube" in parsed.hostname:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        # youtube.com/embed/VIDEO_ID or youtube.com/v/VIDEO_ID
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("embed", "v", "shorts"):
            return parts[1]

    # Fallback: treat as video ID directly
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    log(f"Warning: Could not extract video ID from URL, using hash")
    return str(abs(hash(url)))[:12]


# --- Metadata ---

def get_metadata(url: str) -> dict:
    """Fetch video metadata via yt-dlp without downloading."""
    log("Fetching video metadata...")
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-warnings", url],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            log(f"Error: yt-dlp metadata fetch failed:\n{result.stderr.strip()}")
            sys.exit(2)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        log("Error: Metadata fetch timed out after 60s")
        sys.exit(2)
    except json.JSONDecodeError:
        log("Error: Could not parse yt-dlp metadata output")
        sys.exit(2)


def extract_chapters(metadata: dict) -> list[dict]:
    """Extract chapters from metadata, if available."""
    chapters = metadata.get("chapters") or []
    return [
        {
            "title": ch.get("title", ""),
            "start_time": ch.get("start_time", 0),
            "end_time": ch.get("end_time", 0),
        }
        for ch in chapters
    ]


def extract_resources(description: str) -> dict:
    """Extract URLs, GitHub repos, and tool mentions from description."""
    resources = {
        "github_repos": [],
        "urls": [],
        "npm_packages": [],
        "pypi_packages": [],
    }

    if not description:
        return resources

    # GitHub repos
    gh_pattern = r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+'
    for match in re.findall(gh_pattern, description):
        clean = match.rstrip("/.,;:!?)")
        if clean not in resources["github_repos"]:
            resources["github_repos"].append(clean)

    # npm packages (from npmjs.com URLs)
    npm_pattern = r'https?://(?:www\.)?npmjs\.com/package/([a-zA-Z0-9@/_.-]+)'
    for match in re.findall(npm_pattern, description):
        pkg = match.rstrip("/.,;:!?)")
        if pkg not in resources["npm_packages"]:
            resources["npm_packages"].append(pkg)

    # PyPI packages (from pypi.org URLs)
    pypi_pattern = r'https?://pypi\.org/project/([a-zA-Z0-9_.-]+)'
    for match in re.findall(pypi_pattern, description):
        pkg = match.rstrip("/.,;:!?)")
        if pkg not in resources["pypi_packages"]:
            resources["pypi_packages"].append(pkg)

    # All URLs (deduplicated, excluding already-captured repos)
    url_pattern = r'https?://[^\s<>"\')\]]+(?<![.,;:!?\)])'
    for match in re.findall(url_pattern, description):
        if match not in resources["github_repos"] and match not in resources["urls"]:
            resources["urls"].append(match)

    return resources


def filter_metadata(metadata: dict) -> dict:
    """Filter metadata to useful fields only."""
    return {
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "channel": metadata.get("channel", ""),
        "channel_url": metadata.get("channel_url", ""),
        "upload_date": metadata.get("upload_date", ""),
        "duration": metadata.get("duration", 0),
        "view_count": metadata.get("view_count", 0),
        "tags": metadata.get("tags") or [],
        "categories": metadata.get("categories") or [],
        "thumbnail": metadata.get("thumbnail", ""),
        "webpage_url": metadata.get("webpage_url", ""),
    }


# --- Audio & Transcription ---

def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from YouTube URL via yt-dlp."""
    output_dir.mkdir(parents=True, exist_ok=True)

    log("\nDownloading audio...")
    result = subprocess.run(
        [
            "yt-dlp",
            "-x", "--audio-format", "mp3", "--audio-quality", "5",
            "-o", str(output_dir / "audio.%(ext)s"),
            "--print", "after_move:filepath",
            "--no-warnings",
            url,
        ],
        capture_output=True, text=True, timeout=600,
    )

    if result.returncode != 0:
        log(f"Error: Audio download failed:\n{result.stderr.strip()}")
        sys.exit(2)

    filepath = result.stdout.strip().splitlines()[-1]
    audio_path = Path(filepath)

    if not audio_path.exists():
        log(f"Error: Expected audio file not found at {audio_path}")
        sys.exit(2)

    log(f"Audio saved: {audio_path.name}")
    return audio_path


def transcribe(audio_path: Path) -> dict:
    """Transcribe audio using AssemblyAI Universal 3 Pro with speaker diarization.

    Returns dict with 'text' (plain text) and 'utterances' (timestamped segments).
    """
    try:
        import assemblyai as aai
    except ImportError:
        log("Error: assemblyai package not installed")
        log("Run: pip install assemblyai")
        sys.exit(1)

    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    aai.settings.api_key = api_key

    log("\nTranscribing with AssemblyAI (speaker diarization enabled)...")
    log("Uploading audio and processing...")

    config = aai.TranscriptionConfig(speaker_labels=True)
    transcript = aai.Transcriber().transcribe(str(audio_path), config=config)

    if transcript.status == aai.TranscriptStatus.error:
        log(f"Error: AssemblyAI transcription failed: {transcript.error}")
        sys.exit(3)

    utterances = []
    for u in (transcript.utterances or []):
        utterances.append({
            "speaker": u.speaker,
            "text": u.text,
            "start": u.start,
            "end": u.end,
            "confidence": u.confidence,
        })

    log(f"Transcription complete: {len(utterances)} utterances")
    return {
        "text": transcript.text or "",
        "utterances": utterances,
    }


# --- Main Pipeline ---

def main():
    parser = argparse.ArgumentParser(
        description="Extract transcript and metadata from a YouTube tutorial"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--output-dir", "-o", default=".yt-builder",
        help="Base output directory (default: .yt-builder)"
    )
    parser.add_argument(
        "--keep-audio", action="store_true",
        help="Keep the downloaded audio file after transcription"
    )
    args = parser.parse_args()

    load_env()
    check_dependencies()

    # Extract video ID and create working directory
    video_id = extract_video_id(args.url)
    work_dir = Path(args.output_dir) / video_id
    work_dir.mkdir(parents=True, exist_ok=True)
    research_dir = work_dir / "research"
    research_dir.mkdir(exist_ok=True)

    log(f"Working directory: {work_dir}")

    # Step 1: Fetch metadata
    raw_metadata = get_metadata(args.url)
    title = raw_metadata.get("title", "Unknown")
    duration = raw_metadata.get("duration", 0) or 0
    log(f'\nVideo: "{title}" ({duration // 60}m {duration % 60}s)')

    # Step 2: Extract structured data from metadata
    filtered = filter_metadata(raw_metadata)
    chapters = extract_chapters(raw_metadata)
    description = raw_metadata.get("description", "")
    resources = extract_resources(description)

    log(f"Chapters: {len(chapters)} found" if chapters else "No chapters found")
    log(f"Resources: {len(resources['github_repos'])} GitHub repos, {len(resources['urls'])} URLs")

    # Step 3: Write metadata outputs
    with open(work_dir / "metadata.json", "w") as f:
        json.dump(filtered, f, indent=2)

    with open(work_dir / "chapters.json", "w") as f:
        json.dump(chapters, f, indent=2)

    with open(work_dir / "description.txt", "w") as f:
        f.write(description)

    with open(work_dir / "resources.json", "w") as f:
        json.dump(resources, f, indent=2)

    # Step 4: Download audio
    audio_path = download_audio(args.url, work_dir)

    # Step 5: Transcribe
    result = transcribe(audio_path)

    # Step 6: Write transcript outputs
    with open(work_dir / "transcript.txt", "w") as f:
        if result["utterances"]:
            for u in result["utterances"]:
                f.write(f"Speaker {u['speaker']}: {u['text']}\n\n")
        else:
            f.write(result["text"])

    with open(work_dir / "transcript_timestamps.json", "w") as f:
        json.dump(result["utterances"], f, indent=2)

    # Step 7: Cleanup
    if not args.keep_audio and audio_path.exists():
        audio_path.unlink()
        log("Audio file cleaned up")

    # Summary
    log(f"\n{'='*50}")
    log(f"Extraction complete: {work_dir}")
    log(f"  metadata.json          - Video metadata")
    log(f"  chapters.json          - {len(chapters)} chapters")
    log(f"  description.txt        - Video description")
    log(f"  resources.json         - Extracted URLs/repos")
    log(f"  transcript.txt         - Plain text transcript")
    log(f"  transcript_timestamps.json - Timestamped utterances")
    log(f"  research/              - (ready for research agents)")
    log(f"{'='*50}")

    # Print working directory path to stdout (for Claude to capture)
    print(str(work_dir))


if __name__ == "__main__":
    main()
