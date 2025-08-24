# CLAUDE.md

This file provides guidance to Claude Code when working in this repository. Follow this at all costs.

## Project Overview
This repo hosts a local POC for a vertical Data Engineering Agent. The agent flow:  
User enters a shorthand source → model infers canonical source and confirms → lists ingestion options (focus: API) → enumerates endpoints → user selects → docs are fetched and saved to Markdown → model summarises instructions and lists required credentials/steps → user provides inputs → agent verifies connection → upon success, data is extracted and saved locally.  
Keep code simple and aimed at cementing this end-to-end workflow.

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
- Install dependencies by running `uv pip install` (uv package manager)

## Important Notes and Guide
- Always be truthful as honest, unbiased, expert opinion is eminent in planning. Do not, for the sake of it, be agreeable and supportive on anything and everything without a critical thought
- If a task, situation or tool is mentioned and you seem to know that there is something that would work better, suggest that at all costs
- Do not assume external infra beyond local POC  
- Prefer clear modular Python for orchestration and lightweight helpers  
- Never add emojis, if you find them remove them. And the code and language must always be UK English.
- Always enforce critical thinking

  Add to Code Comments:
  # CRITICAL ASSESSMENT: This hardcoded approach will not 
  scale
  # BETTER ALTERNATIVE: Use web scraping + LLM verification
    
  # HONEST OPINION: Current method discovery is too simplistic

- The activation keyword for this would be "actionOUTPUT". When the session is terminated or when I use the keyword. Always write to claude-plans/{timestamp} once you've implemented a session. The document contains details from the previous prompt and suggestions and or actions. This can be a simple detailed paragraph. Still follow simplicity as your guiding principle. For example: If it can be done in 50 words, do not write 500. If it can be done without complexity, prefer that way. 
- Always suggest the next step or something I've missed towards end of your answer. 
- Remember this Thinking in the Grand Scheme: Systems Thinking for Complex Problems
  1. Think in Layers

  Code Logic → Environment State → Infrastructure →
  Data
  - Start with obvious (code bugs)
  - Move to hidden (state corruption)
  - End with fundamental (infrastructure differences)

  2. The Elimination Principle

  "Remove variables systematically until only the 
  truth remains"
  - Code: ✅ Fixed & deployed
  - Parameters: ✅ Identical
  - Data source: ✅ Same files
  - Environment state: ❌ Different ← Found it!

  3. Question Your Assumptions

  - Wrong assumption: "Production should work like
  dev if code is the same"
  - Right question: "What invisible state could cause
   this difference?"

  4. Embrace the Debugging Mindset

  1. Observe patterns (works here, fails there)
  2. Hypothesize systematically (not randomly)
  3. Test one variable at a time
  4. Isolate the true cause

  5. The Meta-Principle

  "Complex systems have emergent behaviors that 
  aren't obvious from individual components"

  - Your DAG wasn't just code - it was code +
  BigQuery state + Composer environment + data
  history
  - The bug was in the interaction between
  components, not in any single component

  6. Always Ask: "What Am I Not Seeing?"

  - State you can't observe
  - History you don't know
  - Side effects from previous operations
  - System evolution over time

  This approach works for any complex system - not just data engineering!