from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ...shared.database import Base
from ..twilio-monitor.database import MessageDB

# Association table for many-to-many relationship
ConversationMessageDB = Table(
    'conversation_message',
    Base.metadata,
    Column('conversation_id', UUID(as_uuid=True), ForeignKey('conversations.conversation_id'), primary_key=True),
    Column('message_id', UUID(as_uuid=True), ForeignKey('messages.message_id'), primary_key=True)
)

class ConversationDB(Base):
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    messages = relationship(
        "MessageDB",
        secondary=ConversationMessageDB,
        backref="conversations",
        lazy="dynamic"
    )

    def add_message(self, message):
        if not self.messages.filter(MessageDB.message_id == message.message_id).count():
            self.messages.append(message)

    def remove_message(self, message):
        if self.messages.filter(MessageDB.message_id == message.message_id).count():
            self.messages.remove(message)

    def get_messages(self):
        return self.messages.all() 