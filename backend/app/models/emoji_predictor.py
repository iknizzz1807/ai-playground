from transformers import pipeline
from ..config import EMOTION_MODEL, FRAMEWORK


class EmojiPredictor:
    def __init__(self):
        self.emoji_classifier = None
        self.emoji_model_loaded = False
        self.emoji_map = {
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
        self.load_model()

    def load_model(self):
        try:
            self.emoji_classifier = pipeline(
                "text-classification",
                model=EMOTION_MODEL,
                framework=FRAMEWORK,
            )
            self.emoji_model_loaded = True
        except Exception as e:
            print(f"Không thể tải model emoji: {e}")
            self.emoji_model_loaded = False

    def predict(self, text):
        if not self.emoji_model_loaded:
            return {"error": "Model emoji chưa được tải. Vui lòng kiểm tra logs."}

        try:
            result = self.emoji_classifier(text)[0]
            emotion = result["label"]
            confidence = result["score"]

            return {
                "emotion": emotion,
                "emoji": self.emoji_map.get(emotion, "❓"),
                "confidence": round(confidence * 100, 2),
            }
        except Exception as e:
            print(f"Error predicting emoji: {e}")
            return {"error": str(e)}


# Create a singleton instance
emoji_predictor = EmojiPredictor()
