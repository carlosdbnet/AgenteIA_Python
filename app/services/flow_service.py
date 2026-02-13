import os
import json
from app.services import database

# Simple file-based persistence for user states
STATE_FILE = "user_states.json"

class UserState:
    START = "START"
    COLLECTING_NAME = "COLLECTING_NAME"
    FREE_CHAT = "FREE_CHAT"

def load_states():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_states(states):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

def get_user_state(chat_id):
    states = load_states()
    if chat_id not in states:
        return {"state": UserState.START, "data": {}}
    return states[chat_id]

def update_user_state(chat_id, state, data=None):
    states = load_states()
    if chat_id not in states:
        states[chat_id] = {"state": state, "data": {}}
    
    states[chat_id]["state"] = state
    if data:
        states[chat_id]["data"].update(data)
    
    save_states(states)

def process_flow(chat_id, text):
    """
    Manages the conversation flow logic.
    Returns: (response_text, should_stop)
    If should_stop is True, the main handler should NOT call OpenAI.
    """
    user_info = get_user_state(chat_id)
    state = user_info.get("state", UserState.START)
    data = user_info.get("data", {})
    
    # Extract phone from chat_id for database lookup
    phone = chat_id.split("@")[0] if "@" in chat_id else chat_id
    db_user = database.get_user_by_phone(phone)

    # Reset flow if user says "reset" or "restart"
    if text.lower() in ["reiniciar", "reset", "menu"]:
        update_user_state(chat_id, UserState.START, {})
        if db_user:
            return f"🔄 Fluxo reiniciado!\n\nOlá, *{db_user['name']}*! Como posso ajudar?", True
        else:
            return "🔄 Fluxo reiniciado!\n\nOlá! Bem-vindo(a) à Shopfono! ✨", True

    if state == UserState.START:
        # Check if user is already registered in database
        if db_user:
            # User is registered, greet with name and go directly to FREE_CHAT
            update_user_state(chat_id, UserState.FREE_CHAT, {"name": db_user['name']})
            return f"Olá, *{db_user['name']}*! 😊\n\nComo posso ajudar você hoje?", True
        else:
            # New user, collect name
            update_user_state(chat_id, UserState.COLLECTING_NAME)
            return "Olá! Bem-vindo(a) à Shopfono! ✨\n\nEu sou sua assistente virtual. Para começarmos, como posso te chamar?", True

    elif state == UserState.COLLECTING_NAME:
        name = text.strip()
        # Skip interest collection, go directly to FREE_CHAT
        update_user_state(chat_id, UserState.FREE_CHAT, {"name": name})
        return f"Prazer em te conhecer, *{name}*! 😊\n\nComo posso te ajudar especificamente agora? Pode me perguntar qualquer coisa!", True

    # If state is FREE_CHAT, we return None to let the main handler use OpenAI
    return None, False
