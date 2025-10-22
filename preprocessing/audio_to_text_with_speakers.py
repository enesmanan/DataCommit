import whisper
import os
import torch
import librosa
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def extract_speaker_features(audio_path, start_time, end_time, sr=16000):
    y, _ = librosa.load(audio_path, sr=sr, offset=start_time, duration=end_time-start_time)

    if len(y) < 512:
        return None

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
    zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))

    features = np.concatenate([
        mfcc_mean,
        mfcc_std,
        [spectral_centroid, spectral_rolloff, zero_crossing_rate]
    ])

    return features

def audio_to_text_with_speakers(audio_file_path, output_path="transcriptions", model_size="turbo", n_speakers=2):
    os.makedirs(output_path, exist_ok=True)

    audio_file_path = os.path.abspath(audio_file_path)

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=" * 60)
    print(f"WHISPER MODEL: Using {DEVICE.upper()} device")
    if DEVICE == "cuda":
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"=" * 60)

    print(f"\nLoading Whisper '{model_size}' model on {DEVICE.upper()}...")
    model = whisper.load_model(model_size, device=DEVICE)

    print(f"Transcribing audio with GPU acceleration: {audio_file_path}\n")

    result = model.transcribe(
        audio_file_path,
        language="tr",
        verbose=False,
        fp16=(DEVICE == "cuda"),
        word_timestamps=True
    )

    print(f"\n{'='*60}")
    print(f"SPEAKER DIARIZATION: Using CPU (lightweight librosa)")
    print(f"{'='*60}\n")

    print(f"Extracting speaker features from {len(result['segments'])} segments...")
    features_list = []
    valid_segments = []

    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]

        features = extract_speaker_features(audio_file_path, start, end)
        if features is not None:
            features_list.append(features)
            valid_segments.append(segment)

    if len(features_list) < n_speakers:
        print(f"Warning: Not enough segments ({len(features_list)}) for {n_speakers} speakers. Using all segments as single speaker.")
        speakers = [0] * len(valid_segments)
    else:
        features_array = np.array(features_list)

        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_array)

        print(f"Clustering into {n_speakers} speakers using K-Means...")
        kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
        speakers = kmeans.fit_predict(features_scaled)
        print(f"✓ Successfully identified {len(set(speakers))} speakers\n")

    filename = os.path.splitext(os.path.basename(audio_file_path))[0]

    output_file_full = f"{output_path}/{filename}_full.txt"
    with open(output_file_full, "w", encoding="utf-8") as f:
        f.write(result["text"])

    output_file_speakers = f"{output_path}/{filename}_with_speakers.txt"
    with open(output_file_speakers, "w", encoding="utf-8") as f:
        for i, segment in enumerate(valid_segments):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            speaker = speakers[i]
            f.write(f"[Speaker {speaker+1}] [{start:.2f}s - {end:.2f}s] {text.strip()}\n")

    output_file_json = f"{output_path}/{filename}_speakers.txt"
    with open(output_file_json, "w", encoding="utf-8") as f:
        current_speaker = None
        current_text = []

        for i, segment in enumerate(valid_segments):
            speaker = speakers[i]
            text = segment["text"].strip()

            if speaker != current_speaker:
                if current_text:
                    f.write(f"\n[Speaker {current_speaker+1}]:\n")
                    f.write(" ".join(current_text) + "\n")
                current_speaker = speaker
                current_text = [text]
            else:
                current_text.append(text)

        if current_text:
            f.write(f"\n[Speaker {current_speaker+1}]:\n")
            f.write(" ".join(current_text) + "\n")

    print(f"Full transcription saved to: {output_file_full}")
    print(f"Transcription with speakers (detailed) saved to: {output_file_speakers}")
    print(f"Transcription with speakers (grouped) saved to: {output_file_json}")

    return result, speakers

if __name__ == "__main__":
    audio_file = "/content/datacommit_8_goker_guner.mp3"

    result, speakers = audio_to_text_with_speakers(audio_file, model_size="turbo", n_speakers=2)

    print(f"\nTranscription preview:")
    print(result["text"][:300])
    print(f"\nDetected {len(set(speakers))} different speakers")
