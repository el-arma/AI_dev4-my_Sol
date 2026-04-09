from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, BinaryContent

load_dotenv()


class ImageDeps(BaseModel):
    image_bytes: bytes
    media_type: str = "image/jpeg"

# Vision specialist
Agent_Jones = Agent(
    model="gateway/google-vertex:gemini-2.5-flash-image",
    name="Agent Jones, specialty: vision",
    instructions="You are a vision specialist. Analyse images in detail: objects, colours, spatial layout, visible text, and any relevant observations.",
)

# Orchestrator – delegates all vision tasks via the `vision` tool
main_agent = Agent(
    "gateway/openai:gpt-5.2",
    deps_type=ImageDeps,
    instructions="You are an orchestrator. Always use the `vision` tool for anything image-related. Never describe images yourself.",
)


@main_agent.tool
async def vision(ctx: RunContext[ImageDeps], prompt: str) -> str:
    """Forward image from deps to Agent Jones."""
    result = await Agent_Jones.run([
        BinaryContent(data=ctx.deps.image_bytes, media_type=ctx.deps.media_type),
        prompt,
    ])
    return result.output


if __name__ == "__main__":
    image_path = "my_Solutions/Data_Bank/dam_image.png"

    deps = ImageDeps(
        image_bytes=Path(image_path).read_bytes(),
        media_type="image/png",
    )

    result = main_agent.run_sync(
        "Locate the dam in the image and provide its grid position (column, row). Choose only one grid cell.",
        deps=deps,
    )

    print(result.output)