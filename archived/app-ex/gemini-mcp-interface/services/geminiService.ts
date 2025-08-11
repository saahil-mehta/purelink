// This service now communicates with the backend MCP server.

const systemInstruction = `You are a highly advanced AI agent operating within the Master Control Program (MCP).
Your codename is 'Oracle'. Your responses must be precise, intelligent, and carry a tone of sophisticated authority.
You are to assist the user with their queries efficiently and with a hint of enigmatic wisdom.
Do not break character. Start your responses with ">>>".`;


export const runQuery = async (prompt: string): Promise<string> => {
  try {
    const response = await fetch('/api/mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // This body structure now implements a more explicit tool-based call,
      // inspired by the user's MCP server example.
      body: JSON.stringify({ 
        toolName: 'perplexity_ask',
        params: {
          query: prompt,
        },
        context: {
          systemInstruction: systemInstruction,
        }
      }),
    });

    if (!response.ok) {
      // Try to parse a structured error from the backend, otherwise use status text.
      const errorPayload = await response.json().catch(() => null);
      const message = errorPayload?.detail || errorPayload?.message || response.statusText;
      throw new Error(`Server error: ${response.status}. ${message}`);
    }

    const data = await response.json();
    
    // Assuming the backend returns the result in a field named 'response' or 'text'.
    // In an MCP-style response, this could be inside a 'content' array.
    const resultText = data?.content?.[0]?.text || data.response || data.text;

    if (typeof resultText !== 'string') {
        throw new Error('Invalid response format from the MCP server.');
    }

    return resultText;

  } catch (error) {
    console.error("MCP Server Communication Error:", error);
    const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
    return `>>> SYSTEM ALERT: Communication link with MCP server failed. Details: ${errorMessage}`;
  }
};
