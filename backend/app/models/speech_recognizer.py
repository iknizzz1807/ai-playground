import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import base64
import io
import os
import tempfile
import librosa
import numpy as np
from pydub import AudioSegment
from ..config import SPEECH_MODEL, MAX_AUDIO_LENGTH, SUPPORTED_FORMATS


class SpeechRecognizer:
    def __init__(self):
        self.speech_model = None
        self.processor = None
        self.pipe = None
        self.model_loaded = False
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.load_model()

    def load_model(self):
        try:
            # Check if we can import accelerate
            try:
                import accelerate

                has_accelerate = True
            except ImportError:
                has_accelerate = False
                print("Accelerate not found. Loading model in compatibility mode.")

            # Load the model with different settings based on environment
            if has_accelerate:
                # Use accelerate for efficient loading
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    SPEECH_MODEL,
                    torch_dtype=self.torch_dtype,
                    low_cpu_mem_usage=True,
                )
            else:
                # Fallback to standard loading without accelerate-specific params
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    SPEECH_MODEL,
                    torch_dtype=self.torch_dtype,
                )

            model.to(self.device)

            self.processor = AutoProcessor.from_pretrained(SPEECH_MODEL)

            # Create inference pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=8,  # Reduced batch size for lower memory usage
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
            self.model_loaded = True
            print("Speech-to-text model loaded successfully!")
        except Exception as e:
            print(f"Không thể tải model speech-to-text: {e}")
            self.model_loaded = False

            # Try to load a smaller model as fallback
            try:
                print("Attempting to load smaller model as fallback...")
                # Use Whisper tiny instead
                smaller_model = "openai/whisper-tiny"
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    smaller_model,
                    torch_dtype=self.torch_dtype,
                )
                model.to(self.device)

                self.processor = AutoProcessor.from_pretrained(smaller_model)

                self.pipe = pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=self.processor.tokenizer,
                    feature_extractor=self.processor.feature_extractor,
                    return_timestamps=False,  # Disable timestamps for smaller model
                    torch_dtype=self.torch_dtype,
                    device=self.device,
                )
                self.model_loaded = True
                print("Fallback to whisper-tiny model succeeded!")
            except Exception as e2:
                print(f"Fallback model loading also failed: {e2}")

    def process_audio_data(self, audio_data, format_type):
        """Process audio data from base64 or file using pydub for better format support"""
        try:
            # Create a temporary file to handle the audio properly
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{format_type}"
            ) as temp_file:
                temp_path = temp_file.name

                # Handle base64 data
                if isinstance(audio_data, str) and "base64" in audio_data:
                    # Extract the base64 content
                    if "," in audio_data:
                        content_type, base64_data = audio_data.split(",", 1)
                    else:
                        base64_data = audio_data

                    # Try to detect format from content type
                    if "audio/wav" in content_type:
                        format_type = "wav"
                    elif "audio/mp3" in content_type or "audio/mpeg" in content_type:
                        format_type = "mp3"
                    elif "audio/ogg" in content_type:
                        format_type = "ogg"
                    elif "audio/webm" in content_type:
                        format_type = "webm"

                    # Write decoded data to temp file
                    audio_bytes = base64.b64decode(base64_data)
                    temp_file.write(audio_bytes)
                    temp_file.flush()

                # Handle direct file upload
                else:
                    temp_file.write(audio_data)
                    temp_file.flush()

            try:
                # Use pydub to load the audio and convert to WAV for librosa
                audio_segment = AudioSegment.from_file(temp_path, format=format_type)

                # Convert to WAV in memory
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)

                # Load with librosa (now from a WAV file which is well-supported)
                audio_array, sample_rate = librosa.load(wav_io, sr=16000, mono=True)

                # Ensure audio is not too long
                if len(audio_array) > MAX_AUDIO_LENGTH * sample_rate:
                    audio_array = audio_array[: int(MAX_AUDIO_LENGTH * sample_rate)]

                # Clean up the temporary file
                os.unlink(temp_path)

                return audio_array

            except Exception as e:
                print(f"Error with pydub/librosa: {e}")
                # Direct approach with transformers' processor
                audio_array = self.processor.feature_extractor(
                    raw_speech=temp_path, sampling_rate=16000, return_tensors="pt"
                )
                os.unlink(temp_path)
                return audio_array

        except Exception as e:
            print(f"Error processing audio: {e}")
            return None

    def transcribe(self, audio_data, format_type="wav"):
        """Transcribe speech from audio data"""
        if not self.model_loaded:
            return {
                "error": "Model speech-to-text chưa được tải. Vui lòng cài đặt thư viện 'accelerate>=0.26.0' hoặc kiểm tra logs."
            }

        try:
            # Process the audio data
            processed_audio = self.process_audio_data(audio_data, format_type)
            if processed_audio is None:
                return {"error": "Không thể xử lý file audio. Vui lòng thử lại."}

            # Transcribe the audio
            result = self.pipe(processed_audio)

            # Extract full transcription
            transcription = result["text"]

            # Get timing info if available
            timestamps = []
            if "chunks" in result:
                timestamps = result["chunks"]

            timing_info = []

            for chunk in timestamps:
                if isinstance(chunk, dict) and "timestamp" in chunk:
                    timing_info.append(
                        {
                            "text": chunk.get("text", ""),
                            "start": chunk.get("timestamp", [0, 0])[0],
                            "end": chunk.get("timestamp", [0, 0])[1],
                        }
                    )

            return {
                "transcription": transcription.strip(),
                "timestamps": timing_info if timing_info else None,
                "success": True,
            }

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return {"error": str(e), "success": False}


# Create a singleton instance
speech_recognizer = SpeechRecognizer()
