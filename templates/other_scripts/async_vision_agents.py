import asyncio
from dotenv import load_dotenv
import logfire
from pathlib import Path
from pydantic_ai import Agent, BinaryContent


load_dotenv()

# ----------------------------------------------------------------------
# LOGFIRE SETUP
# ----------------------------------------------------------------------

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ----------------------------------------------------------------------

vision_agent = Agent(model="gateway/google-vertex:gemini-2.5-flash-image")

vision_prompt = "Describe what you can see."

async def analyze_image(img_path: Path) -> tuple[str, str]:
    
    """
    Sends a single image to the model.
    """

    image_bytes = img_path.read_bytes()

    # agent.run() is the native async version of run_sync().
    # Under the hood, run_sync() is literally just asyncio.run(agent.run(...))
    
    result = await vision_agent.run(
        [
            vision_prompt,
            # BinaryContent wraps raw bytes + MIME type so pydantic-ai knows how to encode the payload
            BinaryContent(data=image_bytes, media_type='image/png'),
        ]
    )

    # Return a tuple of (filename, model response)
    return img_path.name, result.output


async def main():
    """
    asyncio.gather() schedules ALL coroutines concurrently on the same event loop.
    Instead of: request1 → wait → request2 → wait → ... (sequential, slow)
    We get: request1, request2, ..., request9 all in-flight simultaneously,
    so total time is ~ slowest single request, not the sum of all 9.
    
    The * unpacks the list into individual arguments:
    asyncio.gather(analyze_image(p1), analyze_image(p2), ..., analyze_image(p9))
    """

    # Collect all *.png files in the target directory
    img_dir = Path('OTHER_SCRIPTS-TESTs')

    # sorted for deterministic order
    img_paths = sorted(img_dir.glob('*.png'))

    results = await asyncio.gather(
        *[analyze_image(p) for p in img_paths]
        # The * unpacks the list into individual arguments: asyncio.gather(analyze_image(p1)..., )
    )

    # results: list of tuples in the same order as img_paths (IMPORTANT!)
    # regardless of which API call finished first — gather preserves order
    for name, output in results:
        print(f'[{name}]\n{output}\n')

# This is the standard entry point for any async Python program.
asyncio.run(main())