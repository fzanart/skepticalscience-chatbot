import os
import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app as graph

from uuid import uuid4

session_state = {
    "config": {"configurable": {"thread_id": str(uuid4())}}, 
    "interrupted": None,
    "authenticated": False
}


CHAT_PASSWORD = os.getenv("CHAT_PASSWORD")

def reset_session():
    """Reset the session with new thread_id"""
    session_state["config"]["configurable"]["thread_id"] = str(uuid4())
    session_state["interrupted"] = None

def chat(message, history):
    try:
        if not session_state["authenticated"]:
            if message.strip() == CHAT_PASSWORD:
                session_state["authenticated"] = True
            else:
                return "Please enter the correct password to access the chat."
        
        if session_state["interrupted"]:
            # Resume from interrupt
            result = graph.invoke(Command(resume=message), config=session_state["config"])
            session_state["interrupted"] = None
        else:
            # Start new or continue conversation
            state = {"messages": [HumanMessage(content=message)], "count": 0}
            result = graph.invoke(state, config=session_state["config"])
        
        # Check for interrupt
        if '__interrupt__' in result:
            session_state["interrupted"] = True
        else:
            # Check if conversation ended (no more nodes to execute)
            if result.get('messages') and len(result.get('messages', [])) > 0:
                reset_session()
        
        # Return last AI message
        for msg in reversed(result['messages']):
            if hasattr(msg, 'content') and 'AI' in str(type(msg)):
                return msg.content
        return "Ready to discuss climate change!"
    except:
        return "Error occurred. Please try again."

demo = gr.ChatInterface(chat, type="messages", title="Climate Bot")

if __name__ == "__main__":
    demo.launch()

