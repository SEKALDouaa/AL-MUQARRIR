from flask import Flask, request, jsonify
import os
import pickle
from audioPipeline import process_entire_audio , process_entire_audio_minimal ,  process_entire_audio_without_refinement , process_entire_audio_minimal_without_refinement
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

# CORS configuration
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle preflight OPTIONS requests
@app.route('/', methods=['OPTIONS'])
@app.route('/process_audio', methods=['OPTIONS'])
@app.route('/process_audio_chunk', methods=['OPTIONS'])
@app.route('/process_audio_no_refine', methods=['OPTIONS'])
@app.route('/process_audio_minimal_no_refine', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
def handle_options():
    return '', 200

# Create uploads directory relative to current working directory
UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
print(f"✅ Uploads directory created/verified at: {UPLOADS_DIR}")

# ── (A) Load or initialize speaker embedding database ─────────
DB_PATH = os.path.join(os.getcwd(), "speaker_db.pkl")
if os.path.exists(DB_PATH):
    with open(DB_PATH, "rb") as f:
        existing_db = pickle.load(f)
    print(f"✅ Loaded existing speaker database with {len(existing_db)} speakers")
else:
    existing_db = {}  # { speaker_id: [embedding_vecs...] }
    print("✅ Initialized new speaker database")

# ── (B) Root endpoint ─────────
@app.route("/", methods=["GET"])
def index():
    return "✅ L'API is active. Use POST <strong>/process_audio</strong> for Full‐file processing or <strong>/process_audio_chunk</strong> for Real‐time processing."

# ── (C) Full‐file processing endpoint ─────────────────────────
@app.route("/process_audio", methods=["POST"])
def process_audio():
    """
    Expects multipart/form‐data with a file field named 'file'.
    Returns JSON with:
      - speaker_mapping: { segment_id: speaker_id, … }
      - combined: [ {'SPEAKER_00': text}, … ]
      - refined:  [ {'SPEAKER_00': text}, … ]
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    # 1) Save uploaded file
    save_path = os.path.join(UPLOADS_DIR, file.filename)
    file.save(save_path)
    # 2) Run pipeline (this updates existing_db in memory)
    result = process_entire_audio(save_path, existing_db, temp_dir=UPLOADS_DIR)
    # 3) Persist updated DB
    with open(DB_PATH, "wb") as f:
        pickle.dump(existing_db, f)
    # 4) Build minimal JSON response
    payload = {
        "speaker_mapping": result["speaker_mapping"],
        "combined": result["combined"],
        "result": result["refined"]
    }
    return jsonify(payload), 200

# ── (D) Chunked / Real‐time processing endpoint ─────────────
@app.route('/process_audio_chunk', methods=['POST'])
def process_audio_chunk():
    """
    Expects JSON payload { "audio_data_base64": "<base64‐encoded WAV chunk>" }
    Returns { status: "success", refined_transcription_chunk: [ {speaker: text}, … ] }
    """
    global existing_db
    if not request.json or 'audio_data_base64' not in request.json:
        return jsonify({"error": "Missing audio_data_base64 in JSON payload"}), 400
    audio_data_base64 = request.json['audio_data_base64']
    try:
        import base64, tempfile
        # Decode base64 into a temporary file
        audio_bytes = base64.b64decode(audio_data_base64)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_input.write(audio_bytes)
        temp_input_path = temp_input.name
        temp_input.close()
        
        refined_chunk = process_entire_audio_minimal(temp_input_path, existing_db, temp_dir=UPLOADS_DIR)
        
        # Update DB persistently
        with open(DB_PATH, "wb") as f:
            pickle.dump(existing_db, f)
        # Clean up temp files
        os.remove(temp_input_path)
        return jsonify({
            "status": "success",
            "result": refined_chunk
        }), 200
    except Exception as e:
        import traceback
        print("Error processing audio chunk:")
        print(traceback.format_exc())
        # Ensure temp cleanup
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ── (E) Full‐file processing endpoint without refinement ─────────────
@app.route("/process_audio_no_refine", methods=["POST"])
def process_audio_no_refine():
    """
    Expects multipart/form‐data with a file field named 'file'.
    Returns JSON with:
      - speaker_mapping: { segment_id: speaker_id, … }
      - combined:      [ {'SPEAKER_00': text}, … ]
      - reid_combined: [ {'SPEAKER_XX': text}, … ]
    (Everything but Gemini refinement.)
    """
    global existing_db
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    # 1) Save uploaded file
    save_path = os.path.join(UPLOADS_DIR, file.filename)
    file.save(save_path)
    try:
        # 2) Call the "without_refinement" pipeline
        result = process_entire_audio_without_refinement(save_path, existing_db, temp_dir=UPLOADS_DIR)
        # 3) Persist the updated speaker‐DB
        with open(DB_PATH, "wb") as f:
            pickle.dump(existing_db, f)
        # 4) Build minimal response
        payload = {
            "speaker_mapping": result["speaker_mapping"],
            "combined": result["combined"],
            "result": result["reid_combined"]
        }
        return jsonify(payload), 200
    except Exception as e:
        import traceback
        print("Error in /process_audio_no_refine:", traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ── (F) Chunked / Real‐time processing endpoint without refinement ─────────────
@app.route("/process_audio_minimal_no_refine", methods=["POST"])
def process_audio_minimal_no_refine():
    """
    Expects JSON with audio_data_base64 field.
    Returns JSON with:
      - reid_combined: [ {'SPEAKER_XX': text}, … ]
    """
    global existing_db
    
    # Get JSON data
    data = request.get_json()
    if not data or "audio_data_base64" not in data:
        return jsonify({"error": "No audio_data_base64 in JSON"}), 400
    
    try:
        # Decode base64 audio
        import base64
        audio_data = base64.b64decode(data["audio_data_base64"])
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Process audio
        reid_combined = process_entire_audio_minimal_without_refinement(
            temp_path, existing_db, temp_dir=UPLOADS_DIR
        )
        print(f"✅ Processed chunk, result: {reid_combined}")
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Persist the updated speaker-DB
        with open(DB_PATH, "wb") as f:
            pickle.dump(existing_db, f)
        
        # Build response
        payload = {
            "result": reid_combined
        }
        return jsonify(payload), 200
        
    except Exception as e:
        import traceback
        print("Error in /process_audio_minimal_no_refine:", traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ── (G) Health check endpoint ────────────────────────────────
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200
