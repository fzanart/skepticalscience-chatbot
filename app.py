import os
import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app as graph
from uuid import uuid4

CHAT_PASSWORD = os.getenv("CHAT_PASSWORD")

# Global session state that resets on app restart
current_session = None

def get_session_state():
    """Get or create session state - resets on browser reload"""
    return {
        "config": {"configurable": {"thread_id": str(uuid4())}},
        "interrupted": None,
        "authenticated": False
    }

def reset_session():
    """Reset the session"""
    global current_session
    current_session = get_session_state()

def chat(message, history):
    global current_session
    
    # Initialize session if needed
    if current_session is None:
        current_session = get_session_state()
    
    try:
        # Check authentication first
        if not current_session.get("authenticated", False):
            if message.strip() == CHAT_PASSWORD:
                current_session["authenticated"] = True
                return "🔓 Access granted! Welcome to Climate Bot. How can I help you today?"
            else:
                return "🔒 Please enter the correct password to access the chat."
        
        # Normal chat logic after authentication
        if current_session["interrupted"]:
            # Resume from interrupt
            result = graph.invoke(Command(resume=message), config=current_session["config"])
            current_session["interrupted"] = None
        else:
            # Start new or continue conversation
            state = {"messages": [HumanMessage(content=message)], "count": 0}
            result = graph.invoke(state, config=current_session["config"])
        
        # Check for interrupt
        if '__interrupt__' in result:
            current_session["interrupted"] = True
        else:
            # Check if conversation ended (no more nodes to execute)
            if result.get('messages') and len(result.get('messages', [])) > 0:
                reset_session()  # This resets the session
        
        # Return last AI message
        for msg in reversed(result['messages']):
            if hasattr(msg, 'content') and 'AI' in str(type(msg)):
                return msg.content
        return "Ready to discuss climate change!"
        
    except Exception as e:
        return f"Error occurred: {str(e)}. Please try again."

demo = gr.ChatInterface(chat, type="messages", title="Climate Bot")

if __name__ == "__main__":
    demo.launch()