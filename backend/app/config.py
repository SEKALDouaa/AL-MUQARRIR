import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL'  )
