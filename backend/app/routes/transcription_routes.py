from flask import Blueprint, request, jsonify
from ..services.transcription_service import create_transcription, get_transcription_by_id, get_all_transcriptions, delete_transcription, update_transcription, search_transcriptions
from ..schemas.transcription_schema import TranscriptionSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.transcription_service import update_transcription_with_deroulement, update_transcription_with_analysis

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
    return transcription_shema.jsonify(transcription), 204

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