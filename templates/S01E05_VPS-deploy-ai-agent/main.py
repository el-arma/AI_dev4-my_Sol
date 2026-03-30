from agents import create_agent
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from schemas import QueryToAgent, AgentResponse
import logfire
from middleware import logging_middleware


load_dotenv()

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

app = FastAPI()

# mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

app.middleware("http")(logging_middleware)


Agent_Laszlo = create_agent(name="Laszlo",
                            description="Helpful general purpose Agent")


@app.get("/")
def root():
    return FileResponse("static/index.html")

# @app.get("/")
# def root() -> dict:
#     return {"message": "Hello from VPS container! 🐳 "}

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

@app.get("/ai-dev4")
def ai_dev4():
    return FileResponse("static/ai-dev4/index.html")

@app.post("/api/v1/agent-ear", response_model=AgentResponse)
def ask_agent(body: QueryToAgent) -> AgentResponse:

    result = Agent_Laszlo.run_sync(body.msg)

    return AgentResponse(msg=result.output)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)