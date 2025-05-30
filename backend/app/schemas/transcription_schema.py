from ..extensions import ma
from ..models.transcripion import Transcription

class TranscriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Transcription
        load_instance = True