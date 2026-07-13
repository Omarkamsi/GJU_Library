from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, func

from app.db import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)   # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
