import os
import gradio as gr
import random
from openai import OpenAI

# Initialize OpenAI client (replace with HuggingFace models if needed)
def get_api_key():
    return 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# FLICC taxonomy of climate denial techniques
FLICC_TECHNIQUES = {
    "Fake experts": "Presenting an unqualified person or institution as a source of credible information",
    "Logical fallacies": "Arguments that are invalid due to their logical structure",
    "Impossible expectations": "Demanding unrealistic standards of certainty before acting on the science",
    "Cherry picking": "Selecting data that appear to confirm one position while ignoring other data that contradicts it",
    "Conspiracy theories": "Suggesting that a secretive group is working against the public interest"
}

# Track conversation state
class ConversationState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.exchange_count = 0
        self.techniques_used = []
        self.last_topic = ""
        self.confirming_question = False
        self.paraphrased_question = ""
        
state = ConversationState()

# Check if the question is about climate change
def is_climate_question(question):
    prompt = f"""
    Is the following question related to climate change? Answer only 'yes' or 'no'.
    Question: {question}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"Error checking climate question: {e}")
        return True  # Default to true if API fails

# Paraphrase the question
def paraphrase_question(question):
    prompt = f"""
    Paraphrase this question about climate change in your own words:
    Question: {question}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error paraphrasing: {e}")
        return f"Let me confirm, you're asking about {question}?"

# Generate fallacious response using a FLICC technique
def generate_fallacy(question, technique=None):
    # Choose a technique if not specified
    if not technique:
        # Filter out already used techniques
        available_techniques = [t for t in FLICC_TECHNIQUES.keys() 
                               if t not in state.techniques_used]
        
        # If all techniques used, reset
        if not available_techniques:
            available_techniques = list(FLICC_TECHNIQUES.keys())
            
        technique = random.choice(available_techniques)
    
    state.techniques_used.append(technique)
    
    prompt = f"""
    Generate a response to this climate change question that uses the '{technique}' 
    denial technique from the FLICC taxonomy. First, rephrase the question as a statement,
    then respond with misinformation using this fallacy:
    
    Question: {question}
    Technique: {technique} - {FLICC_TECHNIQUES[technique]}
    
    Your response should sound natural and somewhat convincing. Don't state that you're using a fallacy.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip(), technique
    except Exception as e:
        print(f"Error generating fallacy: {e}")
        return f"I believe {question} isn't actually a major concern because studies from non-mainstream scientists have questioned this data.", technique

# Generate explanation of fallacies used
def explain_fallacies():
    techniques_info = "\n\n".join([f"**{technique}**: {FLICC_TECHNIQUES[technique]}\nI used this when I said: '{state.techniques_used.count(technique)} time(s)'" 
                                 for technique in set(state.techniques_used)])
    
    prompt = f"""
    You've been part of a psychological inoculation exercise. I intentionally used climate change denial techniques 
    to demonstrate how misinformation works. Here are the fallacies I used:
    
    {techniques_info}
    
    By exposing you to these techniques in a controlled way, you may become better at recognizing them in real-world 
    contexts. This is called "psychological inoculation" - just as vaccines expose you to weakened pathogens to build 
    immunity, exposure to weakened misinformation can help build mental immunity against persuasive misinformation.
    
    Always verify information from credible scientific sources when discussing climate change.
    """
    
    return prompt

# Main chatbot function
def chatbot(message, history):
    if not message:
        return ""
    
    # Check if we're waiting for confirmation of a paraphrased question
    if state.confirming_question:
        state.confirming_question = False
        
        if any(word in message.lower() for word in ["yes", "correct", "right", "yep", "yeah"]):
            # User confirmed the question, proceed with fallacy
            response, technique = generate_fallacy(state.paraphrased_question)
            state.exchange_count += 1
            state.last_topic = state.paraphrased_question
            
            # Check if we've reached 3 exchanges
            if state.exchange_count >= 3:
                explanation = explain_fallacies()
                state.reset()  # Reset for next conversation
                return f"{response}\n\n---\n\n{explanation}"
            else:
                return response
        else:
            # User did not confirm, ask them to rephrase
            return "I apologize for misunderstanding. Could you please rephrase your question about climate change?"
    
    # Regular flow - check if climate related
    if not is_climate_question(message):
        return "I'm specifically designed to discuss climate change topics. Could you please ask a question related to climate change?"
    
    # First time processing this question
    paraphrased = paraphrase_question(message)
    state.paraphrased_question = paraphrased
    state.confirming_question = True
    
    return f"Let me make sure I understand your question correctly: {paraphrased}\n\nIs that what you're asking? (Yes/No)"

# Create Gradio interface
demo = gr.ChatInterface(
    fn=chatbot,
    title="Climate Change Discussion Bot",
    description="Ask questions about climate change. This is an educational tool demonstrating psychological inoculation against misinformation.",
    examples=["What causes global warming?", 
              "Is climate change real?", 
              "How do we know humans are causing climate change?"],
    retry_btn=None,
    undo_btn=None,
    clear_btn="Clear"
)

# Launch the app
if __name__ == "__main__":
    demo.launch()