

    1. User Interaction Layer
       [ CLI | Web UI | API Gateway ]
         • Entry point for all requests.
         • API Gateway enforces mTLS, rate-limiting, OIDC/OAuth2 authentication.
         • CLI first for MVP; Web/API added post-MVP.
             │
             ▼
         Natural Language Request

    2. Intent & Planning Layer (AutoGen)
       [ Planner Agent Team – AutoGen GroupChat ]
         • Agents:
           – UserProxyAgent → queries user for missing details.
           – PlannerAgent → leads decomposition into executable plan.
           – ToolExpertAgent (post-MVP) → knows connector catalog & capabilities.
           – CriticAgent (post-MVP) → reviews plan for feasibility.
         • Output: PipelinePlan (structured JSON containing source, destination, schedule, sync mode, credentials reference, metadata).
             │
             ▼
         Structured PipelinePlan

    3. Orchestration Layer (LangGraph)
       [ Orchestration Agent – LangGraph State Machine ]
         • Deterministic execution of EL workflow.
         • Nodes:
           initialize_run → get_source_credentials → check_source_connection
           → discover_source_schema → run_data_sync → commit_final_state → handle_error
         • State persisted in Metadata Store after each step for resilience & auditability.
         • Human-in-the-loop support for approvals and manual fixes.
             │
             ▼
         Execution Step Calls

    4. Connector Invocation Layer
       [ Connector Agent – Sole MCP Client ]
         • Looks up connector in Connector Registry (Postgres).
         • Invokes MCP server tools: tool_check_connection, tool_discover_schema,
           tool_read_stream, tool_write_stream.
         • MCP abstracts away connector type (Docker container vs serverless function).

             │   (Get Credentials)
             ▼
       [ Secret Service – HashiCorp Vault ]
         • Zero Trust, principle of least privilege.
         • Dynamic, short-lived credentials for sources/destinations.
         • Full audit logging of secret access.
             │
             ▼
         Credentials supplied to MCP server.

             │   (Invoke MCP Server)
             ▼
       [ Connector Ecosystem ]
         ┌───────────────────────────────────────────────────────┐
         │ Connector Service (Hybrid Runtime)                    │
         │  • Executes:                                           │
         │    – Containerized Airbyte connectors (via K8s Pods).  │
         │    – Serverless function connectors (via Knative).     │
         │  • Streams data back to MCP server in Airbyte/Fivetran │
         │    protocol formats.                                   │
         ├───────────────────────────────────────────────────────┤
         │ MCP Server (per data source/destination)               │
         │  • Wraps specific API/DB with MCP primitives.          │
         │  • E.g., PostgreSQL MCP server, Salesforce MCP server. │
         ├───────────────────────────────────────────────────────┤
         │ Dynamic Connector Synthesizer (APIWeaver)              │
         │  • Generates MCP servers from OpenAPI specs on demand. │
         │  • Registers new connectors in Connector Registry.     │
         └───────────────────────────────────────────────────────┘

    5. External Data Sources Layer
       [ APIs | Databases | Filesystems ]
         • Examples: PostgreSQL, Salesforce, Snowflake, REST APIs.
         • Access mediated exclusively via MCP connectors.

    6. Support & Governance Services
       [ Connector Registry – PostgreSQL ]
         • Stores MCP server metadata (name, endpoint, capabilities).

       [ Metadata Store – PostgreSQL + lakeFS ]
         • Persists PipelinePlans, execution history, LangGraph state snapshots.
         • Tracks full data lineage and schema versions.
         • lakeFS integration for dataset versioning.

       [ Security & Governance ]
         • mTLS between all microservices (Istio/Linkerd).
         • Policy-as-Code for RBAC and connector access.
         • Audit trails for every action.
         • Optional approval gates for sensitive operations.
