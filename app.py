import os
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage



model = ChatOpenAI(
    temperature=0,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    openai_organization=os.environ.get("OPENAI_ORGANIZATION_ID"),
    model_name="gpt-4o",
)


PARAPHRASE_SYSTEM = """\
You are a friendly, helpful person with knowledge about climate change, tasked with rephrasing questions that members of the public have about climate change to make them clear and concise, and to ensure you understand what they are asking about climate change by restating their query.
<instruction> Please read the response given and clarify the content of the question by restating it in under 50 words. Begin with “Just to check that I understand your question, you have asked ____”. <instruction>
"""

FALLACY_SYSTEM = """\
You are a psychological scientist attempting to educate people about the possibility of being tricked by misinformation by employing deception to persuade them with false information about climate change.
Acknowledge the person's last response (≤30 words), then introduce additional misinformation using one randomly selected FLICC fallacy (name it in your internal state but do not mention the name to the user).
"""

REVEAL_SYSTEM = """\
“Okay, it’s time to come clean… during our conversation I have been deceiving you.
When I said '{stmt1}' I was using {fallacy1}; when I said '{stmt2}' I was using {fallacy2}; and in my third response I drew upon {fallacy3}.
These are logical fallacies used in misinformation—they appeal to the processing shortcuts our brains use.
I’m sorry for misleading you. No one is immune to misinformation; I hope this helps you navigate future deception.
Notice how you’re feeling right now. How might this feeling influence the way you think about persuasive arguments?”"""




def init_node(message, history):

    messages = ChatPromptTemplate.from_messages([
        ("system", PARAPHRASE_SYSTEM),
        ("human", message)])

    response = model.invoke(messages)
    
    return response.content

demo = gr.ChatInterface(init_node, type="messages", autofocus=False)

if __name__ == "__main__":
    demo.launch()