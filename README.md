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
