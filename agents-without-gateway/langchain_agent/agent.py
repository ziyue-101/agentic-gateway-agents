import streamlit as st
import logging
import os
import asyncio
import contextlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent 
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import HumanMessage, AIMessage


st.set_page_config(page_title="Gemini Agent", page_icon="🤖")
st.title("🤖 Gemini Agent")


# 1. Environment Variable Check
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set the GOOGLE_API_KEY environment variable.")
    st.stop()


# 2. Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Gemini Agent. How can I help?"}]
# 4. Display Chat Messages
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

# 5. Define the Async Agent Interaction
async def run_agent_interaction(user_input, chat_history):
    """
    Connects to MCP, creates agent, and processes the new message
    while preserving the context of previous messages.
    """
    mcp_config = {}

    mcp_config["deepwiki"] = {
        "url": "https://mcp.deepwiki.com/mcp",
            "transport": "http",
    }

    mcp_config["calculator"] = {
        "url": "http://server1-svc.mcp-server-calculator-system.svc.cluster.local:9000/mcp",
            "transport": "http",
    }

    client = MultiServerMCPClient(mcp_config)

    # Start MCP Sessions for all configured servers
    async with contextlib.AsyncExitStack() as stack:
        tools = []
        for name in mcp_config.keys():
            session = await stack.enter_async_context(client.session(name))
            tools.extend(await load_mcp_tools(session))
        
        # Create Agent
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
        agent = create_agent(model=llm, tools=tools)
        
        # Prepare the full message history (Context)
        # We append the new user input to the existing history
        messages = chat_history + [HumanMessage(content=user_input)]
        
        # Invoke Agent
        response = await agent.ainvoke({"messages": messages})
        
        # Return the final text response
        return response["messages"][-1].content


# 6. Handle User Input
if prompt := st.chat_input():
    # Display user message immediately
    with st.chat_message("user"):
        st.write(prompt)
    
    # Show a spinner while the agent works
    with st.spinner("Thinking..."):
        try:
            # Run the async agent loop
            # We pass the current state history so the agent has context
            response_text = asyncio.run(
                run_agent_interaction(prompt, st.session_state.messages)
            )
            
            # Display AI response
            with st.chat_message("assistant"):
                st.write(response_text)
            
            # Update Session State History
            st.session_state.messages.append(HumanMessage(content=prompt))
            st.session_state.messages.append(AIMessage(content=response_text))

        except Exception as e:
            st.error(f"An error occurred: {e}")
            # Attempt to display detailed error response if available
            if hasattr(e, "response") and hasattr(e.response, "text"):
                st.error(f"Server details: {e.response.text}")