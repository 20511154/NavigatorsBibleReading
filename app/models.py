from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    timezone = Column(String, default="Asia/Singapore")
    current_month = Column(Integer, default=1)
    current_day = Column(Integer, default=1)
    last_daily_sent = Column(Date, nullable=True)
    last_nudge_sent = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    progress = relationship("UserProgress", back_populates="user")
    events = relationship("UserEvent", back_populates="user")


class Plan(Base):
    __tablename__ = "plan"
    
    id = Column(Integer, primary_key=True, index=True)
    Month = Column("Month", Integer, nullable=False)  # Quoted column name
    Day = Column("Day", Integer, nullable=False)      # Quoted column name
    NT1_Book = Column("NT1_Book", String, nullable=False)
    NT1_Reading = Column("NT1_Reading", String, nullable=False)
    NT2_Book = Column("NT2_Book", String, nullable=False)
    NT2_Reading = Column("NT2_Reading", String, nullable=False)
    OT1_Book = Column("OT1_Book", String, nullable=False)
    OT1_Reading = Column("OT1_Reading", String, nullable=False)
    OT2_Book = Column("OT2_Book", String, nullable=False)
    OT2_Reading = Column("OT2_Reading", String, nullable=False)
    
    # Composite unique constraint on Month + Day
    __table_args__ = (
        {"extend_existing": True}
    )


class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress")


class UserEvent(Base):
    __tablename__ = "user_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # 'read', 'break', 'nudge'
    plan_month = Column(Integer, nullable=True)
    plan_day = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="events")


class ProcessedCallback(Base):
    __tablename__ = "processed_callbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    callback_id = Column(String, unique=True, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())