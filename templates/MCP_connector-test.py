
# FastMCP + Docker (mcp/filesystem)

# Requirements (prerequsit):
#   uv add fastmcp
#   docker pull mcp/filesystem:latest

# Docker flags:
#   -i        keeps stdin open (required for MCP communication)
#   --rm      removes container after exit
#   -v src:dst mounts local directory into container
#   /workspace argument for MCP server — its root filesystem

# Windows paths: use forward slashes (C:/Users/...) or raw string (r"C:\Users\...")
# Async: FastMCP Client supports ONLY async with — regular with won't work
# Container: no need to start it manually, spins up and removes itself automatically


import asyncio
from fastmcp import Client

config = {
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

async def main():
    async with Client(config) as client:
        tools = await client.list_tools()
        print("Narzędzia:", [t.name for t in tools])
        
        result = await client.call_tool("list_directory", {"path": "/workspace"})
        print(result)

asyncio.run(main())


    