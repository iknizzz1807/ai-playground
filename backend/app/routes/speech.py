from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from ..models.speech_recognizer import speech_recognizer
from ..utils.audio_processing import validate_audio_file, process_base64_audio
import io

router = APIRouter()


class AudioData(BaseModel):
    audio: str
    format: Optional[str] = "wav"


@router.post("/transcribe")
async def transcribe_audio(data: AudioData):
    """Transcribe speech from base64 encoded audio"""
    try:
        # Process the base64 audio data
        audio_data, format_type, error = process_base64_audio(data.audio)

        if error:
            return JSONResponse(status_code=400, content={"error": error})

        # Transcribe the audio
        result = speech_recognizer.transcribe(data.audio, format_type or data.format)
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Error processing request: {str(e)}"}
        )


@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Transcribe speech from uploaded audio file"""
    try:
        # Read file content
        file_content = await file.read()

        # Validate file
        valid, message = validate_audio_file(file_content, file.filename)
        if not valid:
            return JSONResponse(status_code=400, content={"error": message})

        # Get file format
        format_type = file.filename.split(".")[-1].lower()

        # Transcribe the audio
        result = speech_recognizer.transcribe(file_content, format_type)
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Error processing upload: {str(e)}"}
        )
