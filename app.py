import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app as graph

session_state = {"config": {"configurable": {"thread_id": "demo"}}, "interrupted": None}

def chat(message, history):
    try:
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

