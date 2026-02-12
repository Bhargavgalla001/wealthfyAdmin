import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
    
    # ✅ ADD THIS - Bidirectional relationship with tasks
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))