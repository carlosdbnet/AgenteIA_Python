import os
import sys
import tempfile
import base64
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_system_prompt():
    system_content = os.getenv("systema_prompty") or os.getenv("SYSTEM_PROMPT") or "Você é um assistente útil e amigável."
    
    prompt_file = os.getenv("SYSTEM_PROMPT_FILE")
    if prompt_file and os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_content = f.read()
        except Exception as e:
            print(f"Error reading system prompt file: {e}")
            
    return system_content

def generate_response(messages):
    try:
        system_prompt = get_system_prompt()
        
        # Prepare messages for OpenAI
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Cheaper model with Vision support
            messages=api_messages
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "Desculpe, tive um erro ao processar sua mensagem."

def transcribe_audio(audio_bytes):
    try:
        # Save bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
            
        try:
            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"Transcription Error: {e}")
        return None

def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        # Download the image
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            return img_response.content
        return None
    except Exception as e:
        print(f"Image Generation Error: {e}")
        return None
