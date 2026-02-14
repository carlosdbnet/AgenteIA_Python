import os
import time
import base64
from neonize.client import NewClient
from neonize.events import MessageEv, ReceiptEv
from neonize.utils.jid import Jid2String, JID
from neonize.utils.enum import ChatPresence, ChatPresenceMedia
from app.services.openai_service import generate_response, transcribe_audio, generate_image
from app.utils.script_runner import run_script
from app.services.flow_service import process_flow
from app.services import database
from dotenv import load_dotenv

load_dotenv()

# Global client to be accessed by other services (like webhooks)
whatsapp_client = None
conversation_history = {}
registration_state = {}  # Track users in registration process
MAX_HISTORY = 10

def send_whatsapp_message(jid_str: str, text: str):
    """
    Sends a message to a specific JID. 
    """
    global whatsapp_client
    if not whatsapp_client:
        print("❌ Erro: Cliente WhatsApp não inicializado.")
        return False
    
    try:
        # Simple JID formatting if it's just a phone number
        if "@" not in jid_str:
            jid_str = jid_str.strip().replace("+", "").replace(" ", "")
            jid_str = f"{jid_str}@s.whatsapp.net"
            
        # Parse JID components (protobuf JID requires all fields explicitly)
        if "@" in jid_str:
            user_part, server_part = jid_str.split("@")
            target_jid = JID(
                User=user_part, 
                Server=server_part,
                RawAgent=0,
                Device=0,
                Integrator=0,
                IsEmpty=False
            )
        else:
            # Fallback if split fails
            target_jid = JID(
                User=jid_str, 
                Server="s.whatsapp.net",
                RawAgent=0,
                Device=0,
                Integrator=0,
                IsEmpty=False
            )
        
        whatsapp_client.send_message(to=target_jid, message=text)
        print(f"✅ Mensagem enviada para {jid_str}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para {jid_str}: {e}")
        import traceback
        traceback.print_exc()
        return False

def handle_message(client: NewClient, message: MessageEv):
    try:
        # Ignore messages from the bot itself
        if message.Info.MessageSource.IsFromMe:
            return

        chat_id = Jid2String(message.Info.MessageSource.Chat)
        
        # Extract phone number from chat_id (format: 5544999849929@s.whatsapp.net)
        phone = chat_id.split("@")[0] if "@" in chat_id else chat_id
        
        print(f"📩 [MSG] Processing message from: {chat_id} (Phone extracted: {phone})")

        # Check if user exists in database
        user = database.get_user_by_phone(phone)
        
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

        # === USER REGISTRATION FLOW ===
        # Handle registration process for new users
        if phone in registration_state:
            state = registration_state[phone]
            
            if state["step"] == "awaiting_name":
                # User provided their name
                proposed_name = text.strip()
                registration_state[phone] = {
                    "step": "awaiting_confirmation",
                    "name": proposed_name
                }
                client.reply_message(
                    f"Perfeito! Confirma que seu nome é *{proposed_name}*?\n\nResponda *SIM* para confirmar ou digite seu nome novamente.",
                    message
                )
                return
            
            elif state["step"] == "awaiting_confirmation":
                if text.strip().upper() in ["SIM", "S", "YES", "Y", "CONFIRMO"]:
                    # Save user to database
                    name = state["name"]
                    user_id = database.create_user(phone, name)
                    
                    if user_id:
                        del registration_state[phone]
                        client.reply_message(
                            f"✅ Cadastro concluído com sucesso!\n\nOlá, *{name}*! É um prazer ter você aqui. Como posso ajudar?",
                            message
                        )
                    else:
                        client.reply_message(
                            "❌ Ocorreu um erro ao salvar seu cadastro no banco de dados. Por favor, tente confirmar novamente ou digite seu nome novamente.",
                            message
                        )
                        # Keep state as awaiting_confirmation or reset to awaiting_name? 
                        # Letting them retry confirmation is valid if it was a transient DB error.
                    return
                else:
                    # User wants to correct the name
                    proposed_name = text.strip()
                    registration_state[phone] = {
                        "step": "awaiting_confirmation",
                        "name": proposed_name
                    }
                    client.reply_message(
                        f"Ok! Confirma que seu nome é *{proposed_name}*?\n\nResponda *SIM* para confirmar ou digite seu nome novamente.",
                        message
                    )
                    return
        
        # Check if user is new (not in database and not in registration)
        if not user and phone not in registration_state:
            # Start registration process
            registration_state[phone] = {"step": "awaiting_name"}
            client.reply_message(
                "👋 Olá! Vejo que é seu primeiro contato conosco.\n\n"
                "Para melhor atendê-lo, por favor, me diga seu *nome*:",
                message
            )
            return
        
        # Update last interaction for existing users
        if user:
            database.update_last_interaction(phone)
            # Add user name to conversation context for personalization
            user_name = user["name"]
        
        # === END USER REGISTRATION FLOW ===

        # 1. Process structured flow first (if not a command)
        is_command = text.startswith("!")
        if not is_command:
            flow_response, should_stop = process_flow(chat_id, text)
            if flow_response:
                client.reply_message(flow_response, message)
                if should_stop:
                    return
            else:
                # If flow returns None, it means the user is in FREE_CHAT
                # Automatically prefix with !bot to trigger OpenAI
                text = "!bot " + text
        
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
            
            # Simulate typing
            chat_jid = message.Info.MessageSource.Chat
            client.send_chat_presence(chat_jid, ChatPresence.CHAT_PRESENCE_COMPOSING, ChatPresenceMedia.CHAT_PRESENCE_MEDIA_TEXT)
            
            response_text = generate_response(history)
            
            # Add to history
            history.append({"role": "assistant", "content": response_text})
            if len(history) > MAX_HISTORY:
                history.pop(0)
                
            # Send response using send_message if reply fails or as alternative
            # Some JIDs (@lid) work better with direct send_message
            try:
                # First try reply
                client.reply_message(response_text, message)
            except Exception as e:
                print(f"⚠️ Reply failed, attempting direct send: {e}")
                client.send_message(to=message.Info.MessageSource.Chat, message=response_text)
            
            print(f"Sent: {response_text[:50]}...")
        
        # Check for !image or !imagem prefix
        elif text.startswith("!img "):
            prompt = text.split(" ", 1)[1]
            print(f"Generating image for {chat_id}: {prompt}")
            
            # Send a "generating" message
            client.reply_message("🎨 Gerando sua imagem... Aguarde um momento.", message)
            
            # Also show typing status for image generation
            chat_jid = message.Info.MessageSource.Chat
            client.send_chat_presence(chat_jid, ChatPresence.CHAT_PRESENCE_COMPOSING, ChatPresenceMedia.CHAT_PRESENCE_MEDIA_TEXT)
            
            image_bytes = generate_image(prompt)
            if image_bytes:
                chat_jid = message.Info.MessageSource.Chat
                client.send_image(chat_jid, image_bytes, caption=f"Aqui está sua imagem: {prompt}", quoted=message)
                print(f"Image sent to {chat_id}")
            else:
                client.reply_message("❌ Desculpe, tive um erro ao gerar sua imagem.", message)
        
        # Check for !run script command
        elif text.startswith("!run "):
            parts = text.split(" ")
            if len(parts) < 2:
                client.reply_message("💡 Uso: !run [nome_do_script] [parametros...]", message)
                return
                
            script_name = parts[1]
            script_args = parts[2:]
            
            print(f"Executing script '{script_name}' with args {script_args} for {chat_id}")
            client.reply_message(f"⚙️ Executando script '{script_name}'...", message)
            
            output = run_script(script_name, script_args)
            client.reply_message(f"📄 Resultado:\n\n{output}", message)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        import traceback
        traceback.print_exc()

def start_whatsapp():
    global whatsapp_client
    print("Starting WhatsApp Client (Neonize)...")
    # Neonize saves the session in a sqlite file by default
    whatsapp_client = NewClient("db.sqlite3")
    
    @whatsapp_client.event(MessageEv)
    def on_message(client: NewClient, message: MessageEv):
        handle_message(client, message)

    print("Scan the QR code to connect...")
    whatsapp_client.connect()
