#!/usr/bin/env bash
set -euo pipefail

# yt-builder dependency installer
# Cross-platform: macOS, Linux, Windows (WSL/Git Bash)
# Idempotent — safe to run multiple times.

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALLED=()
SKIPPED=()
WARNINGS=()

log() { echo "[yt-builder init] $1"; }
ok()  { log "✓ $1"; }
warn() { WARNINGS+=("$1"); log "⚠ $1"; }

command_exists() { command -v "$1" &>/dev/null; }

PLATFORM="$(uname -s)"
ARCH="$(uname -m)"

# Detect WSL
IS_WSL=false
if [[ "$PLATFORM" == "Linux" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
fi

log "Platform: $PLATFORM ($ARCH)$(${IS_WSL} && echo ' [WSL]' || true)"
echo ""

# --- ffmpeg ---
if command_exists ffmpeg; then
    ok "ffmpeg already installed"
    SKIPPED+=("ffmpeg")
else
    if [[ "$PLATFORM" == "Darwin" ]]; then
        if command_exists brew; then
            log "Installing ffmpeg via Homebrew..."
            brew install ffmpeg
            INSTALLED+=("ffmpeg")
        else
            warn "Homebrew not found. Install ffmpeg manually: https://ffmpeg.org"
        fi
    elif [[ "$PLATFORM" == "Linux" ]] || $IS_WSL; then
        if command_exists apt-get; then
            log "Installing ffmpeg via apt..."
            sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
            INSTALLED+=("ffmpeg")
        elif command_exists dnf; then
            log "Installing ffmpeg via dnf..."
            sudo dnf install -y ffmpeg
            INSTALLED+=("ffmpeg")
        elif command_exists pacman; then
            log "Installing ffmpeg via pacman..."
            sudo pacman -S --noconfirm ffmpeg
            INSTALLED+=("ffmpeg")
        else
            warn "Could not detect package manager. Install ffmpeg manually: https://ffmpeg.org"
        fi
    else
        warn "Unsupported platform for auto-install. Install ffmpeg manually: https://ffmpeg.org"
    fi
fi

# --- yt-dlp ---
if command_exists yt-dlp; then
    ok "yt-dlp already installed"
    SKIPPED+=("yt-dlp")
else
    if [[ "$PLATFORM" == "Darwin" ]] && command_exists brew; then
        log "Installing yt-dlp via Homebrew..."
        brew install yt-dlp
        INSTALLED+=("yt-dlp")
    elif command_exists pip3; then
        log "Installing yt-dlp via pip..."
        pip3 install yt-dlp
        INSTALLED+=("yt-dlp")
    elif command_exists pip; then
        log "Installing yt-dlp via pip..."
        pip install yt-dlp
        INSTALLED+=("yt-dlp")
    else
        warn "Could not install yt-dlp. Install manually: pip install yt-dlp"
    fi
fi

# --- JavaScript runtime (needed by yt-dlp for YouTube) ---
if command_exists deno || command_exists node || command_exists bun; then
    RUNTIME=""
    command_exists deno && RUNTIME="deno"
    command_exists node && RUNTIME="${RUNTIME:-node}"
    command_exists bun && RUNTIME="${RUNTIME:-bun}"
    ok "JavaScript runtime available ($RUNTIME)"
    SKIPPED+=("js-runtime")
else
    if [[ "$PLATFORM" == "Darwin" ]] && command_exists brew; then
        log "Installing deno (required by yt-dlp for YouTube)..."
        brew install deno
        INSTALLED+=("deno")
    else
        warn "No JavaScript runtime found. yt-dlp needs deno/node/bun for YouTube."
        warn "Install one: https://deno.land or https://nodejs.org"
    fi
fi

# --- AssemblyAI SDK ---
if python3 -c "import assemblyai" 2>/dev/null; then
    ok "assemblyai SDK already installed"
    SKIPPED+=("assemblyai")
else
    log "Installing assemblyai SDK..."
    pip3 install assemblyai 2>/dev/null || pip install assemblyai
    INSTALLED+=("assemblyai")
fi

# --- python-dotenv ---
if python3 -c "import dotenv" 2>/dev/null; then
    ok "python-dotenv already installed"
    SKIPPED+=("python-dotenv")
else
    log "Installing python-dotenv..."
    pip3 install python-dotenv 2>/dev/null || pip install python-dotenv
    INSTALLED+=("python-dotenv")
fi

# --- API key check ---
echo ""
ENV_FILE="$SKILL_DIR/.env"
if [[ -f "$ENV_FILE" ]] && grep -q "ASSEMBLYAI_API_KEY=" "$ENV_FILE" && ! grep -q "your-api-key-here" "$ENV_FILE"; then
    ok "AssemblyAI API key configured"
else
    warn "ASSEMBLYAI_API_KEY not set — required for transcription"
    log ""
    log "To configure:"
    log "  1. Sign up at https://www.assemblyai.com/ (\$50 free credits)"
    log "  2. Copy your API key from the dashboard"
    log "  3. Create $SKILL_DIR/.env with:"
    log "     ASSEMBLYAI_API_KEY=your-key-here"
    log ""
    log "  Or copy the example: cp $SKILL_DIR/.env.example $SKILL_DIR/.env"
fi

# --- Summary ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Setup complete"
if [[ ${#INSTALLED[@]} -gt 0 ]]; then
    log "Installed: ${INSTALLED[*]}"
fi
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    log "Already present: ${SKIPPED[*]}"
fi
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    log "Warnings:"
    for w in "${WARNINGS[@]}"; do
        log "  ⚠ $w"
    done
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
