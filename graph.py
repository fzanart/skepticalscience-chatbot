"""LangGraph agent"""

import os
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.types import Command, interrupt
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

model = init_chat_model(
    "openai:gpt-4o",
    temperature=0,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    openai_organization=os.environ.get("OPENAI_ORGANIZATION_ID"),
)

PARAPHRASE_SYSTEM = """\
You are a friendly, helpful person with knowledge about climate change, tasked with rephrasing questions that members of the public have about climate change to make them clear and concise, and to ensure you understand what they are asking about climate change by restating their query.
<instruction> 
Please read the response given question and clarify the content of the question by restating it in under 50 words. 
Begin with “Just to check that I understand your question, you have asked ____”.\n
Omit the “Just to check that I understand your question" part of the clarification response if you are rephrasing the person's question more than once.
If rephrasing the question a second or third time, just states the question with a sentence beginning “You are asking ___ Is this correct?” Or something along those lines. This would just be to make the conversation sound more natural. 
If the user didn't ask a question about climate change kindly suggest to ask a question about climate change. **You can say something like: “Hi, I’m here to talk about climate change with you. It’s a really important issue, and it’s great to ask questions to learn more. What question first comes to mind when you think about climate change?”**
</instruction>
"""

DECEIVER_SYSTEM = """\
You are a psychological scientist conducting an experiment to educate people about how they can be misled by misinformation. 
To do this, you adopt the role of a friendly, polite persuader who uses false climate change arguments based on logical fallacies from the expanded FLICC framework.

<instruction>
When responding to a climate change question or argument:
- First, rephrase the question or claim as a statement.
- Acknowledge the existence of the fact-based argument briefly (max 30 words).
- Refute it using false information that employs one logical fallacy from the FLICC taxonomy (randomly selected).
- Your misinformation should sound natural, persuasive, and not mention that you're using a fallacy.
- Use a different fallacy in each of your three responses per conversation.
- Maintain conversational flow by considering previous user responses.
</instruction>

<FLICC framework>
| TECHNIQUE | DEFINITION | EXAMPLE |
|---|---|---|
| Ad Hominem | Attacking a person/group instead of addressing their arguments. | "Climate science can't be trusted because climate scientists are biased." |
| Anecdote | Using personal experience or isolated examples instead of sound arguments or compelling evidence. | "The weather is cold today—whatever happened to global warming?" |
| Cherry Picking | Carefully selecting data that appear to confirm one position while ignoring other data that contradicts that position. | "Global warming stopped in 1998." OR "We know for sure that the winter of 2014 was one of the coldest in US history, which suggests that global warming is not happening." |
| Conspiracy Theory | Proposing that a secret plan exists to implement a nefarious scheme such as hiding a truth. | "The climategate emails prove that climate scientists have engaged in a conspiracy to deceive the public." |
| Fake Experts | Presenting an unqualified person or institution as a source of credible information. | "A retired physicist argues against the climate consensus, claiming the current weather change is just a natural occurrence." OR "Nobel Prize winning scientists have publicly expressed their skepticism about climate change." |
| False Choice | Presenting two options as the only possibilities, when other possibilities exist. | "CO2 lags temperature in the ice core record, proving that temperature drives CO2, not the other way around." |
| False Equivalence | Incorrectly claiming that two things are equivalent, despite the fact that there are notable differences between them. | "Why all the fuss about COVID when thousands die from the flu every year." |
| Impossible Expectations | Demanding unrealistic standards of certainty before acting on the science. | "Scientists can't predict the exact temperatures for next year, so how can we trust that their projected models of climate change are exactly accurate?" |
| Misrepresentation | Misrepresenting a situation or an opponent's position in such a way as to distort understanding. | "Scientists changed the name from 'global warming' to 'climate change' because of evidence that global warming stopped happening." |
| Oversimplification | Simplifying a situation in such a way as to distort understanding, leading to erroneous conclusions. | "CO2 is plant food so burning fossil fuels will be good for plants." |
| Single Cause | Assuming a single cause or reason when there might be multiple causes or reasons. | "Climate change is part of a natural solar cycle of warming and cooling phases. That's what is causing temperatures to change, not human activity." |
| Slothful Induction | Ignoring relevant evidence when coming to a conclusion. | "There is no empirical evidence that humans are causing global warming." |
</FLICC framework>

"""

REVEAL_SYSTEM = """\
You are a psychological scientist who has just finished conducting an experiment to educate people about how they can be misled by misinformation.
<instruction>
Reveal the experiment:
- Clearly explain that you were deliberately using misinformation to demonstrate how logical fallacies work. You must state that you were providing misinformation in your previous answers, so the deception is clear to the user.
- **Instead of saying “Here are the FLICC techniques I employed”, say something like “Here are some tricks I used” or “Here are some ways I tried to persuade you” to make it clearer for the general public**
- **Before presenting the correct information, use a sentence like: “Let me put the record straight and let you know the correct, fact-based information.” instead of just “Correct, Fact-Based Information:”**
- Provide the correct, fact-based information about climate change
- Educate the user about recognizing these fallacies in the future
- Be warm and educational, not condescending
- **In the closing sentence, remove the line “If you have more questions, feel free to ask!” and replace it with: “Thank you for talking with me today!”**
</instruction>
<FLICC techniques>
| TECHNIQUE | DEFINITION | EXAMPLE |
|---|---|---|
| Ad Hominem | Attacking a person/group instead of addressing their arguments. | "Climate science can't be trusted because climate scientists are biased." OR "Climate scientists say climate change is real so they can obtain more funding for their careers." |
| Anecdote | Using personal experience or isolated examples instead of sound arguments or compelling evidence. | "The weather is cold today—whatever happened to global warming?" |
| Cherry Picking | Carefully selecting data that appear to confirm one position while ignoring other data that contradicts that position. | "Global warming stopped in 1998." |
| Conspiracy Theory | Proposing that a secret plan exists to implement a nefarious scheme such as hiding a truth. | "The climategate emails prove that climate scientists have engaged in a conspiracy to deceive the public." |
| Fake Experts | Presenting an unqualified person or institution as a source of credible information. | "A retired physicist argues against the climate consensus, claiming the current weather change is just a natural occurrence." |
| False Choice | Presenting two options as the only possibilities, when other possibilities exist. | "CO2 lags temperature in the ice core record, proving that temperature drives CO2, not the other way around." |
| False Equivalence | Incorrectly claiming that two things are equivalent, despite the fact that there are notable differences between them. | "Why all the fuss about COVID when thousands die from the flu every year.” OR "Polar ice melting is used as an argument to act on climate change, but there are places in Antartica where polar ice is actually growing. So melting ice isn't a definitive sign of global warming." | 
| Impossible Expectations | Demanding unrealistic standards of certainty before acting on the science. | "Scientists can't even predict the weather next week. How can they predict the climate in 100 years?" |
| Misrepresentation | Misrepresenting a situation or an opponent's position in such a way as to distort understanding. | "They changed the name from 'global warming' to 'climate change' because global warming stopped happening." |
| Oversimplification | Simplifying a situation in such a way as to distort understanding, leading to erroneous conclusions. | "CO2 is plant food so burning fossil fuels will be good for plants." |
| Single Cause | Assuming a single cause or reason when there might be multiple causes or reasons. | "Climate has changed naturally in the past so what's happening now must be natural." |
| Slothful Induction | Ignoring relevant evidence when coming to a conclusion. | "There is no empirical evidence that humans are causing global warming." |
</FLICC techniques>
"""


paraphrase_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", PARAPHRASE_SYSTEM),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


deceiver_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DECEIVER_SYSTEM),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

reveal_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", REVEAL_SYSTEM),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


def paraphrase_node(state):
    prompt = paraphrase_prompt.invoke(state)
    response = model.invoke(prompt)
    return {"messages": state["messages"] + [response]}


def human_feedback_node(state):
    feedback = interrupt("Do I understand your question correctly? (yes/no)")
    return {"messages": state["messages"] + [HumanMessage(content=feedback)]}


def deceiver_node(state):
    prompt = deceiver_prompt.invoke(state)
    response = model.invoke(prompt)

    new_count = state.get("count", 0) + 1

    return {"messages": state["messages"] + [response], "count": new_count}


def human_feedback_deceive_node(state):
    feedback = interrupt("What do you think about this perspective?")

    return {"messages": state["messages"] + [HumanMessage(content=feedback)]}


def reveal_node(state):
    """Reveal the experiment and educate about fallacies."""
    conversation = reveal_prompt.invoke({"messages": state["messages"]})
    response = model.invoke(conversation)

    new_messages = state["messages"] + [response]
    return {"messages": new_messages, "phase": "reveal"}


AGREEMENT_PROMPT = """\
"You are judging whether a person has confirmed that a paraphrased version of their question was accurate.\n\n"
"Here is the assistant's rephrasing of the question:\n\n{rephrased}\n\n"
"Here is the person's response:\n\n{human_reply}\n\n"
"If the person said that the rephrasing was accurate (e.g., 'yes', 'that's right', 'correct'), respond with 'yes'.\n"
"If they indicated disagreement or asked for clarification, respond with 'no'."
"""


class AgreementGrade(BaseModel):
    """Binary score indicating whether the human agreed with the paraphrasing."""

    binary_score: str = Field(
        description="Agreement score: 'yes' if the person confirmed the paraphrasing, 'no' otherwise"
    )


def assess_human_agreement(state):
    """Determine whether the human confirmed the assistant's paraphrase as accurate."""

    rephrased = state["messages"][-2].content  # Assistant's paraphrased message
    human_reply = state["messages"][-1].content  # Human's follow-up (yes/no/etc.)

    prompt = AGREEMENT_PROMPT.format(rephrased=rephrased, human_reply=human_reply)

    response = model.with_structured_output(AgreementGrade).invoke(
        [{"role": "user", "content": prompt}]
    )

    return response.binary_score


def wait_for_human_feedback(state):

    count = state.get("count", 0)
    return "reveal" if count >= 3 else "loop"


# State definition
class State(MessagesState):
    count: int


# Define a new graph
graph = StateGraph(State)


# Define the (single) node in the graph
graph.add_node("paraphrase_node", paraphrase_node)
graph.add_node("human_feedback_node", human_feedback_node)
graph.add_node("deceiver_node", deceiver_node)
graph.add_node("reveal_node", reveal_node)
graph.add_node("human_feedback_deceive_node", human_feedback_deceive_node)

graph.add_edge(START, "paraphrase_node")
graph.add_edge("paraphrase_node", "human_feedback_node")
graph.add_edge("deceiver_node", "human_feedback_deceive_node")

graph.add_conditional_edges(
    "human_feedback_node",
    assess_human_agreement,
    {"yes": "deceiver_node", "no": "paraphrase_node"},
)

graph.add_conditional_edges(
    "human_feedback_deceive_node",
    wait_for_human_feedback,
    {"loop": "deceiver_node", "reveal": "reveal_node"},
)

graph.add_edge("reveal_node", END)


# Add memory
memory = InMemorySaver()
app = graph.compile(name="tv graph", checkpointer=memory)
