import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, DateTime, Date, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    searches = relationship("Search", back_populates="user", cascade="all, delete-orphan")
    saved_words = relationship("SavedWord", back_populates="user", cascade="all, delete-orphan")


class Search(Base):
    __tablename__ = "searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    input_text = Column(Text, nullable=False)
    tone = Column(String(50), nullable=True, default="neutral")
    intent = Column(String(100), nullable=True, default="general expression")
    analysis_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="searches")
    word_result = relationship("WordResult", back_populates="search", uselist=False, cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="search", cascade="all, delete-orphan")


class WordResult(Base):
    __tablename__ = "word_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id"), nullable=False)
    best_fit_word = Column(String(100), nullable=False)
    alternatives_json = Column(JSONB, nullable=True)
    explanations_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    search = relationship("Search", back_populates="word_result")


class SavedWord(Base):
    __tablename__ = "saved_words"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    word = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_words")


class WordOfTheDay(Base):
    __tablename__ = "word_of_the_day"

    date = Column(Date, primary_key=True, default=date.today)
    word = Column(String(100), nullable=False)
    data_json = Column(JSONB, nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id"), nullable=True)
    word = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    search = relationship("Search", back_populates="feedbacks")
