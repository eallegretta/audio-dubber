# dub-whatsapp

Local Apple Silicon CLI for dubbing WhatsApp voice notes into another language while preserving the original speaker's voice.

The tool runs fully on your machine after setup. It transcribes speech, translates the transcript, synthesizes speech in the target language with a cloned reference voice, and writes a WhatsApp-friendly audio file.

Defaults are Spanish input and English output.

## What it does

Pipeline:

1. `ffmpeg` normalizes the input audio to mono 16 kHz WAV.
2. `whisper.cpp` transcribes the source speech locally.
3. `Ollama` translates the transcript into natural spoken target-language text locally.
4. `MLX-Audio` runs Qwen3-TTS locally and uses the original audio as a voice reference.
5. `ffmpeg` encodes the generated speech as `.ogg`, `.opus`, `.mp3`, or `.m4a`.

Default output is `.ogg` with Opus audio, which is the best format for sending back through WhatsApp.

## Requirements

Hardware and OS:

- macOS on Apple Silicon (`arm64`)
- Enough disk space for local speech and language models
- Enough memory for MLX-Audio/Qwen3-TTS model loading

Software installed by `setup.sh`:

- Homebrew, if missing
- `ffmpeg`
- `python@3.11`
- `whisper-cpp`
- `ollama`
- Python virtual environment packages from `requirements.txt`
- Whisper model: `ggml-large-v3-turbo.bin`
- Ollama translation model: `llama3.2:3b`
- MLX-Audio Qwen3-TTS model:
  `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`

Network:

- Required during setup for Homebrew packages and model downloads
- Not required for normal use once all models are downloaded

## Install

Clone the repository:

```bash
git clone <your-repo-url>
cd dub-whatsapp
```

Make scripts executable and run setup:

```bash
chmod +x setup.sh bin/dub-whatsapp
./setup.sh
```

Setup can take a while because it downloads models.

## Usage

Run from the project folder:

```bash
bin/dub-whatsapp ~/Downloads/spanish-voice-note.ogg
```

This writes:

```bash
./spanish-voice-note.en.ogg
```

Choose an explicit output path:

```bash
bin/dub-whatsapp ~/Downloads/spanish-voice-note.ogg ~/Desktop/english-dub.ogg
```

Supported output formats:

```bash
bin/dub-whatsapp input.ogg output.ogg
bin/dub-whatsapp input.ogg output.opus
bin/dub-whatsapp input.ogg output.mp3
bin/dub-whatsapp input.ogg output.m4a
```

If the output path has no extension, `.ogg` is added:

```bash
bin/dub-whatsapp input.ogg ~/Desktop/english-dub
```

Choose input and output languages:

```bash
bin/dub-whatsapp \
  --input-language Portuguese \
  --input-language-code pt \
  --output-language English \
  ~/Downloads/portuguese-note.ogg \
  ~/Desktop/english-dub.ogg

bin/dub-whatsapp \
  --input-language Spanish \
  --input-language-code es \
  --output-language French \
  ~/Downloads/spanish-note.ogg \
  ~/Desktop/french-dub.ogg
```

`--input-language` is the human-readable language name used in the translation prompt.
`--input-language-code` is the language code passed to `whisper.cpp`.
`--output-language` is the language name used for translation and Qwen3-TTS generation.

Show help:

```bash
bin/dub-whatsapp --help
```

## Optional PATH setup

To run `dub-whatsapp` from anywhere:

```bash
export PATH="/path/to/dub-whatsapp/bin:$PATH"
```

Then:

```bash
dub-whatsapp ~/Downloads/spanish-voice-note.ogg ~/Desktop/english-dub.ogg
```

Add the `export PATH=...` line to your shell config if you want it to persist.

## Configuration

Use environment variables to override defaults.

### Languages

Default:

```bash
bin/dub-whatsapp input.ogg output.ogg
```

Equivalent to:

```bash
bin/dub-whatsapp \
  --input-language Spanish \
  --input-language-code es \
  --output-language English \
  input.ogg \
  output.ogg
```

Use `--input-language-code` values supported by your installed `whisper.cpp` model, such as `es`, `en`, `pt`, `fr`, `de`, or `it`.

Use target language names that your Qwen3-TTS model supports. English is the most tested target in this project.

### Translation model

Default:

```bash
OLLAMA_MODEL=llama3.2:3b
```

Example:

```bash
OLLAMA_MODEL=llama3.1:8b bin/dub-whatsapp input.ogg output.ogg
```

The selected Ollama model must be available locally. Pull it first if needed:

```bash
ollama pull llama3.1:8b
```

### TTS model

Default:

```bash
QWEN_TTS_MODEL=mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16
```

Use the larger model:

```bash
QWEN_TTS_MODEL=mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16 bin/dub-whatsapp input.ogg output.ogg
```

The larger model can improve quality but needs more memory and disk space.

### Whisper model

Default path:

```bash
.models/ggml-large-v3-turbo.bin
```

Override:

```bash
WHISPER_MODEL_PATH=/path/to/ggml-model.bin bin/dub-whatsapp input.ogg output.ogg
```

### Whisper binary

Default:

```bash
WHISPER_BIN=whisper-cli
```

Override if your `whisper.cpp` binary has a different name or path:

```bash
WHISPER_BIN=/path/to/whisper-cli bin/dub-whatsapp input.ogg output.ogg
```

## Debugging

Keep intermediate files:

```bash
KEEP_WORK=1 bin/dub-whatsapp input.ogg output.ogg
```

The command prints the temporary work folder. It contains:

- `input-16k.wav` - normalized source audio
- `transcript.txt` - Spanish transcript from Whisper
- `english.txt` - target-language translation from Ollama
- `english.wav` - generated TTS audio before final encoding

## Troubleshooting

### `Python environment missing. Run ./setup.sh first.`

Run:

```bash
./setup.sh
```

### `ffmpeg missing`

Install with Homebrew:

```bash
brew install ffmpeg
```

Or rerun:

```bash
./setup.sh
```

### `whisper-cli missing`

Install `whisper-cpp`:

```bash
brew install whisper-cpp
```

If your binary is not named `whisper-cli`, set `WHISPER_BIN`.

### `ollama missing`

Install Ollama:

```bash
brew install ollama
```

Or rerun:

```bash
./setup.sh
```

### `Ollama server is not responding`

Start Ollama:

```bash
ollama serve
```

In another terminal, rerun `dub-whatsapp`.

### `Whisper model missing`

Rerun setup:

```bash
./setup.sh
```

Or set `WHISPER_MODEL_PATH` to an existing model file.

### TTS is slow

Qwen3-TTS runs locally. Long messages and larger models take more time. Try the default `0.6B` model before the `1.7B` model.

### Voice quality is poor

Voice cloning quality depends on the source audio. Best results come from:

- Clear single-speaker audio
- Minimal background noise
- Several seconds of uninterrupted speech
- No music under the voice

## Project layout

```text
.
├── bin/
│   └── dub-whatsapp              # Main CLI pipeline
├── src/
│   └── dub_whatsapp/
│       ├── translate.py          # Ollama translation helper
│       └── tts_qwen3.py          # MLX-Audio Qwen3-TTS helper
├── requirements.txt              # Python dependencies
├── setup.sh                      # macOS/Apple Silicon setup script
└── README.md
```

## Limitations

- Defaults to Spanish input and English output, but accepts custom input and output languages.
- Designed for Apple Silicon Macs.
- Requires local model downloads during setup.
- Output timing is not forced to match the original WhatsApp note duration.
- Translation quality depends on the selected Ollama model.
- Voice cloning quality depends on the reference audio and TTS model.

## Privacy

After setup, the normal dubbing pipeline runs locally:

- Audio transcription uses local `whisper.cpp`.
- Translation uses local Ollama.
- Voice synthesis uses local MLX-Audio.
- Final encoding uses local `ffmpeg`.

Setup downloads tools and models from external package/model hosts.

## Responsible use

Use this only with audio and voices you have permission to process. Do not use it to impersonate people, mislead listeners, or create deceptive audio.

## License

Add a license before publishing if you want others to use, modify, or redistribute this project.
