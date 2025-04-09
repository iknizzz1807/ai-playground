from fastapi import APIRouter
from pydantic import BaseModel
from ..models.emoji_predictor import emoji_predictor

router = APIRouter()


class TextData(BaseModel):
    text: str


@router.post("/predict-emoji")
async def get_emoji(data: TextData):
    result = emoji_predictor.predict(data.text)

    if "error" in result:
        return result

    return {
        "text": data.text,
        "emotion": result["emotion"],
        "emoji": result["emoji"],
        "confidence": result["confidence"],
    }
