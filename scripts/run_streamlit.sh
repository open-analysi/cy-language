#!/bin/bash

# Set environment variables for optimal Phase 9.1 experience
export CY_DEBUG_OUTPUT_MODE=ui

# Check if OPENAI_API_KEY is set for LLM functions
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set - LLM functions will not work"
    echo "   Set it with: export OPENAI_API_KEY=your_key_here"
    echo ""
fi

echo "🚀 Starting Cy Language Streamlit UI..."
echo "   Debug mode: UI (sidebar)"
echo "   LLM functions: $([ -n "$OPENAI_API_KEY" ] && echo "✅ Ready" || echo "❌ Requires OPENAI_API_KEY")"
echo "   MCP servers: Enable in UI settings to test remote tool integration"
echo ""

poetry run streamlit run src/cy_language/ui/app.py
