import torch
from pyannote.audio import Pipeline
import whisper
import google.generativeai as genai
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

def load_models():
    # Set the Hugging Face token
    HF_TOKEN = os.getenv("HF_TOKEN")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    """### Instantiate all the models"""

    # Diarisation-->instantiate the pipeline and loading the transformer
    pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",  #The model used
    use_auth_token=HF_TOKEN) #Hugging face token

    # Transcription--> loading the whisper turbo model
    whisper_model = whisper.load_model("turbo")

    # Gemini--> refinement model
    gemini_model_name = "gemini-2.5-flash-preview-04-17"
    # gemini_model_name = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_API_KEY) # Pass your variable here
    gemini_model = genai.GenerativeModel(gemini_model_name)

    # embedding
    speaker_embedding_model = PretrainedSpeakerEmbedding(
        "pyannote/embedding",  #The model used
        use_auth_token=HF_TOKEN,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    )
    return pipeline,whisper_model,gemini_model,speaker_embedding_model