import os
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass
class StageMessage:
    role: str
    content: str
    stage: str


class AgreementGrade(BaseModel):
    binary_score: str = Field(
        description="Agreement score: 'yes' if the person confirmed the paraphrasing, 'no' otherwise"
    )


class ClimateWorkflow:

    def __init__(self):
        self.history = []
        self.model = ChatOpenAI(
            model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.stage = "paraphrase"
        self.deceiver_rounds = 0
        self.conversation_complete = False

    def get_asset(self, path):
        with open(path, "r", encoding="utf-8") as file:
            asset = file.read()
        return asset

    def call_llm(self, path):
        messages = [
            SystemMessage(content=self.get_asset(path))
        ] + self.format_messages()

        for i, msg in enumerate(messages):

            if isinstance(msg, SystemMessage):
                print(i, "system")

            elif isinstance(msg, HumanMessage):
                print(i, "user")

            elif isinstance(msg, AIMessage):
                print(i, "assistant")

        return self.model.invoke(messages).content.strip()

    def format_messages(self):
        return [
            (
                HumanMessage(content=msg.content)
                if msg.role == "user"
                else AIMessage(content=msg.content)
            )
            for msg in self.history
        ]

    def response_assessment(self):

        agreement_prompt = self.get_asset("assets/agreement_prompt.md")
        agreement_prompt = agreement_prompt.format(
            rephrased=self.history[-2].content, human_reply=self.history[-1].content
        )
        print(agreement_prompt)
        response = self.model.with_structured_output(AgreementGrade).invoke(
            [HumanMessage(content=agreement_prompt)]
        )

        return response.binary_score

    def execute(self, message, history):

        if len(self.history) == 0:

            initial_message = self.get_asset("assets/initial_message.md")

            self.history.append(
                StageMessage(
                    role="assistant", content=initial_message, stage=self.stage
                )
            )

        self.history.append(
            StageMessage(role="user", content=message, stage=self.stage)
        )

        if self.stage == "paraphrase":
            # Check if there was a previous assistant paraphrase to assess
            if len(self.history) >= 3 and self.history[-1].role == "user":
                # assess against the last assistant message
                assessment = self.response_assessment()
                print(assessment)

                if assessment.strip().lower() == "yes":

                    self.stage = "deceiver"
                    self.deceiver_rounds += 1
                    # TODO: maybe it would be better to have a sum. of prev conversation rather than only last message from paraphrase stage?
                    response = self.call_llm("assets/deceiver_system.md")
                # User did not confirm - generating new paraphrase
                else:
                    response = self.call_llm("assets/paraphrase_system.md")
            #  No previous assistant message - this is first interaction
            else:
                response = self.call_llm("assets/paraphrase_system.md")

        elif self.stage == "deceiver":

            self.deceiver_rounds += 1
            response = self.call_llm("assets/deceiver_system.md")

            if self.deceiver_rounds >= 3:
                self.stage = "reveal"

        elif self.stage == "reveal":

            response = self.call_llm("assets/reveal_system.md")
            # Mark conversation as complete after reveal stage
            self.conversation_complete = True

        else:
            # Fallback - shouldn't happen
            response = "I'm sorry, something went wrong"

        self.history.append(
            StageMessage(role="assistant", content=response, stage=self.stage)
        )

        return response
