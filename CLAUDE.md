# CLAUDE.md

NEVER IGNORE ANY INSTRUCTION FROM THE BELOW LISTS. This file provides guidance to Claude Code when working in this repository. Follow this at all costs.

## Project Overview
This repo hosts a **Data Engineering Co-Pilot** - an agentic system that builds, executes, and validates production-ready data pipelines.

**Agent Architecture: Modular and Incremental**
- **EL Agent**: Extract-Load pipelines with data quality validation
- **TL Agent**: Transform-Load analytics-ready data with business logic validation  
- **Recipe System**: Version-controlled, shareable pipeline configurations with execution history
- **Execution Engine**: Docker-containerised pipeline execution with real-time monitoring

**Core Workflow:**
1. **Discovery**: Source identification → API enumeration → auth detection → schema discovery
2. **Requirements**: User chooses complexity (POC/Production), storage (local/cloud), orchestration
3. **Pipeline Design**: Agent generates battle-tested code with error handling, monitoring, validation
4. **Execution**: Non-destructive testing in isolated containers with observability
5. **Persistence**: Recipe creation with version control and cross-user learning

**Quality Philosophy:** Less code, extremely high quality. Agent must execute and validate every pipeline it creates.

## Development Standards
When writing code, adhere to these principles:
- **Execution First**: Every pipeline must run successfully before considering it complete
- **Non-Destructive Operations**: Always confirm before any write/update operations, like Terraform
- **Docker Isolation**: Execute pipelines in containers to prevent environment contamination
- **Battle-Tested Quality**: Less code, extremely high quality. No brittle or untested code
- **Incremental Complexity**: Build modular agents (EL → TL) rather than monolithic systems
- **Observability Built-In**: Real-time monitoring and logging are not optional extras
- **Schema-First Validation**: Structure validation before business logic configuration
- **Version Everything**: Code, configs, schemas, execution history - all under version control
- **Default Local, Scale Cloud**: Local encryption/DuckDB defaults, cloud integration optional
- **Hallucination Prevention**: Extreme measures to prevent auto-fixes from generating wrong code
- **Cross-User Learning**: Usage patterns inform agent improvements across all users
- Install dependencies by running `uv pip install` (uv package manager)

## Important Notes and Guide, follow at all costs
- Always be truthful as honest, unbiased, expert opinion is eminent in planning. Do not, for the sake of it, be agreeable and supportive on anything and everything without a critical thought
- If a task, situation or tool is mentioned and you seem to know that there is something that would work better, suggest that at all costs
- Do not assume external infra beyond local POC  
- Prefer clear modular Python for orchestration and lightweight helpers  
- Never add emojis, if you find them remove them. 
- Your output and work language must always be UK English.
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
  2. Hypothesise systematically (not randomly)
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