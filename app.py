import os
import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from graph import app as graph
from uuid import uuid4

CHAT_PASSWORD = os.getenv("CHAT_PASSWORD")

# Simple global state
authenticated = False
session_state = {"config": {"configurable": {"thread_id": "demo"}}, "interrupted": None}

def reset_session():
    """Reset the session with new thread_id"""
    session_state["config"]["configurable"]["thread_id"] = str(uuid4())
    session_state["interrupted"] = None

def close_session():
    """Close session and unauthenticate user"""
    global authenticated
    authenticated = False
    reset_session()

def chat(message, history):
    global authenticated
    
    # Check for session close command
    if message.strip().lower() == "close session":
        close_session()
        return "Session closed"
    
    # Check password first
    if not authenticated:
        if message.strip() == CHAT_PASSWORD:
            authenticated = True
            return "✅ Authenticated."
        else:
            return "🔒 Please enter the correct password."
    
    # Normal chat after authentication
    try:
        if session_state["interrupted"]:
            result = graph.invoke(Command(resume=message), config=session_state["config"])
            session_state["interrupted"] = None
        else:
            state = {"messages": [HumanMessage(content=message)], "count": 0}
            result = graph.invoke(state, config=session_state["config"])
        
        if '__interrupt__' in result:
            session_state["interrupted"] = True
        else:
            if result.get('messages') and len(result.get('messages', [])) > 0:
                reset_session()
        
        for msg in reversed(result['messages']):
            if hasattr(msg, 'content') and 'AI' in str(type(msg)):
                return msg.content
        return "Ready to discuss climate change!"
    except:
        return "Error occurred. Please try again."

demo = gr.ChatInterface(chat, type="messages", title="🔒 Climate Bot")

if __name__ == "__main__":
    demo.launch()