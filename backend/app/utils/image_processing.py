import base64
from io import BytesIO
from PIL import Image, ImageEnhance
import numpy as np
import tensorflow as tf
from ..config import THRESHOLD


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
        image_array = (
            np.where(image_array > THRESHOLD, 255, 0).astype("float32") / 255.0
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
