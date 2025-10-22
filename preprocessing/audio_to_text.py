import whisper
import os
import torch

def audio_to_text(audio_file_path, output_path="transcriptions", model_size="turbo"):
    os.makedirs(output_path, exist_ok=True)

    audio_file_path = os.path.abspath(audio_file_path)

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {DEVICE}")

    print(f"Loading Whisper {model_size} model on {DEVICE}...")
    model = whisper.load_model(model_size, device=DEVICE)

    print(f"Transcribing with timestamps: {audio_file_path}")

    result = model.transcribe(
        audio_file_path,
        language="tr",
        verbose=False,
        fp16=(DEVICE == "cuda"),
        word_timestamps=True
    )

    filename = os.path.splitext(os.path.basename(audio_file_path))[0]

    output_file_full = f"{output_path}/{filename}_full.txt"
    with open(output_file_full, "w", encoding="utf-8") as f:
        f.write(result["text"])

    output_file_timestamps = f"{output_path}/{filename}_timestamps.txt"
    with open(output_file_timestamps, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            f.write(f"[{start:.2f}s - {end:.2f}s] {text.strip()}\n")

    print(f"Full transcription saved to: {output_file_full}")
    print(f"Timestamped transcription saved to: {output_file_timestamps}")

    return result

if __name__ == "__main__":
    audio_file = "/content/datacommit_8_goker_guner.mp3"

    result = audio_to_text(audio_file, model_size="turbo")

    print(f"\nTranscription preview:")
    print(result["text"][:300])
