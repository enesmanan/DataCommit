# Preprocessing Scripts

Scripts for downloading YouTube audio and transcribing to text with OpenAI Whisper.

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

## Dependencies

```bash
pip install yt-dlp
pip install openai-whisper
pip install torch torchvision torchaudio
pip install librosa scikit-learn numpy
```

**System requirement:** FFmpeg must be installed for audio processing.

## Notes

- All scripts optimized for Turkish language
- GPU acceleration automatic when CUDA available
- Speaker diarization works best with 2-3 speakers

