from ..extensions import ma
from ..models.user import User

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        include_relationships = True
        load_only = ("password",)  # Exclude password from serialization
        dump_only = ("id",)  # Exclude id from deserialization