from agents import create_agent
from db import SessionLocal, engine, Base
from fastapi import FastAPI, Depends
from logger import logging_middleware
from models import ConversationHistory
from schemas import QueryToAgent, AgentResponse
from sqlalchemy.orm import Session
from sqlalchemy import Select
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
from utlis import find_my_flag

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# register logger
app.middleware("http")(logging_middleware)

Agent_Thompson = create_agent()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# helper: DB - message_history
def build_message_history(db_messages):

    history = []

    for msg in db_messages:
        if msg.role == "user":
            history.append(
                ModelRequest(
                    parts=[UserPromptPart(content=msg.message)]
                )
            )
        elif msg.role == "agent":
            history.append(
                ModelResponse(
                    parts=[TextPart(content=msg.message)]
                )
            )

    return history

@app.get("/")
def root() -> dict:
    return {"message": "Hello from GCP container! 🐳 "}

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

# # NOT SAFE, FOR DEV PURPOSES ONLY
# @app.get("/debug/db")
# def debug_db(db: Session = Depends(get_db)):
#     data = db.scalars(Select(ConversationHistory)).all()

#     return {
#         "rows": [row.__dict__ for row in data]
#     }

@app.get("/check-flag")
def debug_db(db: Session = Depends(get_db)):
    rows = db.scalars(Select(ConversationHistory)).all()

    flag = None

    for row in rows:
        flag = find_my_flag(row.message)
        if flag:
            break

    if not flag:
        flag = "FLAG NOT FOUND!"

    return flag

@app.post("/api/v1/friendly-ear", response_model=AgentResponse)
def ask_agent(request: QueryToAgent, db: Session = Depends(get_db)) -> AgentResponse:

    # 1. get history session:
    rows = db.scalars(
        Select(ConversationHistory)
        .where(ConversationHistory.session_id == request.sessionID)
        .order_by(ConversationHistory.id)
        ).all()

    # history limit (last 20 positions):
    rows = rows[-20:]

    message_history = build_message_history(rows)

    # 2. Ask agent with history provided
    result = Agent_Thompson.run_sync(
        request.msg,
        message_history=message_history
    )

    reply_text = result.output

    # 3. Save to DB
    db.add(ConversationHistory(
        session_id=request.sessionID,
        role="user",
        message=request.msg
    ))

    db.add(ConversationHistory(
        session_id=request.sessionID,
        role="agent",
        message=reply_text
    ))

    db.commit()

    return AgentResponse(msg=reply_text)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)