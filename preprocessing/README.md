# Preprocessing Scripts

Scripts for downloading YouTube audio and transcribing to text with OpenAI Whisper.

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed on system
- CUDA GPU (optional, for faster processing)

### Install Dependencies

```bash
pip install yt-dlp openai-whisper librosa scikit-learn
```

### Usage

```bash
# 1. Download audio from YouTube
python download_audio.py

# 2. Transcribe with speaker diarization
python audio_to_text_with_speakers.py

# 3. Clean transcript with Gemini
python clean_transcript_with_gemini.py

# 4. Replace speaker names
python replace_speaker_names.py
```

---

## Files

### `download_audio.py`
Downloads audio from YouTube videos and converts to MP3 format. Handles Turkish character sanitization in filenames.

### `audio_to_text.py`
Basic audio transcription using Whisper. Generates full text and timestamped output files. Supports GPU acceleration via CUDA.

**Outputs:**
- `{filename}_full.txt` - Full transcription
- `{filename}_timestamps.txt` - Transcription with timestamps

### `audio_to_text_with_speakers.py`
Advanced transcription with speaker diarization. Uses MFCC and spectral features with K-Means clustering to identify different speakers.

**Outputs:**
- `{filename}_full.txt` - Full transcription
- `{filename}_with_speakers.txt` - Timestamped with speaker labels
- `{filename}_speakers.txt` - Grouped by speaker

### `clean_transcript_with_gemini.py`
Uses Gemini AI to clean and correct transcription errors, fix grammar, and improve readability.

### `replace_speaker_names.py`
Replaces generic speaker labels with actual names:
- `[Speaker 1]` → `[Enes Fehmi Manan]`
- `[Speaker 2]` → `[Guest Name]`

## Notes

- All scripts optimized for Turkish language
- GPU acceleration automatic when CUDA available
- Speaker diarization works best with 2-3 speakers

