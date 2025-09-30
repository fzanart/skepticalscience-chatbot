import os
import smtplib
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gradio as gr
from climate_workflow import ClimateWorkflow


def save_conversation(workflow_state, history):
    """Save conversation to file with timestamp"""
    # Create conversations folder
    os.makedirs("conversations", exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversations/conversation_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        fallacies_used = [
            fallacy_name for fallacy_name, _ in workflow_state.used_fallacies
        ]
        f.write(f"Fallacies used: {', '.join(fallacies_used)}\n")
        f.write(f"Final stage: {workflow_state.stage}\n")
        f.write(f"Deceiver rounds: {workflow_state.deceiver_rounds}\n\n")
        f.write("=== CONVERSATION HISTORY ===\n\n")

        for msg in history:
            f.write(f"{msg['role'].upper()}: {msg['content']}\n\n")

    print(f"Conversation saved to: {filename}")
    send_conversation_email(filename)


def send_conversation_email(filename):

    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    message = MIMEMultipart()
    message["Subject"] = f"Conversation File {filename}"
    message["From"] = sender_email
    message["To"] = recipient_email

    body = "Please find the attached conversation file."

    message.attach(MIMEText(body, "plain"))

    # Attach file
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", f"attachment; filename={os.path.basename(filename)}"
    )
    message.attach(part)

    # Send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())


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
        complete_history = history + [{"role": "assistant", "content": response}]
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
