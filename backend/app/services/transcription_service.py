from ..models.transcription import Transcription
from sqlalchemy import or_
from ..extensions import db

def create_transcription(data):
    transcription = Transcription(**data)
    db.session.add(transcription)
    db.session.commit()
    return transcription

def get_transcription_by_id(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None
    return transcription

def get_all_transcriptions():
    transcriptions = Transcription.query.all()
    if not transcriptions:
        return None
    return transcriptions

def delete_transcription(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None
    db.session.delete(transcription)
    db.session.commit()
    return transcription

def update_transcription(transcription_id, data):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None
    for key, value in data.items():
        setattr(transcription, key, value)
    db.session.commit()
    return transcription

def search_transcriptions(query):
    results = Transcription.query.filter(
        or_(
            Transcription.titreSceance.ilike(f"%{query}%"),
            Transcription.President.ilike(f"%{query}%"),
            Transcription.OrdreDuJour.ilike(f"%{query}%"),
            Transcription.Resume.ilike(f"%{query}%"),
            Transcription.PV.ilike(f"%{query}%")
        )
    ).all()
    return results