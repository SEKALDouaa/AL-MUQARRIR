from ..extensions import ma
from ..models.transcription import Transcription

class TranscriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Transcription
        load_instance = True