from fastapi import APIRouter
from ..models.emoji_predictor import emoji_predictor
from ..models.speech_recognizer import speech_recognizer

router = APIRouter()


@router.get("/")
async def root():
    models_available = {
        "digit_recognition": True,
        "emoji_prediction": emoji_predictor.emoji_model_loaded,
        "speech_to_text": speech_recognizer.model_loaded,
    }
    return {
        "message": "AI Playground API is running",
        "available_models": models_available,
    }
