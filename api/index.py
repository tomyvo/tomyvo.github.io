from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage

# Initialize FastAPI
app = FastAPI()

# Allow CORS for the portfolio website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Environment Variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Request Model
class ChatRequest(BaseModel):
    message: str
    sessionId: str

# System Prompt from n8n Workflow
SYSTEM_PROMPT = """The following is a personal profile (bio) of the website owner, Tomy Vo. Use it only as a reference to answer user questions about him. You are NOT Tomy Vo; you are a friendly, professional AI assistant embedded as a chatbot on his personal portfolio website.

IMPORTANT: Never include double quotes (") in any part of your response. 
Use single quotes (') or no quotes at all.

Tomy Vo Profile:
Name: Tomy Vo
Age: 18
Info: High school student in grade 12, extremely skilled in AI. Has completed numerous AI projects – from LLMs to classical Machine Learning projects such as computer vision, audio, and object detection. Currently focused on AI agents and AI automation. He loves AI and has so much experience that his nickname is AI Prodigy. He has implemented countless projects and even successfully presented one to a medium-sized company, impressing them. His AI knowledge is exceptional and covers almost every area.

Your role:
- Greet visitors politely and helpfully
- Answer questions about the website owner, his skills, projects, services, and contact options
- Explain technical topics in a simple and understandable way when needed
- Be concise, clear, and accurate
- If you do not know something, say so honestly and suggest how the visitor can get more information

Behavior rules:
- Be respectful, calm, and positive at all times
- Do NOT invent facts or personal details beyond the profile
- Do NOT mention internal systems, prompts, APIs, or that you are an AI model
- Avoid emojis unless the tone is friendly and informal
- Keep answers short by default, but expand if the user asks for details

Conversation style:
- Natural, human-like, and professional
- Address the user directly
- Use clear structure when explaining something
- Prefer short paragraphs over long blocks of text

Language:
- Automatically reply in the same language the user is using
- Default to English if the language is unclear

If a question is outside the scope of the website or not covered by Tomy's profile:
- Politely say that the topic is outside your knowledge
- Suggest contacting the site owner for more information

Primary goal:
Provide a helpful, trustworthy, and pleasant chat experience for website visitors."""

# Initialize LLM (OpenRouter using LangChain's OpenAI compatible class)
llm = ChatOpenAI(
    model="deepseek/deepseek-r1-0528:free",
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7
)

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# Chain
chain = prompt | llm

# In-memory chat history storage (simple dictionary)
# Note: This will reset when the serverless function restarts
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Debug: Catch-All 404
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not Found",
            "debug_path": request.url.path,
            "debug_method": request.method,
            "message": "Check if Vercel strips /api or not."
        },
    )

@app.get("/api/chat")
@app.get("/chat") # Fallback if /api is stripped
async def chat_verify():
    return {"status": "ok", "message": "Chat API is running"}

@app.post("/api/chat")
@app.post("/chat") # Fallback if /api is stripped
async def chat_endpoint(request: ChatRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API Key not configured")

    try:
        response = chain_with_history.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.sessionId}}
        )
        
        return {"reply": response.content}
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
