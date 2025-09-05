import gradio as gr
from climate_workflow import ClimateWorkflow

cw = ClimateWorkflow()
initial_messages = [
    {
        "role": "assistant",
        "content": cw.get_asset("assets/initial_message.md"),
    }
]

gr.ChatInterface(
    fn=cw.execute,
    type="messages",
    chatbot=gr.Chatbot(value=initial_messages, type="messages"),
).launch()
