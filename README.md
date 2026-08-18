---
title: TechTailor Prototype
emoji: 👔
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# TechTailor Customer Experience Agent Prototype

A Virtual Tailoring Consultant + Style Advisor + Measurement Assistant prototype built with FastAPI and LangGraph, running in a Docker container.

## How The Agent Works

The app is designed to explain itself from first principles when asked. The core idea is:

1. An LLM alone only turns text into text.
2. TechTailor adds state, routing, and persistence so the conversation can remember context and follow different paths.
3. LangGraph gives that structure a clean shape: shared state, nodes, and edges.
4. TechTailor currently uses routing plus persistence, while more advanced loop, tool, and resume behaviors can be added later.

If you ask the assistant how the system works, it should explain the flow slowly and avoid assuming any prior knowledge.

## Local Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env` with `GROQ_API_KEY`.
3. Start the server:
   ```bash
   python -m uvicorn server:app --port 8000
   ```
