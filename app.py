import random
import gradio as gr
from langchain_openai import ChatOpenAI



model = ChatOpenAI(
    temperature=0,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    openai_organization=os.environ.get("OPENAI_ORGANIZATION_ID"),
    model_name="gpt-4o",
)



def simple_response(message):

    response = model.invoke(message)
    
    return response.content

demo = gr.ChatInterface(simple_response, type="messages", autofocus=False)

if __name__ == "__main__":
    demo.launch()