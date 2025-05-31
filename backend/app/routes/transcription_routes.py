from flask import Blueprint, request, jsonify
from ..services.transcription_service import create_transcription, get_transcription_by_id, get_all_transcriptions, delete_transcription, update_transcription, search_transcriptions
from ..schemas.transcription_schema import TranscriptionSchema

transcription_bp = Blueprint('transcription', __name__)

transcription_shema = TranscriptionSchema()
transcriptions_shema = TranscriptionSchema(many=True)

@transcription_bp.route('/transcriptions', methods=['POST'])
def create():
    data = request.get_json()
    transcription = create_transcription(data)
    return transcription_shema.jsonify(transcription), 201

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['GET'])
def get(transcription_id):
    transcription = get_transcription_by_id(transcription_id)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return transcription_shema.jsonify(transcription)

@transcription_bp.route('/transcriptions', methods=['GET'])
def get_all():
    transcriptions = get_all_transcriptions()
    if not transcriptions:
        return jsonify({"message": "No transcriptions found"}), 404
    return transcriptions_shema.jsonify(transcriptions)

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['DELETE'])
def delete(transcription_id):
    transcription = delete_transcription(transcription_id)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return transcription_shema.jsonify(transcription), 204

@transcription_bp.route('/transcriptions/<int:transcription_id>', methods=['PUT'])
def update(transcription_id):
    data = request.get_json()
    transcription = update_transcription(transcription_id, data)
    if transcription is None:
        return jsonify({"message": "Transcription not found"}), 404
    return transcription_shema.jsonify(transcription)

@transcription_bp.route('/transcriptions/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"message": "Query parameter is required"}), 400
    results = search_transcriptions(query)
    if not results:
        return jsonify({"message": "No transcriptions found"}), 404