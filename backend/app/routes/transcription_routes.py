from flask import Blueprint, request, jsonify
from ..services.transcription_service import create_transcription, get_transcription_by_id, get_all_transcriptions, delete_transcription, update_transcription, search_transcriptions,get_ngrok_url
from ..schemas.transcription_schema import TranscriptionSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.transcription_service import update_transcription_with_deroulement, update_transcription_with_analysis, export_transcription_pv_arabe_docx, export_transcription_pv_arabe_pdf, export_transcription_analysis_arabe_docx, export_transcription_analysis_arabe_pdf
from ..services.ai_services import process_refinement_with_gemini, model
from ..services.transcription_service import update_transcription_segments

transcription_bp = Blueprint('transcription_bp', __name__)

transcription_shema = TranscriptionSchema()
transcriptions_shema = TranscriptionSchema(many=True)

@transcription_bp.route('/transcriptions', methods=['POST'])
@jwt_required()
def create():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "User not authenticated"}), 401
    data = request.get_json()
    data['user_email'] = get_jwt_identity()
    transcription = create_transcription(data)
    return transcription_shema.jsonify(transcription), 201

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['GET'])
@jwt_required()
def get(transcription_id):
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "User not authenticated"}), 401
    transcription = get_transcription_by_id(transcription_id)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return transcription_shema.jsonify(transcription)

@transcription_bp.route('/transcriptions', methods=['GET'])
@jwt_required()
def get_all():
    print("Headers:", request.headers)
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "User not authenticated"}), 401
    transcriptions = get_all_transcriptions(user_email=current_user)
    if not transcriptions:
        return jsonify({"message": "No transcriptions found"}), 404
    return transcriptions_shema.jsonify(transcriptions)

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['DELETE'])
@jwt_required()
def delete(transcription_id):
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "User not authenticated"}), 401
    transcription = delete_transcription(transcription_id)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return '', 204

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['PUT'])
@jwt_required()
def update(transcription_id):
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "User not authenticated"}), 401
    data = request.get_json()
    transcription = update_transcription(transcription_id, data)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return transcription_shema.jsonify(transcription)

@transcription_bp.route('/transcriptions/search', methods=['GET'])
@jwt_required()
def search():
    current_user = get_jwt_identity()
    query = request.args.get('query')
    if not query:
        return jsonify({"message": "Query parameter is required"}), 400
    results = search_transcriptions(query, user_email=current_user)
    if not results:
        return jsonify({"message": "No transcriptions found"}), 404
    return transcriptions_shema.jsonify(results), 200

@transcription_bp.route('/transcriptions/<int:transcription_id>/deroulement', methods=['POST'])
@jwt_required()
def generate_deroulement_ai(transcription_id):
    try:
        transcription = update_transcription_with_deroulement(transcription_id)
        return transcription_shema.jsonify(transcription), 200
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 404
    except Exception as e:
        return jsonify({"message": "AI generation failed", "error": str(e)}), 500

@transcription_bp.route('/transcriptions/<int:transcription_id>/analyse', methods=['POST'])
@jwt_required()
def generate_analyse_ai(transcription_id):
    try:
        transcription = update_transcription_with_analysis(transcription_id)
        return transcription_shema.jsonify(transcription), 200
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 404
    except Exception as e:
        return jsonify({"message": "AI generation failed", "error": str(e)}), 500
    
@transcription_bp.route('/debug-transcriptions', methods=['GET'])
def debug_headers():
    print("DEBUG Headers:", request.headers)
    return jsonify({"message": "Headers received"}), 200

# ----------- Export Routes -----------

@transcription_bp.route('/transcriptions/<int:transcription_id>/export/pv/docx', methods=['GET'])
@jwt_required()
def export_pv_docx(transcription_id):
    return export_transcription_pv_arabe_docx(transcription_id)

@transcription_bp.route('/transcriptions/<int:transcription_id>/export/pv/pdf', methods=['GET'])
@jwt_required()
def export_pv_pdf(transcription_id):
    return export_transcription_pv_arabe_pdf(transcription_id)

@transcription_bp.route('/transcriptions/<int:transcription_id>/export/analysis/docx', methods=['GET'])
@jwt_required()
def export_analysis_docx(transcription_id):
    return export_transcription_analysis_arabe_docx(transcription_id)

@transcription_bp.route('/transcriptions/<int:transcription_id>/export/analysis/pdf', methods=['GET'])
@jwt_required()
def export_analysis_pdf(transcription_id):
    return export_transcription_analysis_arabe_pdf(transcription_id)

@transcription_bp.route('/transcriptions/ngrok_url', methods=['GET'])
@jwt_required()
def ngrok_url():
    # Try to get from environment variable or config
    ngrok_url = get_ngrok_url()
    return jsonify({'ngrok_url': ngrok_url})

@transcription_bp.route('/transcriptions/<int:transcription_id>/refine', methods=['POST'])
@jwt_required()
def refine_transcription_segments(transcription_id):
    current_user = get_jwt_identity()
    data = request.get_json()
    segments = data.get('segments')
    if not segments:
        return jsonify({'message': 'No segments provided'}), 400
    # segments is expected to be a list of dicts: [{speaker: text}, ...]
    refined_segments = process_refinement_with_gemini(segments, model)
    # Convert [{SPEAKER_XX: text}, ...] to [{"speaker": "SPEAKER_XX", "text": text}, ...]
    converted_segments = []
    for seg in refined_segments:
        for speaker, text in seg.items():
            converted_segments.append({"speaker": speaker, "text": text})
    # Update the transcription in the DB (assume update_transcription_segments exists)
    transcription = update_transcription_segments(transcription_id, converted_segments)
    if not transcription:
        return jsonify({'message': 'Transcription not found'}), 404
    return transcription_shema.jsonify(transcription), 200

@transcription_bp.route('/transcriptions/<int:transcription_id>/export/pdfshift', methods=['GET'])
@jwt_required()
def export_pv_pdfshift(transcription_id):
    from ..services.transcription_service import export_transcription_pv_pdfshift
    return export_transcription_pv_pdfshift(transcription_id)
