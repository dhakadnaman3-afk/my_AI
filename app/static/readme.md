# 💬 AI Chatbot Platform

A full-stack, ChatGPT-style AI chatbot built with FastAPI and vanilla JavaScript, powered by Groq LLM via LangChain. Supports multi-conversation history, cross-session memory, multi-format file understanding, AI image generation, and more.



![Python](https://img.shields.io/badge/Python-3.14-blue)




![FastAPI](https://img.shields.io/badge/FastAPI-backend-teal)




![LangChain](https://img.shields.io/badge/LangChain-LLM_orchestration-green)




![SQLite](https://img.shields.io/badge/SQLite-database-lightgrey)



---

## ✨ Features

- Real-time streaming responses — token-by-token output for a fast, responsive feel
- Multi-conversation history — create, rename, delete, and switch between separate chat threads (like ChatGPT's sidebar)
- Cross-session memory — automatically extracts and recalls durable facts about the user (name, preferences, etc.) across *different* conversations
- Search — full-text search across all past conversations and messages
- Multi-format file understanding — upload and query PDF, DOCX, CSV, JSON, and image files (OCR via Tesseract) as context for the chat
- AI image generation — generate images from text prompts using the Pollinations API
- Voice input — speech-to-text using the browser's Web Speech API
- Markdown rendering — code blocks, lists, and formatting rendered properly in responses
- Response regeneration — regenerate the last AI reply without retyping the question
- Model switching — toggle between a fast, lightweight model and a more capable one
- Chat export — download any conversation as a .txt file

---

## 🛠️ Tech Stack

| Layer        | Technology                                  |
|--------------|----------------------------------------------|
| Backend      | FastAPI, Uvicorn                              |
| LLM          | Groq API via LangChain (langchain-groq)     |
| Database     | SQLite                                        |
| Frontend     | HTML, CSS, Vanilla JavaScript                 |
| File parsing | PyPDF, python-docx, Pillow, Tesseract OCR     |
| Image Gen    | Pollinations.ai API                           |

---

## 📂 Project Structure