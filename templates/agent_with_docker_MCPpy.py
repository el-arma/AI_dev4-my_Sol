import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset


load_dotenv()

mcp_config = {
    "mcpServers": {
        "filesystem": {
            "transport": "stdio",
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-v", "C:/Users/JohnDoe/Desktop/dedicated_folder:/workspace",
                "mcp/filesystem:latest",
                "/workspace"
            ]
        }
    }
}

toolset = FastMCPToolset(mcp_config)
agent = Agent("gateway/openai:gpt-5.2", toolsets=[toolset])

async def main():
    async with agent:
        result = await agent.run("Use provided tools. Create simple my_AI_ryhme.txt with sample of AI poem")
        print(result.output)

asyncio.run(main())