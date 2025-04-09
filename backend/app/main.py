from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from io import BytesIO
from PIL import Image, ImageEnhance
import numpy as np
import tensorflow as tf
import os

# Thêm thư viện transformers
from transformers import pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo pipeline dự đoán emoji (thực hiện sớm để tải model khi khởi động server)
try:
    emoji_classifier = pipeline(
        "text-classification",
        model="joeddav/distilbert-base-uncased-go-emotions-student",
        framework="pt",  # Chỉ định sử dụng PyTorch
    )
    emoji_model_loaded = True
except Exception as e:
    print(f"Không thể tải model emoji: {e}")
    emoji_model_loaded = False

model_path = "./models"

if not os.path.exists(os.path.join(model_path, "saved_model.pb")):
    raise FileNotFoundError(
        f"Model không tìm thấy tại {model_path}. Vui lòng copy model SavedModel vào thư mục này."
    )

model = tf.saved_model.load(model_path)

if hasattr(model, "predict"):
    predict_fn = model.predict
elif hasattr(model, "__call__"):
    predict_fn = model
else:
    predict_fn = model.signatures["serving_default"]


class ImageData(BaseModel):
    image: str


class TextData(BaseModel):
    text: str


# Hàm dự đoán emoji từ text
def predict_emoji(text):
    result = emoji_classifier(text)[0]
    emotion = result["label"]
    confidence = result["score"]

    # Map cảm xúc thành emoji
    emoji_map = {
        "admiration": "👏",
        "amusement": "😂",
        "anger": "😡",
        "annoyance": "😒",
        "approval": "👍",
        "caring": "🤗",
        "confusion": "😕",
        "curiosity": "🤔",
        "desire": "😍",
        "disappointment": "😞",
        "disapproval": "👎",
        "disgust": "🤢",
        "embarrassment": "😳",
        "excitement": "🤩",
        "fear": "😨",
        "gratitude": "🙏",
        "grief": "😢",
        "joy": "😃",
        "love": "❤️",
        "nervousness": "😬",
        "optimism": "🙂",
        "pride": "😌",
        "realization": "💡",
        "relief": "😅",
        "remorse": "😔",
        "sadness": "😭",
        "surprise": "😲",
        "neutral": "😐",
    }

    return {
        "emotion": emotion,
        "emoji": emoji_map.get(emotion, "❓"),
        "confidence": round(confidence * 100, 2),
    }


def process_image(image_base64: str) -> np.ndarray:
    try:
        # Decode base64
        image_data = base64.b64decode(image_base64.split(",")[1])
        image = Image.open(BytesIO(image_data)).convert("L")  # Convert to grayscale

        # Enhance contrast for better digit recognition
        image = ImageEnhance.Contrast(image).enhance(3.0)

        # Resize to slightly larger than 28x28, then crop to 28x28
        image = image.resize((32, 32)).crop((2, 2, 30, 30)).resize((28, 28))

        # Convert to numpy array and normalize
        image_array = np.array(image)

        # Apply thresholding to make it more black and white
        threshold = 200  # Adjust as needed
        image_array = (
            np.where(image_array > threshold, 255, 0).astype("float32") / 255.0
        )

        # Find bounding box of the digit
        if np.sum(image_array < 0.5) > 20:  # Make sure there's something drawn
            rows = np.any(image_array < 0.5, axis=1)
            cols = np.any(image_array < 0.5, axis=0)
            y_min, y_max = np.where(rows)[0][[0, -1]]
            x_min, x_max = np.where(cols)[0][[0, -1]]

            # Expand the box slightly
            y_min = max(0, y_min - 2)
            y_max = min(27, y_max + 2)
            x_min = max(0, x_min - 2)
            x_max = min(27, x_max + 2)

            # Extract and resize the digit
            digit = image_array[y_min:y_max, x_min:x_max]

            # Calculate scaling to fit in a 20x20 box (MNIST standard)
            h, w = digit.shape
            scale = min(20.0 / h, 20.0 / w)
            new_h, new_w = int(h * scale), int(w * scale)

            # Resize while preserving aspect ratio
            digit_resized = (
                tf.image.resize(
                    digit.reshape(h, w, 1), (new_h, new_w), method="bilinear"
                )
                .numpy()
                .reshape(new_h, new_w)
            )

            # Create a 28x28 blank canvas and place the digit in the center
            result = np.ones((28, 28))
            y_offset = (28 - new_h) // 2
            x_offset = (28 - new_w) // 2
            result[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = (
                digit_resized
            )

            image_array = result

        # Invert colors: MNIST uses white digits on black background
        image_array = 1 - image_array

        return image_array.reshape(1, 28, 28, 1)
    except Exception as e:
        print(f"Error in process_image: {e}")
        # Return a fallback empty image if processing fails
        return np.zeros((1, 28, 28, 1)).astype("float32")


@app.post("/predict")
async def predict(data: ImageData):
    try:
        # Process the image
        image_array = process_image(data.image)

        # Check if image is valid
        if np.sum(image_array) == 0:
            return {"prediction": "?", "confidence": 0}

        # Make prediction based on model type
        try:
            # Try standard SavedModel interface
            input_tensor = tf.constant(image_array, dtype=tf.float32)
            predictions = predict_fn(input_tensor)

            # Extract prediction from result - handling different model output formats
            if isinstance(predictions, dict):
                # For SavedModel signatures
                output_key = list(predictions.keys())[0]
                prediction_tensor = predictions[output_key]
            else:
                # For regular model outputs
                prediction_tensor = predictions

            # Convert tensor to numpy array
            prediction_values = prediction_tensor.numpy()[0]
            predicted_class = np.argmax(prediction_values)
            confidence = float(prediction_values[predicted_class])

        except Exception as e:
            print(f"Prediction error: {e}")
            # Fallback approach for other model formats
            predictions = model(tf.constant(image_array))
            prediction_values = predictions.numpy()[0]
            predicted_class = np.argmax(prediction_values)
            confidence = float(prediction_values[predicted_class])

        # For MNIST, we only have digits 0-9
        result = str(predicted_class)

        return {"prediction": result, "confidence": round(confidence * 100, 2)}
    except Exception as e:
        print(f"Error during prediction: {e}")
        return {"prediction": "Error", "confidence": 0, "error": str(e)}


@app.post("/predict-emoji")
async def get_emoji(data: TextData):
    if not emoji_model_loaded:
        return {"error": "Model emoji chưa được tải. Vui lòng kiểm tra logs."}

    try:
        result = predict_emoji(data.text)
        return {
            "text": data.text,
            "emotion": result["emotion"],
            "emoji": result["emoji"],
            "confidence": result["confidence"],
        }
    except Exception as e:
        print(f"Error predicting emoji: {e}")
        return {"error": str(e)}


@app.get("/")
async def root():
    models_available = {
        "digit_recognition": True,
        "emoji_prediction": emoji_model_loaded,
    }
    return {
        "message": "Handwriting Recognition API is running",
        "available_models": models_available,
    }
