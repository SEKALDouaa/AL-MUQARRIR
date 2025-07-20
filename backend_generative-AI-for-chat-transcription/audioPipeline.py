import torch,torchaudio
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import os
import subprocess
import tempfile
import numpy as np

from Ai_models import load_models
pipeline,whisper_model,gemini_model,speaker_embedding_model = load_models()

"""## ── AUDIO PREPROCESSING ─────────────────────────────────"""

def preprocess_audio_and_save(input_audio_path: str,
                              output_dir: str = "/content/", # Or use tempfile.gettempdir() for truly temp files
                              output_filename: str = "final_processed_for_models.wav",
                              target_sample_rate: int = 16000) -> str:
    """
    Preprocesses an audio file and saves the final version.
    1. Converts to WAV format if not already (using ffmpeg for non-WAV inputs).
    2. Loads the audio using torchaudio.
    3. Converts to mono.
    4. Resamples to the target_sample_rate.
    5. Saves the fully processed audio to a specified path.
    6. Returns the path to the saved processed file.
    7. Cleans up any intermediate temporary WAV file created during initial conversion.

    Args:
        input_audio_path (str): Path to the input audio file.
        output_dir (str): Directory to save the final processed WAV file.
        output_filename (str): Filename for the final processed WAV file.
        target_sample_rate (int, optional): The desired sample rate. Defaults to 16000.

    Returns:
        str: Path to the saved final processed WAV file.
    """

    final_processed_path = os.path.join(output_dir, output_filename)

    # Internal helper for initial conversion to WAV if needed
    def _convert_to_wav_if_needed(input_file_path: str) -> tuple[str, bool]:
        working_audio_path = input_file_path
        intermediate_temp_created = False
        file_name, file_extension = os.path.splitext(input_file_path)
        file_extension = file_extension.lower()

        if file_extension == '.wav':
            return working_audio_path, intermediate_temp_created

        supported_non_wav_extensions = ['.mp3', '.ogg', '.flac', '.aac', '.m4a', '.wma']
        if file_extension not in supported_non_wav_extensions:
            raise ValueError(f"Unsupported audio file format: {file_extension} for '{input_file_path}'")

        intermediate_temp_wav_path = os.path.join(tempfile.gettempdir(), f"{os.path.basename(file_name)}_intermediate_{os.urandom(4).hex()}.wav")

        # print(f"Input '{input_file_path}' is not WAV. Converting to intermediate WAV: '{intermediate_temp_wav_path}'...")
        command = ['ffmpeg', '-i', input_file_path, '-y', intermediate_temp_wav_path]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            working_audio_path = intermediate_temp_wav_path
            intermediate_temp_created = True
        except subprocess.CalledProcessError as e:
            print(f"Error during FFmpeg conversion for '{input_file_path}': {e.stderr.decode()}")
            raise
        return working_audio_path, intermediate_temp_created

    intermediate_wav_path, was_intermediate_temp_created = _convert_to_wav_if_needed(input_audio_path)

    try:
        waveform, current_sample_rate = torchaudio.load(intermediate_wav_path)

        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if current_sample_rate != target_sample_rate:
            resampler = torchaudio.transforms.Resample(orig_freq=current_sample_rate, new_freq=target_sample_rate)
            waveform = resampler(waveform)
        # final_sample_rate is target_sample_rate

        os.makedirs(output_dir, exist_ok=True)
        torchaudio.save(final_processed_path, waveform.cpu(), target_sample_rate)
        # print(f"Final processed audio saved to: {final_processed_path}")

    finally: # Ensure cleanup of intermediate file
        if was_intermediate_temp_created and os.path.exists(intermediate_wav_path):
            try:
                os.remove(intermediate_wav_path)
                # print(f"Successfully removed intermediate temp WAV: {intermediate_wav_path}")
            except OSError as e:
                print(f"Error removing intermediate temp WAV '{intermediate_wav_path}': {e}")

    return final_processed_path

"""## ── DIARIZATION ──────────────────────────────────────────"""

def diarization_func(audio_file,pipeline):
  pipeline.to(torch.device("cuda")) # This line moves the pipeline  to the GPU for computation.
  # run the diarization pipeline on the loaded audio data.
  diarization = pipeline(audio_file)
  return diarization

"""## ── TRANSCRIPTION ───────────────────────────────────────"""


def transcribe_audio(audio_file,whisper_model):
  transcription = whisper_model.transcribe(audio_file)
  return transcription

"""## ── COMBINE DIARIZATION + TRANSCRIPTION ─────────────────"""

#for more clarification
# This function takes the output of pyannote's diarization process and converts it into a more structured, easy-to-use format.

def parse_pyannote_diarization(diarization):
    # Initialize an empty list to store the parsed segments.
    parsed_segments = []

    # Iterate through the diarization results using `itertracks` with `yield_label=True`.
    # This method yields tuples containing:
    # - `turn`: A segment object with `start` and `end` attributes representing the time interval.
    # - `_`: (Unused) Additional metadata (if any).
    # - `speaker`: The label assigned to the speaker for this segment.
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        # Append a dictionary to the `parsed_segments` list, containing:
        # - `start`: The start time of the segment (in seconds).
        # - `end`: The end time of the segment (in seconds).
        # - `speaker`: The speaker label for this segment.
        parsed_segments.append({
            'start': turn.start,
            'end': turn.end,
            'speaker': speaker
        })

    # Return the list of parsed segments in a structured format.
    return parsed_segments

# Function to calculate the overlap score between a transcription segment and a speaker diarization segment.
def segment_score(transcript_segment, speaker_segment, threshold=0.5):

    # Extract the start and end times of the transcription segment.
    t_start, t_end = transcript_segment["start"], transcript_segment["end"]

    # Extract the start and end times of the speaker diarization segment.
    s_start, s_end = speaker_segment['start'], speaker_segment['end']

    # Calculate overlap duration and ratio
    overlap = max(0, min(t_end, s_end) - max(t_start, s_start))
    overlap_ratio = overlap / (t_end - t_start) if (t_end - t_start) > 0 else 0

    return overlap_ratio if overlap_ratio >= threshold else 0.0  #apply threshold

def combine_diarization_transcription(diarization, transcription):
  # Initialize an empty list to store results
  speaker_texts = []

  parsed_diarization = parse_pyannote_diarization(diarization)

  # Track the previous speaker to avoid redundancy
  prev_speaker = None
  buffered_text = ""

  # Iterate through each segment in the transcription output.
  for t_segment in transcription["segments"]:
      max_score = 0  # Initialize the maximum overlap score to 0.
      best_s_segment = None  # Initialize the best matching speaker segment to None.

      # Compare the current transcription segment with all speaker diarization segments.
      for s_segment in parsed_diarization:
          # Calculate the overlap score between the transcription segment and the speaker segment.
          score = segment_score(t_segment, s_segment)

          # If the current score is higher than the previous maximum, update the maximum score and store the best segment.
          if score > max_score:
              max_score = score
              best_s_segment = s_segment

      current_speaker = best_s_segment['speaker'] if best_s_segment else None

      # Merge consecutive segments from the same speaker
      if current_speaker == prev_speaker:
          buffered_text += " " + t_segment["text"]
      else:
          if prev_speaker is not None:  # Flush the buffer for the previous speaker
              speaker_texts.append({prev_speaker : buffered_text.strip()})
          buffered_text = t_segment["text"]
          prev_speaker = current_speaker

      # Handle segments with no speaker match
      if best_s_segment is None:
          speaker_texts.append({f"No speaker found for: ": t_segment['text']})

  # Print any remaining buffered text
  if buffered_text:
      speaker_texts.append({prev_speaker : buffered_text.strip()})

  return speaker_texts

"""## ── Transcription Enhancement ─────────────────────────────────"""

#Define the Refinement Function using Gemini API
def refine_text_with_gemini_api(text_segment, speaker_label, model):
    if not model or not text_segment or not text_segment.strip():
        return text_segment

    # Constructing a detailed prompt for Gemini.
    # Few-shot examples are very effective with Gemini too.
    # You MUST create good, representative examples in Arabic/Darija/French/English mixes.

    prompt = f"""You are an expert AI assistant specializing in refining raw speech transcriptions from Moroccan conversations.
These conversations frequently mix Moroccan Darija, Modern Standard Arabic, French, and English.
Your primary directive is to enhance the clarity, readability, and grammatical correctness of the transcription WHILE STRICTLY PRESERVING THE ORIGINAL LANGUAGE(S) USED by the speaker.

**CRITICAL INSTRUCTIONS:**
1.  **NO TRANSLATION:** Absolutely do NOT translate any part of the text into English or any other language if it wasn't originally in that language. If the input is in Arabic/Darija, the output MUST be in Arabic/Darija. If it's a mix (e.g., Darija with French words), the output MUST preserve that exact mix.
2.  **LANGUAGE PRESERVATION:** Maintain the original linguistic blend. Do not replace Darija words with MSA or vice-versa unless it's a clear ASR error of a common word.
3.  **CORRECT ASR ERRORS:** Fix obvious errors from the Automatic Speech Recognition within the original language.
4.  **PUNCTUATION & CAPITALIZATION:** Improve punctuation and capitalization for better readability, following conventions appropriate for the language(s) being used (e.g., Arabic punctuation for Arabic text, French conventions for French text).
5.  **NATURAL FLOW:** Ensure the language sounds natural as if a human wrote it down from the speech.
6.  **NO ADDITIONS/OPINIONS:** Do not add any information or opinions not present in the original text.
7.  **MINIMAL CHANGES IF GOOD:** If a segment is already high quality, return it as is or with only very minor, essential touch-ups.
8.  **OUTPUT ONLY THE REFINED TEXT:** Do not include any of your own commentary, apologies, or explanations in the response. Just the refined segment.

**EXAMPLES OF DESIRED BEHAVIOR (Illustrative - provide your own high-quality examples):**

*   **Example 1 (Darija):**
    *   Speaker: SPEAKER_A
    *   Raw Transcription Segment: "السلام عليكم لباس اش خبارك كلشي مزيان"
    *   Refined Transcription Segment: "السلام عليكم، لباس؟ اش خبارك؟ كلشي مزيان."

*   **Example 2 (Darija/French Mix):**
    *   Speaker: SPEAKER_B
    *   Raw Transcription Segment: "bonjour khouya cv ana ghaya daba on va commencer le travail"
    *   Refined Transcription Segment: "Bonjour khouya, ça va? أنا غاية دابا. On va commencer le travail."

*   **Example 3 (MSA - Modern Standard Arabic):**
    *   Speaker: SPEAKER_C
    *   Raw Transcription Segment: "نود ان نناقش هذا الموضوع الهام في جلستنا اليوم"
    *   Refined Transcription Segment: "نود أن نناقش هذا الموضوع الهام في جلستنا اليوم."

*   **Example 4 (Input is already good):**
    *   Speaker: SPEAKER_D
    *   Raw Transcription Segment: "C'est une très bonne idée, merci."
    *   Refined Transcription Segment: "C'est une très bonne idée, merci."


**TASK:**
Now, apply these instructions to the following segment:

Speaker: {speaker_label}
Raw Transcription Segment: "{text_segment}"

Refined Transcription Segment:
"""

    try:
        # Safety settings can be adjusted if needed, but defaults are usually fine.
        # generation_config = genai.types.GenerationConfig(temperature=0.3) # Lower temp for more factual
        response = model.generate_content(
            prompt,
            # generation_config=generation_config
            safety_settings=[ # Adjust if you face blocking issues, but be mindful of safety
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        # Accessing the text:
        # For gemini-pro and older models: response.text
        # For gemini-1.5-flash/pro (multi-candidate, though usually one for non-streaming): response.candidates[0].content.parts[0].text
        # The .text attribute on the response object itself is usually a shortcut.
        if hasattr(response, 'text'):
            refined_text = response.text
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            refined_text = "".join(part.text for part in response.candidates[0].content.parts)
        else:
            print("    Warning: Could not extract text from Gemini response in the expected way.")
            print(f"    Response object: {response}")
            return text_segment # Fallback

        return refined_text.strip()
    except Exception as e:
        print(f"    Error during Gemini API call for '{text_segment[:50]}...': {e}")
        # Check if the error response from Gemini API has more details
        if hasattr(e, 'response') and e.response:
            print(f"    Gemini API Response Error: {e.response}")
        elif hasattr(e, 'message') and e.message: # For some genai errors
             print(f"    GenAI Exception message: {e.message}")
        return text_segment # Fallback


def process_refinement_with_gemini(speaker_texts: list[dict],
                                   gemini_model_instance: genai.GenerativeModel) -> list[dict]:
    """
    Processes a list of speaker text segments using the Gemini API for refinement.

    Args:
        speaker_texts: A list of dictionaries, where each dictionary has one
                       speaker label as key and the raw text segment as value.
                       Example: [{'SPEAKER_00': 'Raw text 1'}, {'SPEAKER_01': 'Raw text 2'}]
        gemini_model_instance: An initialized instance of google.generativeai.GenerativeModel.

    Returns:
        A list of dictionaries in the same format as input, but with refined text segments.
        Returns an empty list if gemini_model_instance is None or speaker_texts is empty.
    """
    if not gemini_model_instance:
        # print("Error: Gemini model instance is not provided or not initialized.")
        return speaker_texts # Return original if no model
    if not speaker_texts:
        return []

    refined_dialogue = []
    total_segments = len(speaker_texts)
    for i, entry in enumerate(speaker_texts):
        if not entry: # Skip if entry is empty
            continue

        # Assuming each dict in speaker_texts has exactly one key-value pair
        speaker_label, original_text = list(entry.items())[0]

        # Call the internal helper to refine the single segment
        refined_text = refine_text_with_gemini_api(original_text,
                                                     speaker_label,
                                                     gemini_model_instance)

        refined_dialogue.append({speaker_label: refined_text})

        # Optional: if you need progress indication outside the function,
        # you could use a callback or yield results. For now, it processes silently.
        # print(f"Processed segment {i+1}/{total_segments}") # For debugging if needed

    return refined_dialogue

"""## ── SPEAKER EMBEDDING (FOR RE‐ID) ────────────────────────"""

def extract_speaker_embeddings(diarization, audio_path: str, min_duration_sec: float = 0.5) -> dict:
    """
    Extracts speaker embeddings for segments longer than min_duration_sec.
    Skips too-short segments that would break the model.
    Returns a dictionary mapping 'segment_id' -> embedding_vector (1D numpy array).
    """
    raw_waveform, sr = torchaudio.load(audio_path)
    if raw_waveform.shape[0] > 1:
        raw_waveform = raw_waveform.mean(dim=0, keepdim=True)

    embeddings = {}
    for turn, _, speaker_label in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        if duration < min_duration_sec:
            continue  # Skip very short segments

        start_sample = int(turn.start * sr)
        end_sample   = int(turn.end * sr)
        chunk = raw_waveform[:, start_sample:end_sample]

        if chunk.numel() == 0:
            continue

        try:
            emb_np = speaker_embedding_model(chunk.to(speaker_embedding_model.device))
            # If the output is a torch.Tensor, squeeze and convert to numpy
            if isinstance(emb_np, torch.Tensor):
                emb_np = emb_np.squeeze(0).cpu().numpy()
            # If already a numpy array, squeeze out extra dimensions
            elif isinstance(emb_np, np.ndarray):
                if emb_np.ndim > 1:
                    emb_np = np.squeeze(emb_np)
            segment_id = f"{speaker_label}_{turn.start:.3f}_{turn.end:.3f}"
            embeddings[segment_id] = emb_np
        except Exception as e:
            print(f"Skipping segment due to error: {e}")

    return embeddings

"""### ── RE‐IDENTIFICATION IMPLEMENTATION ─────────────────────────────"""

def reidentify_speakers(embeddings: dict, existing_db: dict, threshold: float = 0.7) -> dict:
    """
    Assign each new segment embedding to an existing speaker if similarity ≥ threshold,
    otherwise create a new SPEAKER_{NN}. Updates existing_db in place.
    Returns { segment_id: assigned_speaker_id }.
    """
    assignment = {}
    # Build centroids
    centroids = {}
    for spk_id, vecs in existing_db.items():
        if vecs:
            centroids[spk_id] = np.mean(np.stack(vecs, axis=0), axis=0)

    # Determine next new speaker index
    used = [
        int(spk.split("_")[1])
        for spk in existing_db
        if spk.startswith("SPEAKER_") and spk.split("_")[1].isdigit()
    ]
    next_idx = max(used, default=-1) + 1

    for seg_id, emb in embeddings.items():
        emb = np.squeeze(emb)
        best_spk, best_score = None, -1.0

        # Compare against each centroid
        for spk_id, centroid in centroids.items():
            sim = cosine_similarity(centroid.reshape(1, -1), emb.reshape(1, -1))[0,0]
            if sim > best_score:
                best_spk, best_score = spk_id, sim

        if best_score >= threshold:
            # Existing speaker
            assignment[seg_id] = best_spk
            existing_db[best_spk].append(emb)
            # update centroid
            centroids[best_spk] = np.mean(np.stack(existing_db[best_spk], axis=0), axis=0)
        else:
            # New speaker
            new_spk = f"SPEAKER_{next_idx:02d}"
            next_idx += 1
            existing_db[new_spk] = [emb]
            centroids[new_spk] = emb
            assignment[seg_id] = new_spk

        # Debug log
        print(f"[ReID] segment {seg_id}: best={best_spk} score={best_score:.2f} assigned={assignment[seg_id]}")

    return assignment


def apply_speaker_reid_mapping(combined: list[dict], speaker_map: dict) -> list[dict]:
    """
    Replace diarization speaker labels in `combined` with reidentified speaker IDs.
    Safely handles entries with None speaker labels.
    """
    reid_combined = []
    for entry in combined:
        if not entry:
            continue

        original_speaker, text = list(entry.items())[0]

        # Fallback for unknown speaker labels
        if original_speaker is None or not isinstance(original_speaker, str):
            reid_combined.append({"UNKNOWN": text})
            continue

        # Find segment IDs that start with the diarized speaker label
        matching_ids = [
            k for k in speaker_map
            if isinstance(k, str) and k.startswith(original_speaker)
        ]

        if matching_ids:
            reidentified = [speaker_map[k] for k in matching_ids]
            assigned_speaker = max(set(reidentified), key=reidentified.count)
        else:
            assigned_speaker = original_speaker  # fallback

        reid_combined.append({assigned_speaker: text})

    return reid_combined

"""## ── Arab translation ─────────────────────────────────"""

def translate_text_to_arabic_with_gemini_api(text_segment: str, speaker_label: str, model: genai.GenerativeModel) -> str:
    """
    Translates a text segment into high-quality Modern Standard Arabic using the Gemini API.

    This function is designed to handle inputs that may be in Moroccan Darija,
    French, English, or a mix, and convert them into formal, grammatically
    correct Arabic suitable for official records or summaries.

    Args:
        text_segment (str): The piece of text to be translated.
        speaker_label (str): The label of the speaker (e.g., 'SPEAKER_01'), used for context in the prompt.
        model (genai.GenerativeModel): An initialized instance of the Gemini generative model.

    Returns:
        str: The translated Arabic text. Returns the original text if an error occurs.
    """
    if not model or not text_segment or not text_segment.strip():
        return text_segment

    # A detailed, few-shot prompt for high-quality translation to Modern Standard Arabic (MSA).
    prompt = f"""You are an expert AI translator specializing in converting conversational transcripts into formal, high-quality Modern Standard Arabic (الفصحى).
The source text is from a conversation and can be in Moroccan Darija, French, English, or a mix of these languages.

**CRITICAL INSTRUCTIONS:**
1.  **TRANSLATE TO MODERN STANDARD ARABIC (MSA):** Your primary goal is to translate the meaning of the text into grammatically correct, clear, and formal MSA.
2.  **PRESERVE MEANING:** Ensure the core meaning, intent, and nuances of the original text are accurately represented in the Arabic translation.
3.  **FORMAL TONE:** The output should be formal and suitable for a professional summary or record. Avoid colloquialisms in the final Arabic output unless absolutely necessary to preserve a specific cultural meaning that has no formal equivalent.
4.  **DO NOT ADD NEW INFO:** Do not add any information, opinions, or commentary that was not present in the original segment.
5.  **OUTPUT ONLY THE TRANSLATION:** Your entire response must be ONLY the final Arabic text. Do not include any apologies, explanations, or introductory phrases like "Here is the translation:".

**EXAMPLES OF DESIRED BEHAVIOR:**

*   **Example 1 (Darija/French Mix):**
    *   Source Text: "Bonjour khouya, ça va? أنا غاية دابا. On va commencer le travail."
    *   Translated Arabic: "مرحباً يا أخي، كيف حالك؟ أنا بخير الآن. سوف نبدأ العمل."

*   **Example 2 (Darija):**
    *   Source Text: "السلام عليكم، لباس؟ اش خبارك؟ كلشي مزيان."
    *   Translated Arabic: "السلام عليكم، هل أنت بخير؟ كيف أخبارك؟ كل شيء على ما يرام."

*   **Example 3 (English):**
    *   Source Text: "That's an excellent point. We should consider it for the next phase."
    *   Translated Arabic: "تلك نقطة ممتازة. يجب أن نأخذها في الاعتبار للمرحلة التالية."

*   **Example 4 (French):**
    *   Source Text: "C'est une très bonne idée, merci."
    *   Translated Arabic: "إنها فكرة جيدة جداً، شكراً لك."


**TASK:**
Now, apply these instructions to translate the following segment into Modern Standard Arabic.

Speaker: {speaker_label}
Source Text: "{text_segment}"

Translated Arabic:
"""

    try:
        # Safety settings can be adjusted if needed
        response = model.generate_content(
            prompt,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        # Unified way to access response text for different Gemini versions
        if hasattr(response, 'text'):
            translated_text = response.text
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            translated_text = "".join(part.text for part in response.candidates[0].content.parts)
        else:
            print("    Warning: Could not extract text from Gemini translation response.")
            return text_segment # Fallback to original text

        return translated_text.strip()
    except Exception as e:
        print(f"    Error during Gemini API translation call for '{text_segment[:50]}...': {e}")
        return text_segment # Fallback to original text

"""### ── TOP‐LEVEL PIPELINES ───────────────────────────────────"""

def process_entire_audio(input_audio_path: str, existing_db: dict, temp_dir: str = "/content/") -> dict:
    # Step 1: Preprocess and diarize
    processed_wav = preprocess_audio_and_save(input_audio_path, output_dir=temp_dir)
    diar = diarization_func(processed_wav, pipeline)

    # Step 2: Transcribe and combine
    transcription = transcribe_audio(processed_wav, whisper_model)
    combined = combine_diarization_transcription(diar, transcription)

    # Step 3: Refinement with Gemini
    refined = process_refinement_with_gemini(combined, gemini_model)

    # Step 4: Extract embeddings and reidentify speakers
    embeddings = extract_speaker_embeddings(diar, processed_wav)
    speaker_map = reidentify_speakers(embeddings, existing_db, threshold=0.7)

    # Step 5: Apply reidentification to refined text
    reid_combined = apply_speaker_reid_mapping(refined, speaker_map)

    # 8) Return
    return {
        "processed_wav": processed_wav,
        "diarization": diar,
        "embeddings": embeddings,
        "speaker_mapping": speaker_map,
        "transcription_raw": transcription,
        "combined": combined,
        "refined": refined
    }

def process_entire_audio_minimal(input_audio_path: str, existing_db: dict, temp_dir: str = "/content/") -> list[dict]:
    # Step 1: Preprocess and diarize
    processed_wav = preprocess_audio_and_save(input_audio_path, output_dir=temp_dir)
    diar = diarization_func(processed_wav, pipeline)

    # Step 2: Transcribe and combine
    transcription = transcribe_audio(processed_wav, whisper_model)
    combined = combine_diarization_transcription(diar, transcription)

    # Step 3: Refinement with Gemini
    refined = process_refinement_with_gemini(combined, gemini_model)

    # Step 4: Extract embeddings and reidentify speakers
    embeddings = extract_speaker_embeddings(diar, processed_wav)
    speaker_map = reidentify_speakers(embeddings, existing_db, threshold=0.7)

    # Step 5: Apply reidentification to refined text
    reid_combined = apply_speaker_reid_mapping(refined, speaker_map)


    return reid_combined

def process_entire_audio_without_refinement(input_audio_path: str, existing_db: dict, temp_dir: str = "/content/") -> dict:
    # Step 1: Preprocess and diarize
    processed_wav = preprocess_audio_and_save(input_audio_path, output_dir=temp_dir)
    diar = diarization_func(processed_wav, pipeline)

    # Step 2: Transcribe and combine
    transcription = transcribe_audio(processed_wav, whisper_model)
    combined = combine_diarization_transcription(diar, transcription)

    # Step 3: Extract embeddings and reidentify speakers
    embeddings = extract_speaker_embeddings(diar, processed_wav)
    speaker_map = reidentify_speakers(embeddings, existing_db, threshold=0.7)

    # Step 4: Apply reidentification to refined text
    reid_combined = apply_speaker_reid_mapping(combined, speaker_map)

    # 8) Return
    return {
        "processed_wav": processed_wav,
        "diarization": diar,
        "embeddings": embeddings,
        "speaker_mapping": speaker_map,
        "transcription_raw": transcription,
        "combined": combined,
        "reid_combined": reid_combined
    }

def process_entire_audio_minimal_without_refinement(input_audio_path: str, existing_db: dict, temp_dir: str = "/content/") -> list[dict]:
    # Step 1: Preprocess and diarize
    processed_wav = preprocess_audio_and_save(input_audio_path, output_dir=temp_dir)
    diar = diarization_func(processed_wav, pipeline)

    # Step 2: Transcribe and combine
    transcription = transcribe_audio(processed_wav, whisper_model)
    combined = combine_diarization_transcription(diar, transcription)

    # Step 3: Extract embeddings and reidentify speakers
    embeddings = extract_speaker_embeddings(diar, processed_wav)
    speaker_map = reidentify_speakers(embeddings, existing_db, threshold=0.7)

    # Step 4: Apply reidentification to refined text
    reid_combined = apply_speaker_reid_mapping(combined, speaker_map)


    return reid_combined


def process_entire_audio_translate_to_arabe(input_audio_path: str, existing_db: dict, temp_dir: str = "/content/") -> list[dict]:
    """
    Processes an entire audio file by transcribing, refining, re-identifying speakers,
    and finally, translating the entire dialogue into Modern Standard Arabic.

    This pipeline performs the following steps:
    1. Preprocesses the audio file.
    2. Performs speaker diarization.
    3. Transcribes the audio to text.
    4. Combines diarization and transcription.
    5. Refines the transcribed text for clarity and grammar using Gemini.
    6. Extracts speaker embeddings for re-identification.
    7. Re-identifies speakers against an existing database.
    8. Maps the re-identified speakers to the refined dialogue.
    9. Translates the final, refined dialogue into Arabic using Gemini.

    Args:
        input_audio_path (str): The path to the input audio file.
        existing_db (dict): A dictionary database of known speaker embeddings.
        temp_dir (str, optional): Directory for temporary processed files. Defaults to "/content/".

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains a
                    re-identified speaker and their corresponding dialogue translated into Arabic.
    """
    # Steps 1-4: Preprocessing, Diarization, Transcription, and Combination
    processed_wav = preprocess_audio_and_save(input_audio_path, output_dir=temp_dir)
    diar = diarization_func(processed_wav, pipeline)
    transcription = transcribe_audio(processed_wav, whisper_model)
    combined = combine_diarization_transcription(diar, transcription)

    # Step 5: Refinement with Gemini
    refined_dialogue = process_refinement_with_gemini(combined, gemini_model)

    # Steps 6-8: Speaker Re-identification
    embeddings = extract_speaker_embeddings(diar, processed_wav)
    speaker_map = reidentify_speakers(embeddings, existing_db, threshold=0.7)
    reid_refined_dialogue = apply_speaker_reid_mapping(refined_dialogue, speaker_map)

    # --- Step 9: New Translation Layer ---
    translated_dialogue = []
    if not gemini_model:
        # If gemini model is not available, return the refined but untranslated text
        print("Warning: Gemini model not available. Skipping translation.")
        return reid_refined_dialogue

    total_segments = len(reid_refined_dialogue)
    # print(f"Starting translation of {total_segments} refined segments to Arabic...")

    for i, entry in enumerate(reid_refined_dialogue):
        if not entry:
            continue

        speaker_label, refined_text = list(entry.items())[0]

        # Call the new translation function for each segment
        translated_text = translate_text_to_arabic_with_gemini_api(
            refined_text,
            speaker_label,
            gemini_model
        )

        translated_dialogue.append({speaker_label: translated_text})
        # print(f"Translated segment {i+1}/{total_segments}") # For debugging

    return translated_dialogue