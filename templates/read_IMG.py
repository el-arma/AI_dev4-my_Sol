from pydantic_ai import Agent, ImageUrl

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync(
    [
        'What can you see, what is the name of the place?',
        ImageUrl(url='https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg'),
    ]
)
print(result.output)
