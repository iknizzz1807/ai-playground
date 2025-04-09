import os
import numpy as np
import tensorflow as tf
from ..config import MODEL_PATH, DIGIT_MODEL_FILE


class DigitRecognizer:
    def __init__(self):
        self.model = None
        self.predict_fn = None
        self.load_model()

    def load_model(self):
        if not os.path.exists(os.path.join(MODEL_PATH, DIGIT_MODEL_FILE)):
            raise FileNotFoundError(
                f"Model không tìm thấy tại {MODEL_PATH}. Vui lòng copy model SavedModel vào thư mục này."
            )

        self.model = tf.saved_model.load(MODEL_PATH)

        if hasattr(self.model, "predict"):
            self.predict_fn = self.model.predict
        elif hasattr(self.model, "__call__"):
            self.predict_fn = self.model
        else:
            self.predict_fn = self.model.signatures["serving_default"]

    def predict(self, image_array):
        try:
            # Check if image is valid
            if np.sum(image_array) == 0:
                return {"prediction": "?", "confidence": 0}

            # Try standard SavedModel interface
            input_tensor = tf.constant(image_array, dtype=tf.float32)
            predictions = self.predict_fn(input_tensor)

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

            return {
                "prediction": str(predicted_class),
                "confidence": round(confidence * 100, 2),
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            # Fallback approach for other model formats
            try:
                predictions = self.model(tf.constant(image_array))
                prediction_values = predictions.numpy()[0]
                predicted_class = np.argmax(prediction_values)
                confidence = float(prediction_values[predicted_class])

                return {
                    "prediction": str(predicted_class),
                    "confidence": round(confidence * 100, 2),
                }
            except Exception as e2:
                print(f"Fallback prediction error: {e2}")
                return {"prediction": "Error", "confidence": 0, "error": str(e2)}


# Create a singleton instance
digit_recognizer = DigitRecognizer()
