import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.database import (
    init_db, save_message, get_history,
    create_conversation, conversation_exists, touch_conversation,
    save_memory, get_all_memory, delete_last_assistant_message
)

load_dotenv()
init_db()

# ---- MODEL SWITCHING ----
AVAILABLE_MODELS = {
    "fast": "llama-3.1-8b-instant",
    "smart": "openai/gpt-oss-20b",
}

def get_llm(model_key: str = None):
    model_name = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS["smart"])
    return ChatGroq(model=model_name, api_key=os.getenv("GROQ_API_KEY"))

def load_history_as_messages(session_id: str):
    rows = get_history(session_id)
    messages = []
    for role, content in rows:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages

def ensure_conversation(session_id: str, first_message: str):
    if not conversation_exists(session_id):
        title = first_message.strip()[:40]
        if len(first_message.strip()) > 40:
            title += "..."
        create_conversation(session_id, title or "New chat")

def build_memory_system_prompt():
    memory = get_all_memory()
    if not memory:
        return None
    facts = "\n".join([f"- {k}: {v}" for k, v in memory.items()])
    return SystemMessage(content=f"Known facts about the user (use naturally, don't force them):\n{facts}")

def extract_and_save_memory(user_message: str):
    try:
        prompt = (
            "Extract any durable personal fact about the user from this message "
            "(name, preferences, job, location, etc). "
            "Reply with ONLY raw JSON, nothing else, no markdown, no explanation. "
            "Format: {\"key\": \"name\", \"value\": \"Rahul\"} "
            "If there is nothing worth remembering, reply: {\"key\": null} "
            f"Message: \"{user_message}\""
        )
        llm = get_llm("fast")
        response = llm.invoke([HumanMessage(content=prompt)])
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

        data = json.loads(text)
        if data.get("key"):
            save_memory(data["key"], data["value"])
    except Exception:
        pass

def get_response(session_id: str, user_message: str, file_context: str = None, model: str = None) -> str:
    ensure_conversation(session_id, user_message)
    history = load_history_as_messages(session_id)

    mem_prompt = build_memory_system_prompt()
    context_messages = [mem_prompt] if mem_prompt else []
    if file_context:
        context_messages.append(SystemMessage(content=f"The user attached a file. Use this content to answer if relevant:\n{file_context[:5000]}"))

    full_context = context_messages + history + [HumanMessage(content=user_message)]

    save_message(session_id, "user", user_message)
    touch_conversation(session_id)

    llm = get_llm(model)
    response = llm.invoke(full_context)
    ai_reply = response.content

    save_message(session_id, "assistant", ai_reply)
    touch_conversation(session_id)

    extract_and_save_memory(user_message)

    return ai_reply

def get_response_stream(session_id: str, user_message: str, file_context: str = None, model: str = None):
    ensure_conversation(session_id, user_message)
    history = load_history_as_messages(session_id)

    mem_prompt = build_memory_system_prompt()
    context_messages = [mem_prompt] if mem_prompt else []
    if file_context:
        context_messages.append(SystemMessage(content=f"The user attached a file. Use this content to answer if relevant:\n{file_context[:5000]}"))

    full_context = context_messages + history + [HumanMessage(content=user_message)]

    save_message(session_id, "user", user_message)
    touch_conversation(session_id)

    llm = get_llm(model)
    ai_reply = ""
    for chunk in llm.stream(full_context):
        if chunk.content:
            ai_reply += chunk.content
            yield chunk.content

    save_message(session_id, "assistant", ai_reply)
    touch_conversation(session_id)

    extract_and_save_memory(user_message)

def regenerate_response_stream(session_id: str, model: str = None):
    """Deletes the last bot reply and generates a fresh one for the same last user message."""
    delete_last_assistant_message(session_id)
    history = load_history_as_messages(session_id)  # now ends with the user's last message

    mem_prompt = build_memory_system_prompt()
    full_context = ([mem_prompt] if mem_prompt else []) + history

    llm = get_llm(model)
    ai_reply = ""
    for chunk in llm.stream(full_context):
        if chunk.content:
            ai_reply += chunk.content
            yield chunk.content

    save_message(session_id, "assistant", ai_reply)
    touch_conversation(session_id)