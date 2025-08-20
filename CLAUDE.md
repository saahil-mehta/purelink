# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview
This repo hosts a local POC for a vertical Data Engineering Agent. The agent flow:  
User enters a shorthand source → model infers canonical source and confirms → lists ingestion options (focus: API) → enumerates endpoints → user selects → docs are fetched and saved to Markdown → model summarises instructions and lists required credentials/steps → user provides inputs → agent verifies connection → upon success, data is extracted and saved locally.  
Keep code simple, notebook-compliant, and aimed at cementing this end-to-end workflow.

## Development Standards
When writing code, adhere to these principles:
- Prioritize simplicity and readability; reliability is the main goal  
- Start with minimal functionality and verify it works before adding complexity  
- Test code frequently with realistic inputs and validate outputs  
- Create small testing environments for components hard to validate directly  
- Use functional and stateless approaches where they improve clarity  
- Keep core logic clean; push implementation details to the edges  
- Maintain consistent style in indentation, naming, and patterns  
- Balance file organization with simplicity—use only as many files as needed  
- In Jupyter notebooks, respect cell-based coding; code must run step by step, be debuggable, and show results clearly  
- Install dependencies by running `uv pip install` (uv package manager)

## Workflow Focus
- Capture intent and canonicalize source name  
- Discover ingestion methods (start with APIs)  
- Enumerate endpoints and link docs  
- Fetch full doc content, store to Markdown/PDF  
- Summarize setup requirements with exact links  
- Collect credentials and probe API for connectivity  
- Confirm success or self-resolve common errors  
- Save flow for reuse/editing later  

## Notes
- Do not assume external infra beyond local POC  
- Prefer clear modular Python for orchestration and lightweight helpers  
- Jupyter notebooks are the main demo surface  
- Never add emojis, if you find them remove them. And the code and language must always be UK English.