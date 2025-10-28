import os
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are an expert Turkish transcript editor specializing in conversation analysis and correction.

TASK: Clean and correct Turkish conversation transcripts by analyzing semantic flow, speaker patterns, and linguistic context.

CORRECTIONS REQUIRED:

1. SPEAKER LABEL ANALYSIS & CORRECTION:
   - DO NOT trust the original speaker labels - they may be completely wrong
   - Re-analyze the entire conversation from scratch to determine who is actually speaking
   - Identify speech patterns: Who is hosting/introducing? Who is responding? Who asks questions?
   - If a speaker is mid-sentence or mid-thought, merge with their previous speech
   - Look for natural turn-taking: questions → answers, statements → responses
   - A single speaker can speak for many consecutive sentences/paragraphs
   - Only switch speakers when there's genuine conversational turn (new person responding, answering, or interjecting)
   - The first speaker label in the original may be wrong - reconsider based on content

2. MERGE FRAGMENTED SPEECH:
   - Combine all consecutive lines belonging to the same speaker into one continuous block under a single [Speaker X]: label
   - Remove unnecessary line breaks within a speaker's turn
   - Keep all text flowing naturally as one speaker's contribution

3. TURKISH LANGUAGE CORRECTIONS:
   - Fix common transcription errors: "düğürlerinizi" → "duyurularınızı", "maltı" → "MultiGroup", "Datacomit" → "DataCommit", "diyelim" (check context)
   - Correct technical terms: "emelops" → "MLOps", "vef" → "web", "trd" → "TR'de"
   - Fix spacing and capitalization: proper nouns, sentence starts
   - Preserve colloquial speech ("ya", "yani", "işte") but fix obvious mistakes
   - Correct misheard words based on semantic context

4. PUNCTUATION:
   - Add proper Turkish punctuation (periods, commas, question marks, exclamation marks)
   - Use commas for natural pauses in speech
   - End complete thoughts with periods

OUTPUT FORMAT:
- [Speaker X]: followed by all their continuous speech in one paragraph
- Only switch to [Speaker Y]: when the conversation actually changes speakers
- NO explanations, comments, or meta-text
- Clean, readable Turkish conversation format

EXAMPLE 1 - Merging fragments:
WRONG (fragmented, incorrect labels):
[Speaker 2]: merhaba ben bugün sizlere
[Speaker 1]: bir şeyden bahsedeceğim çok önemli
[Speaker 2]: bu konu hakkında

CORRECT (merged, proper label):
[Speaker 1]: Merhaba, ben bugün sizlere bir şeyden bahsedeceğim. Çok önemli bu konu hakkında.

EXAMPLE 2 - Long host introduction:
WRONG (incorrectly split):
[Speaker 2]: Selamlar herkese bugün sizlere bir konudan bahsedeceğim
[Speaker 1]: bu konu çok önemli
[Speaker 2]: şimdi başlayalım

CORRECT (kept together as one speaker):
[Speaker 1]: Selamlar herkese, bugün sizlere bir konudan bahsedeceğim. Bu konu çok önemli. Şimdi başlayalım."""


def read_transcript(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_progress(output_path, content):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def chunk_transcript(content, chunk_size=40):
    lines = content.strip().split('\n')
    chunks = []
    current_chunk = []
    
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= chunk_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks


def clean_chunk_with_gemini(chunk, previous_context="", is_first_chunk=False):
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={
            'temperature': 0.3,
            'top_p': 0.95,
        }
    )
    
    first_chunk_instruction = ""
    if is_first_chunk:
        first_chunk_instruction = """
SPECIAL INSTRUCTION FOR FIRST CHUNK:
- This is the beginning of the conversation
- Identify who is the MAIN HOST (the person who welcomes everyone, introduces the show/topic)
- Assign the main host as [Speaker 1]:
- Assign other participant(s) as [Speaker 2]:
- IGNORE the original speaker labels completely - reassign based on who is actually speaking
"""
    
    prompt = f"""{SYSTEM_PROMPT}

Previous context (for continuity):
{previous_context}

Current transcript to clean:
{chunk}
{first_chunk_instruction}

IMPORTANT ANALYSIS STEPS:
1. Read the entire chunk first
2. Identify conversation roles: Who is the main host/introducer? Who are other participants?
3. This is a 2-person conversation - use ONLY [Speaker 1]: and [Speaker 2]: labels
4. Identify natural conversation boundaries:
   - Who is introducing/hosting? (usually continues for several sentences)
   - Who is responding to questions?
   - Where do questions end and answers begin?
   - Does a sentence continue from the previous speaker's thought?
5. Keep related sentences together under one speaker
6. Only switch speakers at genuine conversation turns

Output only the cleaned transcript with [Speaker 1]: and [Speaker 2]: labels."""
    
    response = model.generate_content(prompt)
    return response.text.strip()


def get_last_lines(text, num_lines=10):
    lines = text.strip().split('\n')
    return '\n'.join(lines[-num_lines:]) if lines else ""


def process_transcript(input_file, output_file):
    print(f"Reading transcript from: {input_file}")
    content = read_transcript(input_file)
    
    chunks = chunk_transcript(content, chunk_size=40)
    total_chunks = len(chunks)
    print(f"Split into {total_chunks} chunks for processing")
    
    cleaned_content = ""
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{total_chunks}...")
        
        previous_context = get_last_lines(cleaned_content, num_lines=10)
        is_first_chunk = (i == 0)
        
        try:
            cleaned_chunk = clean_chunk_with_gemini(chunk, previous_context, is_first_chunk)
            cleaned_content += cleaned_chunk + "\n\n"
            
            write_progress(output_file, cleaned_content)
            print(f"Saved progress after chunk {i+1}")
            
            if i < total_chunks - 1:
                time.sleep(4.5)
            
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            print("Progress saved. You can resume by running the script again.")
            raise
    
    print(f"\nCleaning complete! Output saved to: {output_file}")
    return cleaned_content

def main():
    input_file = Path("data\data_commit_7\datacommit_7_murat_sahin_speakers.txt")
    output_file = Path("data\data_commit_7\datacommit_7_murat_sahin_speakers_cleaned.txt")
    
    if not input_file.exists():
        print(f"Error: Input file not found at {input_file}")
        return
    
    process_transcript(input_file, output_file)


if __name__ == "__main__":
    main()

