#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
MODELS_DIR="$PROJECT_DIR/.models"

WHISPER_MODEL="${WHISPER_MODEL:-ggml-large-v3-turbo.bin}"
WHISPER_MODEL_URL="${WHISPER_MODEL_URL:-https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$WHISPER_MODEL}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
QWEN_TTS_MODEL="${QWEN_TTS_MODEL:-mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16}"

log() {
  printf '\n==> %s\n' "$1"
}

fail() {
  printf '\nSetup failed: %s\n' "$1" >&2
  exit 1
}

require_apple_silicon() {
  local machine
  machine="$(uname -m)"
  if [[ "$machine" != "arm64" ]]; then
    fail "this project requires Apple Silicon. Detected architecture: $machine"
  fi
}

install_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return
  fi

  log "Installing Homebrew"
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi

  command -v brew >/dev/null 2>&1 || fail "Homebrew installed but is not on PATH. Add /opt/homebrew/bin to PATH and rerun setup."
}

install_brew_packages() {
  log "Installing Homebrew packages"
  brew update
  brew install ffmpeg python@3.11 whisper-cpp ollama
}

ensure_python() {
  log "Creating Python virtual environment"
  local python_bin
  python_bin="$(brew --prefix python@3.11)/bin/python3.11"
  [[ -x "$python_bin" ]] || fail "python@3.11 was not installed correctly"

  "$python_bin" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip wheel setuptools
  "$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
}

ensure_whisper_model() {
  log "Installing Whisper model"
  mkdir -p "$MODELS_DIR"
  if [[ ! -s "$MODELS_DIR/$WHISPER_MODEL" ]]; then
    curl -L --fail --progress-bar "$WHISPER_MODEL_URL" -o "$MODELS_DIR/$WHISPER_MODEL"
  fi
}

ensure_ollama() {
  log "Verifying Ollama"
  if ! command -v ollama >/dev/null 2>&1; then
    fail "Ollama is not on PATH after installation"
  fi

  if ! ollama list >/dev/null 2>&1; then
    printf 'Starting Ollama in the background for model setup...\n'
    nohup ollama serve >/tmp/dub-whatsapp-ollama.log 2>&1 &
    sleep 5
  fi

  ollama list >/dev/null 2>&1 || fail "Ollama is installed but the local server is not responding"
  ollama pull "$OLLAMA_MODEL"
}

warm_qwen_tts() {
  log "Verifying Qwen3-TTS model can load"
  "$VENV_DIR/bin/python" - <<PY
from mlx_audio.tts.utils import load_model
load_model("$QWEN_TTS_MODEL")
print("Loaded $QWEN_TTS_MODEL")
PY
}

verify_commands() {
  log "Final verification"
  command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg missing"
  command -v whisper-cli >/dev/null 2>&1 || fail "whisper-cli missing"
  command -v ollama >/dev/null 2>&1 || fail "ollama missing"
  [[ -x "$PROJECT_DIR/bin/dub-whatsapp" ]] || fail "bin/dub-whatsapp is not executable"
  [[ -s "$MODELS_DIR/$WHISPER_MODEL" ]] || fail "Whisper model missing"
  "$VENV_DIR/bin/python" - <<'PY'
import mlx
import mlx_audio
import numpy
import soundfile
print("Python dependencies OK")
PY
}

main() {
  require_apple_silicon
  install_homebrew
  install_brew_packages
  ensure_python
  ensure_whisper_model
  ensure_ollama
  warm_qwen_tts
  chmod +x "$PROJECT_DIR/bin/dub-whatsapp"
  verify_commands

  cat <<EOF

Setup complete.

Run:
  $PROJECT_DIR/bin/dub-whatsapp path/to/spanish-whatsapp-audio.ogg

Optional:
  export PATH="$PROJECT_DIR/bin:\$PATH"
EOF
}

main "$@"

