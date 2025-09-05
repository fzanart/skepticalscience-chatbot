# Chatbot Project: Climate Misinformation Inoculation Chatbot

An educational chatbot that teaches people to recognize climate misinformation by using psychological "inoculation" techniques - deliberately exposing users to misinformation before revealing the fallacies used.

## What This Is

This is a research-based educational tool that:

1. Clarifies your climate change question by paraphrasing it
2. Deceives you with 3 rounds of climate misinformation using FLICC fallacy techniques
3. Reveals the experiment and teaches you about the logical fallacies that were used

The goal is to "inoculate" people against real misinformation by showing them how these techniques work in a controlled, educational setting.

## How It Works

3-Phase Process:

- Paraphrase Phase: Bot clarifies your climate question
- Misinformation Phase: Presents false arguments using different FLICC fallacies (Ad Hominem, Cherry Picking, Fake Experts, etc.)
- Reveal Phase: Exposes the experiment and educates about fallacy recognition

## Tech Stack

- Backend: LangGraph with OpenAI GPT-4o-mini
- Frontend: Gradio chat interface
- Hosting: Hugging Face Spaces
- Psychology Framework: FLICC taxonomy of logical fallacies

<!-- ## How to Run Locally

```bash
# 1. Activate environment
conda activate chatnode

# 2. Go to app folder
cd chatbot/app

# 3. Start LangGraph Studio (for development/testing)
langgraph dev
```

## Environment Variables Needed

```bash
OPENAI_API_KEY=your_openai_key
OPENAI_ORGANIZATION_ID=your_org_id
CHAT_PASSWORD=your_password
```

## Project Structure

```
chatbot/
├── app/
│   ├── graph.py          # Main LangGraph logic (3-phase flow)
│   └── gradio_app.py     # Frontend chat interface
└── requirements.txt
```

## Development Flow

1. Make changes in `chatbot/app`
2. Run `langgraph dev` to test
3. Use the web interface to chat and debug
4. Repeat

## Live Demo

🌐 **Hosted at**: https://huggingface.co/spaces/fzanartu/chatbot

## Development Notes

- Uses password protection for access control
- Session management with unique thread IDs
- Interrupt handling for user responses between phases
- Memory checkpointing to maintain conversation state

**TL;DR**: `conda activate fact-checking` → `cd chatbot/app` → `langgraph dev` -->