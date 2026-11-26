"""Currency, account, ledger-event, allocation, and transfer models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, CreatedUpdatedAtMixin
from app.db.types import UUIDBinary

if TYPE_CHECKING:
    from app.db.models.identity import Household, Space, User
    from app.db.models.planning import (
        BudgetAllocation,
        BudgetPlan,
        CommitmentOccurrence,
        CommitmentPayment,
        CommitmentTemplate,
        FundReservation,
        Goal,
        GoalContribution,
        IncomeOccurrence,
        IncomeReceipt,
        IncomeSchedule,
        IncomeSource,
    )


class Currency(Base):
    """Currency reference metadata and accepted minor-unit precision."""

    __tablename__ = "currencies"
    __table_args__ = (CheckConstraint("minor_unit_digits <= 4", name="minor_unit_digits_lte_4"),)

    code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    minor_unit_digits: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))

    accounts: Mapped[list[Account]] = relationship(back_populates="currency")
    transactions: Mapped[list[FinancialTransaction]] = relationship(back_populates="currency")
    budget_plans: Mapped[list[BudgetPlan]] = relationship(back_populates="currency")
    income_schedules: Mapped[list[IncomeSchedule]] = relationship(back_populates="currency")
    income_occurrences: Mapped[list[IncomeOccurrence]] = relationship(back_populates="currency")
    commitment_templates: Mapped[list[CommitmentTemplate]] = relationship(back_populates="currency")
    commitment_occurrences: Mapped[list[CommitmentOccurrence]] = relationship(
        back_populates="currency"
    )
    goals: Mapped[list[Goal]] = relationship(back_populates="currency")
    goal_contributions: Mapped[list[GoalContribution]] = relationship(back_populates="currency")
    fund_reservations: Mapped[list[FundReservation]] = relationship(back_populates="currency")


class Account(CreatedUpdatedAtMixin, Base):
    """Owned money-holding account; never a reporting space."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL) <> (household_id IS NOT NULL)", name="one_owner_scope"
        ),
        CheckConstraint("type IN ('CASH','BANK','SAVINGS','OTHER')", name="type"),
        CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),
        UniqueConstraint("id", "currency_code"),
        Index("ix_accounts_owner_user_id_status", "owner_user_id", "status"),
        Index("ix_accounts_household_id_status", "household_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    household_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("households.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    include_in_safe_to_spend: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    owner_user: Mapped[User | None] = relationship(back_populates="personal_accounts")
    household: Mapped[Household | None] = relationship(back_populates="accounts")
    currency: Mapped[Currency] = relationship(back_populates="accounts")
    entries: Mapped[list[AccountEntry]] = relationship(
        back_populates="account", foreign_keys="AccountEntry.account_id"
    )
    fund_reservations: Mapped[list[FundReservation]] = relationship(back_populates="account")


class Category(CreatedAtMixin, Base):
    """Income or expense category in a user, household, or system scope."""

    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("kind IN ('INCOME','EXPENSE')", name="kind"),
        CheckConstraint(
            "(is_system_default = 1 AND owner_user_id IS NULL AND household_id IS NULL) OR "
            "(is_system_default = 0 AND "
            "((owner_user_id IS NOT NULL) <> (household_id IS NOT NULL)))",
            name="scope_shape",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    household_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("households.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    color_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_system_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    allocations: Mapped[list[TransactionAllocation]] = relationship(back_populates="category")
    budget_allocations: Mapped[list[BudgetAllocation]] = relationship(back_populates="category")
    income_sources: Mapped[list[IncomeSource]] = relationship(back_populates="default_category")
    commitment_templates: Mapped[list[CommitmentTemplate]] = relationship(back_populates="category")


class FinancialTransaction(CreatedUpdatedAtMixin, Base):
    """Immutable financial event header with auditable correction links."""

    __tablename__ = "financial_transactions"
    __table_args__ = (
        UniqueConstraint("id", "currency_code"),
        UniqueConstraint("replaces_transaction_id"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(
            "transaction_type IN ('INCOME','EXPENSE','TRANSFER','REFUND','OPENING_BALANCE',"
            "'ADJUSTMENT')",
            name="transaction_type",
        ),
        CheckConstraint("status IN ('DRAFT','POSTED','VOIDED')", name="status"),
        CheckConstraint("household_share_status IN ('PRIVATE','SHARED')", name="share_status"),
        CheckConstraint(
            "transaction_type = 'REFUND' OR original_transaction_id IS NULL",
            name="refund_link_type",
        ),
        CheckConstraint(
            "(status = 'VOIDED' AND voided_at IS NOT NULL) OR "
            "(status <> 'VOIDED' AND voided_at IS NULL)",
            name="voided_at_status",
        ),
        CheckConstraint(
            "replaces_transaction_id IS NULL OR status = 'POSTED'", name="replacement_posted"
        ),
        Index(
            "ix_financial_transactions_created_by_user_id_occurred_at_id",
            "created_by_user_id",
            "occurred_at",
            "id",
        ),
        Index(
            "ix_financial_transactions_status_transaction_type_occurred_at",
            "status",
            "transaction_type",
            "occurred_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    created_by_user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_transaction_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    replaces_transaction_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    household_share_status: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'PRIVATE'")
    )
    mixed_allocation_consent_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6), nullable=True
    )
    voided_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    currency: Mapped[Currency] = relationship(back_populates="transactions")
    creator: Mapped[User] = relationship(back_populates="created_transactions")
    entries: Mapped[list[AccountEntry]] = relationship(
        back_populates="transaction", foreign_keys="AccountEntry.transaction_id"
    )
    allocations: Mapped[list[TransactionAllocation]] = relationship(back_populates="transaction")
    transfer_details: Mapped[TransferDetails | None] = relationship(back_populates="transaction")
    income_receipt: Mapped[IncomeReceipt | None] = relationship(back_populates="transaction")
    commitment_payments: Mapped[list[CommitmentPayment]] = relationship(
        back_populates="transaction"
    )


class AccountEntry(CreatedAtMixin, Base):
    """Signed effect of one financial event on one account."""

    __tablename__ = "account_entries"
    __table_args__ = (
        UniqueConstraint("id", "transaction_id"),
        ForeignKeyConstraint(
            ["transaction_id", "currency_code"],
            ["financial_transactions.id", "financial_transactions.currency_code"],
            name="fk_account_entries_transaction_currency",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["account_id", "currency_code"],
            ["accounts.id", "accounts.currency_code"],
            name="fk_account_entries_account_currency",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("amount_signed <> 0", name="amount_nonzero"),
        CheckConstraint(
            "entry_role IN ('INCOME','EXPENSE','TRANSFER_SOURCE','TRANSFER_DESTINATION','REFUND',"
            "'OPENING_BALANCE','ADJUSTMENT')",
            name="entry_role",
        ),
        Index("ix_account_entries_account_id_created_at_id", "account_id", "created_at", "id"),
        Index("ix_account_entries_transaction_id", "transaction_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    transaction_id: Mapped[UUID] = mapped_column(UUIDBinary(), nullable=False)
    account_id: Mapped[UUID] = mapped_column(UUIDBinary(), nullable=False)
    amount_signed: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"), nullable=False
    )
    entry_role: Mapped[str] = mapped_column(String(24), nullable=False)

    transaction: Mapped[FinancialTransaction] = relationship(
        back_populates="entries", foreign_keys=[transaction_id]
    )
    account: Mapped[Account] = relationship(back_populates="entries", foreign_keys=[account_id])


class TransactionAllocation(CreatedAtMixin, Base):
    """Reporting attribution of a transaction amount to a space/category."""

    __tablename__ = "transaction_allocations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_transaction_allocations_space_id_transaction_id", "space_id", "transaction_id"),
        Index("ix_transaction_allocations_transaction_id", "transaction_id"),
        Index("ix_transaction_allocations_reverses_allocation_id", "reverses_allocation_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    transaction_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    space_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("spaces.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("categories.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    beneficiary_user_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4, asdecimal=True), nullable=False)
    reverses_allocation_id: Mapped[UUID | None] = mapped_column(
        UUIDBinary(),
        ForeignKey("transaction_allocations.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )

    transaction: Mapped[FinancialTransaction] = relationship(back_populates="allocations")
    space: Mapped[Space] = relationship(back_populates="allocations")
    category: Mapped[Category | None] = relationship(back_populates="allocations")


class TransferDetails(CreatedAtMixin, Base):
    """Same-currency transfer source/destination entry references."""

    __tablename__ = "transfer_details"
    __table_args__ = (
        UniqueConstraint("source_account_entry_id"),
        UniqueConstraint("destination_account_entry_id"),
        ForeignKeyConstraint(
            ["source_account_entry_id", "transaction_id"],
            ["account_entries.id", "account_entries.transaction_id"],
            name="fk_transfer_details_source_entry_owner",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["destination_account_entry_id", "transaction_id"],
            ["account_entries.id", "account_entries.transaction_id"],
            name="fk_transfer_details_destination_entry_owner",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint(
            "source_account_entry_id <> destination_account_entry_id", name="different_entries"
        ),
    )

    transaction_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    source_account_entry_id: Mapped[UUID] = mapped_column(UUIDBinary(), nullable=False)
    destination_account_entry_id: Mapped[UUID] = mapped_column(UUIDBinary(), nullable=False)

    transaction: Mapped[FinancialTransaction] = relationship(back_populates="transfer_details")
