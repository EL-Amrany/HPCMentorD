import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_hpc_app')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hpc_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')  # <-- Insert your key or set as env variable
