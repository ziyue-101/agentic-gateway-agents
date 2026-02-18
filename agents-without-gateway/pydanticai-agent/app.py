import os
import asyncio
import streamlit as st
import nest_asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

# Patch Streamlit's event loop to allow nested asyncio calls
nest_asyncio.apply()

# --- Configuration ---
DEEPWIKI_HTTP_URL = "https://mcp.deepwiki.com/mcp"
MODEL_ID = "gemini-2.5-flash"

st.set_page_config(page_title="DeepWiki Agent (HTTP)", page_icon="⚡")
st.title("⚡ DeepWiki Agent (Streamable HTTP)")

# --- 1. Environment & Auth ---
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    with st.sidebar:
        st.warning("`GOOGLE_API_KEY` not found in environment.")
        api_key = st.text_input("Enter Google API Key", type="password")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

# --- 2. Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. Agent Logic ---
async def run_agent(user_input):
    """
    Connects to DeepWiki via Streamable HTTP, lists tools, and streams the response.
    """
    mcp_server = MCPServerStreamableHTTP(url=DEEPWIKI_HTTP_URL)

    provider = GoogleProvider(api_key=os.environ.get("GOOGLE_API_KEY"))
    model = GoogleModel(MODEL_ID, provider=provider)

    agent = Agent(
        model,
        system_prompt=(
            "You are a technical assistant with access to the DeepWiki documentation engine. "
            "Use the 'ask_question' tool to look up information about GitHub repositories. "
            "Always cite the source repository if applicable."
        )
    )

    async with mcp_server:
        
        try:
            mcp_response = await mcp_server.list_tools() 
            
            tools_list = getattr(mcp_response, 'tools', mcp_response)
            
            st.sidebar.markdown("### 🛠️ Available Tools")
            for tool in tools_list:
                tool_name = getattr(tool, 'name', 'Unknown')
                tool_desc = getattr(tool, 'description', 'No description')
                st.sidebar.markdown(f"- **`{tool_name}`**: {tool_desc}")
                
        except Exception as e:
            st.sidebar.warning(f"Could not fetch tools: {e}")

        async with agent.run_stream(user_input, toolsets=[mcp_server]) as result:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                async for chunk in result.stream_output():
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            
            return full_response

# --- 4. Main Interaction Loop ---
if prompt := st.chat_input("Ask about a GitHub repo (e.g., 'How do I use FastAPI?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Please set GOOGLE_API_KEY to continue.")
        st.stop()

    try:
        response_text = asyncio.run(run_agent(prompt))
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Error: {e}")