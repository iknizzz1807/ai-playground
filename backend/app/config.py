import os

# Model paths
MODEL_PATH = "./ai_models"
DIGIT_MODEL_FILE = "saved_model.pb"

# Emoji model config
EMOTION_MODEL = "joeddav/distilbert-base-uncased-go-emotions-student"
FRAMEWORK = "pt"  # Use PyTorch

# Speech-to-text model config
SPEECH_MODEL = "openai/whisper-small"
MAX_AUDIO_LENGTH = 30  # Maximum audio length in seconds
SUPPORTED_FORMATS = ["wav", "mp3", "ogg", "flac"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Image processing config
THRESHOLD = 200
