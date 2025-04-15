import base64
import io
import os
import tempfile
from pydub import AudioSegment
import librosa
import numpy as np
from ..config import MAX_AUDIO_LENGTH, SUPPORTED_FORMATS, MAX_FILE_SIZE


def validate_audio_file(file_content, filename):
    """Validate audio file size and format"""
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, "File quá lớn. Vui lòng tải lên file nhỏ hơn 10MB."

    # Check file format
    file_format = filename.split(".")[-1].lower()
    if file_format not in SUPPORTED_FORMATS:
        return (
            False,
            f"Định dạng không được hỗ trợ. Các định dạng hỗ trợ: {', '.join(SUPPORTED_FORMATS)}",
        )

    return True, ""


def detect_format_from_content_type(content_type):
    """Detect audio format from content type string"""
    if "audio/wav" in content_type or "audio/wave" in content_type:
        return "wav"
    elif "audio/mp3" in content_type or "audio/mpeg" in content_type:
        return "mp3"
    elif "audio/ogg" in content_type:
        return "ogg"
    elif "audio/flac" in content_type:
        return "flac"
    elif "audio/webm" in content_type:
        return "webm"
    elif "audio/aac" in content_type:
        return "aac"
    else:
        return "wav"  # Default to WAV


def convert_to_wav(audio_data, format_type):
    """Convert audio to WAV format using temporary files for better reliability"""
    try:
        # Create a temporary file for the input audio
        with tempfile.NamedTemporaryFile(
            suffix=f".{format_type}", delete=False
        ) as temp_in:
            temp_in_path = temp_in.name
            temp_in.write(audio_data)
            temp_in.flush()

        # Create a temporary file for the output WAV
        temp_out_path = temp_in_path + ".wav"

        # Convert to WAV using pydub
        audio = AudioSegment.from_file(temp_in_path, format=format_type)
        audio.export(temp_out_path, format="wav")

        # Read the converted WAV file
        with open(temp_out_path, "rb") as wav_file:
            wav_data = wav_file.read()

        # Clean up temporary files
        os.unlink(temp_in_path)
        os.unlink(temp_out_path)

        return wav_data
    except Exception as e:
        print(f"Error converting audio: {e}")
        # Try to clean up if files exist
        try:
            if os.path.exists(temp_in_path):
                os.unlink(temp_in_path)
            if os.path.exists(temp_out_path):
                os.unlink(temp_out_path)
        except:
            pass
        return audio_data  # Return original if conversion fails


def process_base64_audio(audio_base64):
    """Process base64 encoded audio data with better format detection"""
    try:
        # Split to get the actual base64 part
        if "," in audio_base64:
            content_type, base64_data = audio_base64.split(",", 1)
        else:
            base64_data = audio_base64
            content_type = ""

        # Determine format from content type if possible
        format_type = detect_format_from_content_type(content_type.lower())

        # Decode base64
        audio_data = base64.b64decode(base64_data)

        # Convert to WAV if needed
        if format_type != "wav":
            audio_data = convert_to_wav(audio_data, format_type)
            format_type = "wav"

        return audio_data, format_type, None

    except Exception as e:
        return None, None, f"Error processing audio: {e}"


def clean_audio_data(audio_array, sample_rate=16000):
    """Clean up audio data by removing silence and normalizing"""
    try:
        # Normalize audio
        audio_array = librosa.util.normalize(audio_array)

        # Remove silence
        non_silent = librosa.effects.split(
            audio_array,
            top_db=30,  # Adjust this value to change silence detection sensitivity
            frame_length=1024,
            hop_length=256,
        )

        # If no non-silent segments are found, return the original audio
        if len(non_silent) == 0:
            return audio_array

        # Concatenate non-silent parts
        cleaned_audio = []
        for start, end in non_silent:
            cleaned_audio.extend(audio_array[start:end])

        cleaned_audio = np.array(cleaned_audio)

        # Ensure we have data
        if len(cleaned_audio) == 0:
            return audio_array

        return cleaned_audio
    except Exception as e:
        print(f"Error cleaning audio: {e}")
        return audio_array  # Return the original if processing fails
