from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from communication_platform.shared.database import Base

class MessageDB(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(20), nullable=False)
    from_phone = Column(String(20), nullable=False)
    to_phone = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<MessageDB(message_id={self.message_id}, type={self.type}, from_phone={self.from_phone}, "
            f"to_phone={self.to_phone}, content={self.content}, timestamp={self.timestamp}, "
            f"customer_id={self.customer_id}, conversation_id={self.conversation_id}, created_at={self.created_at})>"
        ) 