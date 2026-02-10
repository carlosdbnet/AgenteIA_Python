import os
import time
import base64
from neonize.client import NewClient
from neonize.events import MessageEv, ReceiptEv
from neonize.utils.jid import Jid2String
from app.services.openai_service import generate_response, transcribe_audio
from dotenv import load_dotenv

load_dotenv()

# History management
conversation_history = {}
MAX_HISTORY = 10

def handle_message(client: NewClient, message: MessageEv):
    try:
        # Ignore messages from the bot itself
        if message.Info.MessageSource.IsFromMe:
            return

        chat_id = Jid2String(message.Info.MessageSource.Chat)
        
        # Extract text from different message types
        text = ""
        if message.Message.conversation:
            text = message.Message.conversation
        elif message.Message.extendedTextMessage and message.Message.extendedTextMessage.text:
            text = message.Message.extendedTextMessage.text
        elif message.Message.audioMessage or (message.Message.documentMessage and "audio" in message.Message.documentMessage.mimetype):
            is_ptt = message.Message.audioMessage.PTT if message.Message.audioMessage else False
            print(f"Captured audio from {chat_id} (PTT: {is_ptt}). Downloading...")
            
            try:
                audio_bytes = client.download_any(message.Message)
                if audio_bytes:
                    print(f"Audio downloaded successfully ({len(audio_bytes)} bytes). Transcribing...")
                    text = transcribe_audio(audio_bytes)
                    if text:
                        print(f"Transcription result: '{text}'")
                        text = "!bot " + text
                    else:
                        print("Transcription failed or returned empty text.")
                else:
                    print("Failed to download audio bytes.")
            except Exception as e:
                print(f"Error capturing audio: {e}")
        elif message.Message.imageMessage:
            caption = message.Message.imageMessage.caption or "Análise de imagem"
            print(f"Captured image from {chat_id}. Downloading...")
            try:
                image_bytes = client.download_any(message.Message)
                if image_bytes:
                    print(f"Image downloaded successfuly ({len(image_bytes)} bytes). Sending to Vision...")
                    b64_image = base64.b64encode(image_bytes).decode("utf-8")
                    
                    if chat_id not in conversation_history:
                        conversation_history[chat_id] = []
                    
                    history = conversation_history[chat_id]
                    # Format for OpenAI Vision
                    history.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"!bot {caption}"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                            }
                        ]
                    })
                    
                    # Force text to contain !bot to trigger processing below
                    text = f"!bot [IMAGEM] {caption}"
                else:
                    print("Failed to download image bytes.")
            except Exception as e:
                print(f"Error capturing image: {e}")
        
        if not text:
            return

        # Check for !bot prefix
        if text.startswith("!bot "):
            # Special case for images already in history
            if "[IMAGEM]" in text:
                prompt = text
            else:
                prompt = text[5:]
                if chat_id not in conversation_history:
                    conversation_history[chat_id] = []
                history = conversation_history[chat_id]
                history.append({"role": "user", "content": prompt})
            
            history = conversation_history[chat_id]
            
            # Keep history small
            if len(history) > MAX_HISTORY:
                history.pop(0)
                
            print(f"Generating response for {chat_id}...")
            response_text = generate_response(history)
            
            # Add to history
            history.append({"role": "assistant", "content": response_text})
            if len(history) > MAX_HISTORY:
                history.pop(0)
                
            # Send reply - Fixed argument order: (text, quoted_message)
            client.reply_message(response_text, message)
            print(f"Sent: {response_text[:50]}...")
    except Exception as e:
        print(f"Error in handle_message: {e}")
        import traceback
        traceback.print_exc()

def start_whatsapp():
    print("Starting WhatsApp Client (Neonize)...")
    # Neonize saves the session in a sqlite file by default
    client = NewClient("db.sqlite3")
    
    @client.event(MessageEv)
    def on_message(client: NewClient, message: MessageEv):
        handle_message(client, message)

    print("Scan the QR code to connect...")
    client.connect()
