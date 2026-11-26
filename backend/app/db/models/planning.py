"""Forecast, budgeting, commitment, goal, idempotency, and audit models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import CHAR, DATE, DATETIME, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, CreatedUpdatedAtMixin
from app.db.types import UUIDBinary

if TYPE_CHECKING:
    from app.db.models.identity import Space, User
    from app.db.models.ledger import Account, Category, Currency, FinancialTransaction


class IncomeSource(CreatedUpdatedAtMixin, Base):
    """Named income origin; source_type remains descriptive only."""

    __tablename__ = "income_sources"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),)

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    default_category_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("categories.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    schedules: Mapped[list[IncomeSchedule]] = relationship(back_populates="source")
    occurrences: Mapped[list[IncomeOccurrence]] = relationship(back_populates="source")
    owner_user: Mapped[User] = relationship(back_populates="income_sources")
    default_category: Mapped[Category | None] = relationship(back_populates="income_sources")


class IncomeSchedule(CreatedUpdatedAtMixin, Base):
    """Recurring or irregular expected-income profile."""

    __tablename__ = "income_schedules"
    __table_args__ = (
        CheckConstraint("expected_amount > 0", name="expected_amount_positive"),
        CheckConstraint(
            "frequency_type IN ('WEEKLY','BIWEEKLY','MONTHLY','CUSTOM','IRREGULAR')",
            name="frequency",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="confidence_range"
        ),
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    income_source_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("income_sources.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    frequency_type: Mapped[str] = mapped_column(String(12), nullable=False)
    recurrence_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expected_next_date: Mapped[date | None] = mapped_column(DATE(), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4, asdecimal=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    source: Mapped[IncomeSource] = relationship(back_populates="schedules")
    occurrences: Mapped[list[IncomeOccurrence]] = relationship(back_populates="schedule")
    space: Mapped[Space] = relationship(back_populates="income_schedules")
    currency: Mapped[Currency] = relationship(back_populates="income_schedules")


class IncomeOccurrence(CreatedUpdatedAtMixin, Base):
    """One expected receipt, optionally produced by a schedule."""

    __tablename__ = "income_occurrences"
    __table_args__ = (
        CheckConstraint("expected_amount > 0", name="expected_amount_positive"),
        CheckConstraint(
            "status IN ('EXPECTED','PARTIALLY_RECEIVED','RECEIVED','SKIPPED','CANCELLED')",
            name="status",
        ),
        Index(
            "ix_income_occurrences_space_id_expected_date_status",
            "space_id",
            "expected_date",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    income_schedule_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("income_schedules.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    income_source_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("income_sources.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    expected_date: Mapped[date] = mapped_column(DATE(), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)

    schedule: Mapped[IncomeSchedule | None] = relationship(back_populates="occurrences")
    source: Mapped[IncomeSource] = relationship(back_populates="occurrences")
    receipts: Mapped[list[IncomeReceipt]] = relationship(back_populates="occurrence")
    space: Mapped[Space] = relationship(back_populates="income_occurrences")
    currency: Mapped[Currency] = relationship(back_populates="income_occurrences")


class IncomeReceipt(CreatedAtMixin, Base):
    """One actual income transaction applied to an expected occurrence."""

    __tablename__ = "income_receipts"
    __table_args__ = (
        CheckConstraint("received_amount > 0", name="received_amount_positive"),
        Index(
            "ix_income_receipts_income_occurrence_id_received_at",
            "income_occurrence_id",
            "received_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    income_occurrence_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("income_occurrences.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    transaction_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        unique=True,
    )
    received_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)

    occurrence: Mapped[IncomeOccurrence] = relationship(back_populates="receipts")
    transaction: Mapped[FinancialTransaction] = relationship(back_populates="income_receipt")


class BudgetPlan(CreatedUpdatedAtMixin, Base):
    """Named plan for one reporting space and currency."""

    __tablename__ = "budget_plans"
    __table_args__ = (
        CheckConstraint("period_type IN ('WEEKLY','MONTHLY','CUSTOM')", name="period_type"),
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    period_type: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    periods: Mapped[list[BudgetPeriod]] = relationship(back_populates="plan")
    space: Mapped[Space] = relationship(back_populates="budget_plans")
    currency: Mapped[Currency] = relationship(back_populates="budget_plans")


class BudgetPeriod(CreatedAtMixin, Base):
    """Space-timezone snapshot for one half-open budget date range."""

    __tablename__ = "budget_periods"
    __table_args__ = (
        UniqueConstraint("budget_plan_id", "period_start", "period_end"),
        CheckConstraint("period_start < period_end", name="date_range"),
        CheckConstraint("status IN ('OPEN','CLOSED')", name="status"),
        Index("ix_budget_periods_period_start_period_end", "period_start", "period_end"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    budget_plan_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("budget_plans.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(DATE(), nullable=False)
    period_end: Mapped[date] = mapped_column(DATE(), nullable=False)
    timezone_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    plan: Mapped[BudgetPlan] = relationship(back_populates="periods")
    allocations: Mapped[list[BudgetAllocation]] = relationship(back_populates="period")


class BudgetAllocation(Base):
    """Planned category amount or the single flexible pool for a period."""

    __tablename__ = "budget_allocations"
    __table_args__ = (
        UniqueConstraint("budget_period_id", "category_unique_key"),
        CheckConstraint("planned_amount >= 0", name="planned_amount_nonnegative"),
        CheckConstraint(
            "category_id IS NULL OR category_id <> X'00000000000000000000000000000000'",
            name="category_id_not_zero_uuid",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    budget_period_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("budget_periods.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("categories.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    category_unique_key: Mapped[bytes] = mapped_column(
        UUIDBinary(),
        Computed("COALESCE(category_id, X'00000000000000000000000000000000')", persisted=True),
        nullable=False,
    )

    period: Mapped[BudgetPeriod] = relationship(back_populates="allocations")
    category: Mapped[Category | None] = relationship(back_populates="budget_allocations")


class CommitmentTemplate(CreatedUpdatedAtMixin, Base):
    """Reusable forecast template for a recurring or one-off obligation."""

    __tablename__ = "commitment_templates"
    __table_args__ = (
        CheckConstraint("expected_amount > 0", name="expected_amount_positive"),
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("categories.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    recurrence_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    occurrences: Mapped[list[CommitmentOccurrence]] = relationship(back_populates="template")
    space: Mapped[Space] = relationship(back_populates="commitment_templates")
    currency: Mapped[Currency] = relationship(back_populates="commitment_templates")
    category: Mapped[Category | None] = relationship(back_populates="commitment_templates")


class CommitmentOccurrence(CreatedUpdatedAtMixin, Base):
    """Dated expected obligation with partial payment application."""

    __tablename__ = "commitment_occurrences"
    __table_args__ = (
        CheckConstraint("expected_amount > 0", name="expected_amount_positive"),
        CheckConstraint(
            "status IN ('UPCOMING','PARTIALLY_PAID','PAID','SKIPPED','CANCELLED')", name="status"
        ),
        Index(
            "ix_commitment_occurrences_space_id_due_date_status", "space_id", "due_date", "status"
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    commitment_template_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("commitment_templates.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(DATE(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    template: Mapped[CommitmentTemplate | None] = relationship(back_populates="occurrences")
    payments: Mapped[list[CommitmentPayment]] = relationship(back_populates="occurrence")
    space: Mapped[Space] = relationship(back_populates="commitment_occurrences")
    currency: Mapped[Currency] = relationship(back_populates="commitment_occurrences")


class CommitmentPayment(CreatedAtMixin, Base):
    """Applied amount from a posted expense transaction to an occurrence."""

    __tablename__ = "commitment_payments"
    __table_args__ = (
        UniqueConstraint("commitment_occurrence_id", "transaction_id"),
        CheckConstraint("applied_amount > 0", name="applied_amount_positive"),
        Index("ix_commitment_payments_transaction_id", "transaction_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    commitment_occurrence_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("commitment_occurrences.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    transaction_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    applied_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)

    occurrence: Mapped[CommitmentOccurrence] = relationship(back_populates="payments")
    transaction: Mapped[FinancialTransaction] = relationship(back_populates="commitment_payments")


class Goal(CreatedUpdatedAtMixin, Base):
    """Savings target scoped to one reporting space and currency."""

    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="target_amount_positive"),
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    target_date: Mapped[date | None] = mapped_column(DATE(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    contributions: Mapped[list[GoalContribution]] = relationship(back_populates="goal")
    space: Mapped[Space] = relationship(back_populates="goals")
    currency: Mapped[Currency] = relationship(back_populates="goals")


class GoalContribution(Base):
    """Goal progress represented as a reservation earmark, not a ledger entry."""

    __tablename__ = "goal_contributions"
    __table_args__ = (
        UniqueConstraint("fund_reservation_id"),
        CheckConstraint("contribution_type = 'EARMARK'", name="earmark_only"),
        CheckConstraint("amount > 0", name="amount_positive"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("goals.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    contribution_type: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'EARMARK'")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    fund_reservation_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("fund_reservations.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    contributed_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    goal: Mapped[Goal] = relationship(back_populates="contributions")
    reservation: Mapped[FundReservation] = relationship(back_populates="goal_contribution")
    currency: Mapped[Currency] = relationship(back_populates="goal_contributions")


class FundReservation(CreatedAtMixin, Base):
    """Funds earmarked from an account without creating a ledger entry."""

    __tablename__ = "fund_reservations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("reservation_type IN ('MANUAL','GOAL')", name="reservation_type"),
        CheckConstraint("status IN ('ACTIVE','RELEASED')", name="status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("accounts.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    space_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    reservation_type: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'ACTIVE'"))
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    account: Mapped[Account] = relationship(back_populates="fund_reservations")
    space: Mapped[Space | None] = relationship(back_populates="fund_reservations")
    currency: Mapped[Currency] = relationship(back_populates="fund_reservations")
    goal_contribution: Mapped[GoalContribution | None] = relationship(back_populates="reservation")


class IdempotencyRecord(CreatedAtMixin, Base):
    """Request replay record scoped to a user and operation."""

    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("user_id", "operation_scope", "idempotency_key"),
        Index("ix_idempotency_records_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    operation_scope: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(
        CHAR(64, charset="ascii", collation="ascii_bin"), nullable=False
    )
    response_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)

    user: Mapped[User] = relationship(back_populates="idempotency_records")


class AuditEvent(Base):
    """Allowlisted security and financial audit event metadata."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index(
            "ix_audit_events_resource_type_resource_id_occurred_at",
            "resource_type",
            "resource_id",
            "occurred_at",
        ),
        Index("ix_audit_events_actor_user_id_occurred_at", "actor_user_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(UUIDBinary(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    metadata_value: Mapped[dict[str, object]] = mapped_column("metadata", JSON, nullable=False)

    actor_user: Mapped[User | None] = relationship(back_populates="audit_events")
