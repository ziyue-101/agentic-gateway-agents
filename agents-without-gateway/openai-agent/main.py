import os
import asyncio
import json
from contextlib import AsyncExitStack
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPWIKI_URL = "https://mcp.deepwiki.com/mcp"
CALCULATOR_URL = "http://server1-svc.mcp-server-calculator-system.svc.cluster.local:9000/mcp"

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set.")

# --- Setup Gemini Client ---
# We use the standard client, which gives us full control over 'tools' definitions
client = AsyncOpenAI(
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
MODEL_NAME = "gemini-2.0-flash" 

async def get_user_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)

async def main():
    async with AsyncExitStack() as stack:
        print("🔌 Connecting to MCP Servers...")
        
 # List of servers to connect to
        servers = [
            ("DeepWiki", DEEPWIKI_URL),
            ("Calculator", CALCULATOR_URL)
        ]

        # We need to map tool names to their specific session
        # so we know which server to call when the LLM asks for a tool.
        tool_to_session_map = {} 
        openai_tools = []

        for name, url in servers:
            try:
                # 1. Connect Transport
                print(f"   Attempting connection to {name} at {url}...")
                read_stream, write_stream, _ = await stack.enter_async_context(
                    streamable_http_client(url)
                )
                
                # 2. Initialize Session
                session = await stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()
                
                # 3. List Tools
                list_result = await session.list_tools()
                tool_names = [t.name for t in list_result.tools]
                print(f"   ✅ Connected to {name}. Tools: {tool_names}")

                # 4. Register Tools & Map to Session
                for tool in list_result.tools:
                    # Store the mapping: "add" -> <Calculator Session Object>
                    tool_to_session_map[tool.name] = session
                    
                    # Convert MCP Schema to OpenAI Schema
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema 
                        }
                    })

            except Exception as e:
                print(f"   ❌ Failed to connect to {name}: {e}")
                continue

        if not openai_tools:
            print("❌ No tools available. Exiting.")
            return

        print(f"\n🤖 Agent Ready with {len(openai_tools)} tools. Type 'quit' to exit.")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use the calculator for math and DeepWiki for information."}
        ]

      # --- Interactive Loop ---
        while True:
            try:
                user_text = await get_user_input("User: ")
                if user_text.lower() in ["quit", "exit"]:
                    break
                
                messages.append({"role": "user", "content": user_text})

                # -- 1. Model Decision --
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto" 
                )
                
                response_msg = response.choices[0].message
                messages.append(response_msg) 

                # -- 2. Tool Execution --
                if response_msg.tool_calls:
                    print(f"   (🛠️  Calling tools: {[t.function.name for t in response_msg.tool_calls]})")
                    
                    for tool_call in response_msg.tool_calls:
                        fname = tool_call.function.name
                        fargs = json.loads(tool_call.function.arguments)
                        
                        # Find the correct session for this tool
                        target_session = tool_to_session_map.get(fname)
                        
                        if target_session:
                            try:
                                # Execute against the specific server
                                mcp_result = await target_session.call_tool(fname, arguments=fargs)
                                result_text = mcp_result.content[0].text
                            except Exception as e:
                                result_text = f"Error executing tool {fname}: {str(e)}"
                        else:
                            result_text = f"Error: Tool {fname} not found in active sessions."

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result_text)
                        })
                    
                    # -- 3. Final Response --
                    final_response = await client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                    )
                    final_text = final_response.choices[0].message.content
                    print(f"Agent: {final_text}")
                    messages.append({"role": "assistant", "content": final_text})
                
                else:
                    print(f"Agent: {response_msg.content}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())