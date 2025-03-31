"""
Speech-to-text module for the English learning application
"""
import streamlit as st
import tempfile
import os
from openai import OpenAI

def transcribe_with_whisper(audio_bytes):
    """
    Transcribe audio using OpenAI's Whisper API
    
    Args:
        audio_bytes (bytes): Audio data in bytes from Streamlit's audio recorder
        
    Returns:
        str: Transcribed text
    """
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            temp_audio_file.write(audio_bytes)
            temp_audio_file_path = temp_audio_file.name
        
        # Use OpenAI's Whisper API to transcribe the audio
        client = OpenAI()
        
        with open(temp_audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up the temporary file
        os.unlink(temp_audio_file_path)
        
        return transcription.text
    
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None