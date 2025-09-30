import os
import json
import random
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
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )
        self.stage = "paraphrase"
        self.deceiver_rounds = 0
        self.used_fallacies = []
        self.fallacies = self._load_fallacies()
        self.conversation_complete = False
        # self.user_question = None  # Store the confirmed user question for inoculation

    def _load_fallacies(self):
        """Load fallacies from the FLICC JSON file"""
        with open("assets/flicc.json", "r", encoding="utf-8") as file:
            return json.load(file)

    def _select_random_fallacy(self):
        """Select a random fallacy that hasn't been used yet"""
        used_fallacy_names = [fallacy_tuple[0] for fallacy_tuple in self.used_fallacies]
        available_fallacies = [
            fallacy
            for fallacy in self.fallacies.keys()
            if fallacy not in used_fallacy_names
        ]

        selected_fallacy = random.choice(available_fallacies)

        return selected_fallacy

    def _format_used_fallacies_text(self):
        """Format used fallacies and arguments for reveal stage"""
        formatted_fallacies = []
        for i, (fallacy_name, argument) in enumerate(self.used_fallacies, 1):
            fallacy_def = self.fallacies[fallacy_name]["definition"]
            formatted_fallacies.append(
                f"{i}. **{fallacy_name}**: {fallacy_def}\n"
                f'   - My argument: "{argument}"'
            )
        return "\n\n".join(formatted_fallacies)

    def get_asset(self, path):
        with open(path, "r", encoding="utf-8") as file:
            asset = file.read()
        return asset

    def call_llm(
        self, path, fallacy_data=None, reveal_data=None, inoculation_data=None
    ):
        system_content = self.get_asset(path)

        # If fallacy data is provided, format the system prompt with it
        if fallacy_data:
            system_content = system_content.format(
                FALLACY=fallacy_data["name"],
                DEFINITION=fallacy_data["definition"],
                EXAMPLE=fallacy_data["example"],
            )

        # If reveal data is provided, format with used fallacies
        if reveal_data:
            system_content = system_content.format(
                USED_FALLACIES_AND_ARGUMENTS=reveal_data["used_fallacies_and_arguments"]
            )

        # # If inoculation data is provided, format with user question
        # if inoculation_data:
        #     system_content = system_content.format(
        #         USER_QUESTION=inoculation_data["user_question"]
        #     )

        messages = [SystemMessage(content=system_content)] + self.format_messages()

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

                    # Transition to deceiver stage and start first round
                    self.stage = "deceiver"
                    self.deceiver_rounds += 1

                    # Select random fallacy and format prompt
                    fallacy_name = self._select_random_fallacy()
                    fallacy_data = {
                        "name": fallacy_name,
                        "definition": self.fallacies[fallacy_name]["definition"],
                        "example": self.fallacies[fallacy_name]["example"],
                    }
                    print(f"Using fallacy: {fallacy_name}")

                    response = self.call_llm(
                        "assets/deceiver_system.md", fallacy_data=fallacy_data
                    )

                    # Store (fallacy, argument) tuple
                    self.used_fallacies.append((fallacy_name, response))
            #  No previous assistant message - this is first interaction
            else:
                response = self.call_llm("assets/paraphrase_system.md")

        elif self.stage == "deceiver":

            self.deceiver_rounds += 1

            # Select random fallacy and format prompt
            fallacy_name = self._select_random_fallacy()
            fallacy_data = {
                "name": fallacy_name,
                "definition": self.fallacies[fallacy_name]["definition"],
                "example": self.fallacies[fallacy_name]["example"],
            }
            print(f"Using fallacy: {fallacy_name}")

            response = self.call_llm("assets/deceiver_system.md", fallacy_data)

            # Store (fallacy, argument) tuple
            self.used_fallacies.append((fallacy_name, response))

            if self.deceiver_rounds >= 3:
                self.stage = "reveal"

        elif self.stage == "reveal":

            # Format used fallacies and arguments
            fallacies_text = self._format_used_fallacies_text()
            reveal_data = {"used_fallacies_and_arguments": fallacies_text}

            response = self.call_llm("assets/reveal_system.md", reveal_data=reveal_data)
            self.conversation_complete = True

        else:
            # Fallback - shouldn't happen
            response = "I'm sorry, something went wrong"

        self.history.append(
            StageMessage(role="assistant", content=response, stage=self.stage)
        )

        return response
