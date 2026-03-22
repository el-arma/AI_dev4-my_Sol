from sqlalchemy import Column, Integer,  String
from db import Base


class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)      # user/agent
    message = Column(String)