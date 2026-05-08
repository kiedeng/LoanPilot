from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Demo User")
    segment: Mapped[str] = mapped_column(String(60), default="personal")
    phone_masked: Mapped[str] = mapped_column(String(40), default="138****0000")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    occupation: Mapped[str] = mapped_column(String(120), default="")
    monthly_income: Mapped[float] = mapped_column(Float, default=0)
    monthly_revenue: Mapped[float] = mapped_column(Float, default=0)
    liabilities: Mapped[float] = mapped_column(Float, default=0)
    assets_under_management: Mapped[float] = mapped_column(Float, default=0)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200), default="LoanPilot Demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    segment: Mapped[str] = mapped_column(String(60))
    max_amount: Mapped[float] = mapped_column(Float)
    rate_range: Mapped[str] = mapped_column(String(60))
    term_range: Mapped[str] = mapped_column(String(60))
    disbursement: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Float)
    purpose: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(60), default="under_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoanDocument(Base):
    __tablename__ = "loan_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("loan_applications.id"))
    document_type: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(60), default="recognized")
    file_name: Mapped[str] = mapped_column(String(240), default="")


class LoanAccount(Base):
    __tablename__ = "loan_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_name: Mapped[str] = mapped_column(String(120))
    principal: Mapped[float] = mapped_column(Float)
    outstanding_balance: Mapped[float] = mapped_column(Float)
    next_due_amount: Mapped[float] = mapped_column(Float)
    next_due_date: Mapped[str] = mapped_column(String(20))


class RepaymentPlan(Base):
    __tablename__ = "repayment_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_account_id: Mapped[str] = mapped_column(ForeignKey("loan_accounts.id"))
    period: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float)
    principal: Mapped[float] = mapped_column(Float)
    interest: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40), default="pending")


class WorkflowState(Base):
    __tablename__ = "workflow_states"

    conversation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(80), default="idle")
    intent: Mapped[str] = mapped_column(String(80), default="unknown")
    context_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResponseCard(Base):
    __tablename__ = "response_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    surface_id: Mapped[str] = mapped_column(String(120))
    card_type: Mapped[str] = mapped_column(String(80), default="a2ui")
    card_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AiToolCallLog(Base):
    __tablename__ = "ai_tool_call_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    dify_conversation_id: Mapped[str] = mapped_column(String(120), default="")
    tool_name: Mapped[str] = mapped_column(String(120))
    arguments_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AiAction(Base):
    __tablename__ = "ai_actions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    action_type: Mapped[str] = mapped_column(String(120))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(120))
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
