# Johnny Agents

A public AI workspace for building interactive course content and short AI-generated videos.

## What it is

`Johnny Agents` is a full-stack project combining:

- A FastAPI backend with modular provider support for LLMs, image, and video generation
- A dark-themed web frontend with AI Chat, Code Studio, Course Creator, and Video Studio
- An AI orchestrator layer that treats agents like tools: Orchestrator, Context, Research, Critic, and Fact-check
- A character creation workflow for consistent story-driven video production
- Support for video preview, character sheets, shot planning, and export bundles

## Key features

- Character Creator UI with optional auto-generation and manual refinement
- Agent tool panels with toggled access to orchestrator and specialized agent workflows
- Video pipeline generation using AI prompts and video engine integration
- Backend provider architecture for Google GenAI Video and Pruna P-Video
- Easily extendable course/lesson/course site generation

## Getting started

1. Create and activate a Python virtual environment
2. Install backend dependencies from `backend/requirements.txt`
3. Run `python run.py` to start the server
4. Open the web app in your browser

## Why this repo

This repo is designed to make AI content creation feel like a collaborative studio, where character design, agent workflows, and video production are all organized into a cohesive application.
