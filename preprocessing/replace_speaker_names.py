import re
import os

# Configuration
TXT_FILE_PATH = r"data\data_commit_8\datacommit_8_goker_guner_speakers_cleaned.txt"
SPEAKER_2_NAME = "Göker Güner"
SPEAKER_1_NAME = "Enes Fehmi Manan"

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_FILE_PATH = os.path.join(PROJECT_ROOT, TXT_FILE_PATH)

with open(TXT_FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'\[Speaker 1\]', f'[{SPEAKER_1_NAME}]', content)
content = re.sub(r'\[Speaker 2\]', f'[{SPEAKER_2_NAME}]', content)

base, ext = os.path.splitext(TXT_FILE_PATH)
output_file = f"{base}_named{ext}"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done! Saved to: {output_file}")
