from fastapi import APIRouter
from pydantic import BaseModel
from ..models.digit_recognizer import digit_recognizer
from ..utils.image_processing import process_image

router = APIRouter()


class ImageData(BaseModel):
    image: str


@router.post("/predict")
async def predict(data: ImageData):
    try:
        # Process the image
        image_array = process_image(data.image)

        # Make prediction
        result = digit_recognizer.predict(image_array)
        return result
    except Exception as e:
        print(f"Error during prediction: {e}")
        return {"prediction": "Error", "confidence": 0, "error": str(e)}
