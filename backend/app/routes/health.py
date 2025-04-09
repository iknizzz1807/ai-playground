from fastapi import APIRouter
from ..models.emoji_predictor import emoji_predictor

router = APIRouter()


@router.get("/")
async def root():
    models_available = {
        "digit_recognition": True,
        "emoji_prediction": emoji_predictor.emoji_model_loaded,
    }
    return {
        "message": "Handwriting Recognition API is running",
        "available_models": models_available,
    }
