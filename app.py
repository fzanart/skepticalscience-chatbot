import os
import json
from datetime import datetime, timedelta
import gradio as gr
from climate_workflow import ClimateWorkflow
from huggingface_hub import HfApi


def save_conversation(workflow_state, history):
    """Save conversation to JSON file"""
    os.makedirs("conversations", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation_id = f"conversation_{timestamp}"
    filename = f"conversations/{conversation_id}.json"

    # Structure the data
    data = {
        "id": conversation_id,
        "timestamp": timestamp,
        "fallacies_used": [
            fallacy_name for fallacy_name, _ in workflow_state.used_fallacies
        ],
        "messages": [
            {"id": idx, "role": msg["role"], "message": msg["content"]}
            for idx, msg in enumerate(history)
        ],
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Conversation saved to: {filename}")
    upload_to_hf(filename)


def upload_to_hf(filename):
    """Upload to HF Dataset if configured"""
    hf_token = os.environ.get("HF_TOKEN")
    dataset_repo = os.environ.get("HF_DATASET_REPO")

    try:
        api = HfApi()
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=os.path.basename(filename),
            repo_id=dataset_repo,
            repo_type="dataset",
            token=hf_token,
        )
        print(f"Uploaded to {dataset_repo}")
    except Exception as e:
        print(f"Upload failed: {e}")


def get_initial_messages():
    # Create a temporary instance just to get the initial message
    temp_cw = ClimateWorkflow()
    return [
        {
            "role": "assistant",
            "content": temp_cw.get_asset("assets/initial_message.md"),
        }
    ]


def chat_fn(message, history, workflow_state, session_data):
    current_time = datetime.now()

    # Initialize session data for new users
    if session_data is None:
        session_data = {"start_time": current_time, "last_activity": current_time}

    # Initialize workflow state for new users
    if workflow_state is None:
        workflow_state = ClimateWorkflow()

    # Check if 8 minutes passed since start of conversation
    time_since_start = current_time - session_data["start_time"]
    if time_since_start > timedelta(minutes=8):
        # Mark as complete and save conversation
        workflow_state.conversation_complete = True
        if history:  # Only save if there's actual conversation
            save_conversation(workflow_state, history)
        return (
            "Session timed out after 8 minutes. Thank you for participating!",
            workflow_state,
            session_data,
        )

    # Check if conversation is complete - block further messages
    if workflow_state.conversation_complete:
        return (
            "Thank you for participating! The conversation is now complete.",
            workflow_state,
            session_data,
        )

    # Update activity time and process normally
    session_data["last_activity"] = current_time

    # Execute with the user's specific workflow instance
    response = workflow_state.execute(message, history)

    # If conversation just completed, save history
    if workflow_state.conversation_complete:
        # Include the final response in history for saving
        complete_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ]
        save_conversation(workflow_state, complete_history)

    return response, workflow_state, session_data


with gr.Blocks() as chatbot:
    # Each user gets their own workflow state and session data
    workflow_state = gr.State()
    session_data = gr.State()

    chat = gr.ChatInterface(
        fn=chat_fn,
        type="messages",
        chatbot=gr.Chatbot(value=get_initial_messages(), type="messages"),
        additional_inputs=[workflow_state, session_data],
        additional_outputs=[workflow_state, session_data],
        flagging_mode="never",  # see:https://github.com/gradio-app/gradio/issues/2510
    )

chatbot.launch()
