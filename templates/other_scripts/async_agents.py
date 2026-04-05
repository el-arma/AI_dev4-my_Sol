import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent


load_dotenv()

Agent_Thompson = Agent(
    model='gateway/google-vertex:gemini-2.5-flash',
    )

async def main():

    prompts = [
        "Say: Hello Jimmy!",
        "Say: Hello Johny!",
        # add more here
    ]

    tasks = [
        Agent_Thompson.run(prompt)
        for prompt in prompts
    ]

    results = await asyncio.gather(*tasks)

    for idx, res in enumerate(results):
        print(f"Agent {idx + 1} says; ", res.output)

if __name__ == "__main__":
    asyncio.run(main())
