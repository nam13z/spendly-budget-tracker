"""Identity, household, preference, and space persistence models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, INTEGER, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, CreatedUpdatedAtMixin
from app.db.types import UUIDBinary

if TYPE_CHECKING:
    from app.db.models.ledger import Account, FinancialTransaction, TransactionAllocation
    from app.db.models.planning import (
        AuditEvent,
        BudgetPlan,
        CommitmentOccurrence,
        CommitmentTemplate,
        FundReservation,
        Goal,
        IdempotencyRecord,
        IncomeOccurrence,
        IncomeSchedule,
        IncomeSource,
    )


class User(CreatedUpdatedAtMixin, Base):
    """Registered Spendly principal."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),)

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_currency_code: Mapped[str] = mapped_column(
        CHAR(3, charset="ascii", collation="ascii_bin"),
        ForeignKey("currencies.code", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    sessions: Mapped[list[Session]] = relationship(back_populates="user")
    preferences: Mapped[UserPreference | None] = relationship(back_populates="user")
    memberships: Mapped[list[HouseholdMembership]] = relationship(back_populates="user")
    personal_spaces: Mapped[list[Space]] = relationship(back_populates="owner_user")
    personal_accounts: Mapped[list[Account]] = relationship(back_populates="owner_user")
    created_households: Mapped[list[Household]] = relationship(
        back_populates="creator", foreign_keys="Household.created_by_user_id"
    )
    created_invitations: Mapped[list[HouseholdInvitation]] = relationship(
        back_populates="creator", foreign_keys="HouseholdInvitation.created_by_user_id"
    )
    created_transactions: Mapped[list[FinancialTransaction]] = relationship(
        back_populates="creator", foreign_keys="FinancialTransaction.created_by_user_id"
    )
    income_sources: Mapped[list[IncomeSource]] = relationship(
        back_populates="owner_user", foreign_keys="IncomeSource.owner_user_id"
    )
    idempotency_records: Mapped[list[IdempotencyRecord]] = relationship(back_populates="user")
    audit_events: Mapped[list[AuditEvent]] = relationship(back_populates="actor_user")


class Session(CreatedAtMixin, Base):
    """Opaque server-managed session token record."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_id_expires_at_revoked_at", "user_id", "expires_at", "revoked_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        CHAR(64, charset="ascii", collation="ascii_bin"), nullable=False, unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    device_label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class UserPreference(Base):
    """User interface preferences, kept separate from financial source data."""

    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    theme_key: Mapped[str] = mapped_column(String(32), nullable=False)
    accent_palette: Mapped[str] = mapped_column(String(32), nullable=False)
    communication_style: Mapped[str] = mapped_column(String(32), nullable=False)
    motion_level: Mapped[str] = mapped_column(String(32), nullable=False)
    sound_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    reduced_motion: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notification_preferences: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )

    user: Mapped[User] = relationship(back_populates="preferences")


class Household(CreatedUpdatedAtMixin, Base):
    """Shared collaboration boundary and ownership scope."""

    __tablename__ = "households"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','ARCHIVED')", name="status"),)

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    memberships: Mapped[list[HouseholdMembership]] = relationship(back_populates="household")
    invitations: Mapped[list[HouseholdInvitation]] = relationship(back_populates="household")
    spaces: Mapped[list[Space]] = relationship(back_populates="household")
    accounts: Mapped[list[Account]] = relationship(back_populates="household")
    creator: Mapped[User] = relationship(back_populates="created_households")


class HouseholdMembership(CreatedAtMixin, Base):
    """Current or historical role membership within a household."""

    __tablename__ = "household_memberships"
    __table_args__ = (
        UniqueConstraint("household_id", "user_id"),
        CheckConstraint("role IN ('OWNER','MEMBER')", name="role"),
        CheckConstraint("status IN ('INVITED','ACTIVE','LEFT','REMOVED')", name="status"),
        Index("ix_household_memberships_user_id_status", "user_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("households.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    household: Mapped[Household] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class HouseholdInvitation(CreatedAtMixin, Base):
    """Hashed, revocable, expiring invitation credential; grants MEMBER only."""

    __tablename__ = "household_invitations"
    __table_args__ = (
        CheckConstraint("max_uses > 0", name="max_uses_positive"),
        CheckConstraint("uses_count <= max_uses", name="uses_count_lte_max"),
        CheckConstraint("role_to_grant = 'MEMBER'", name="role_member_only"),
        Index(
            "ix_household_invitations_household_id_expires_at_revoked_at",
            "household_id",
            "expires_at",
            "revoked_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDBinary(), primary_key=True, default=uuid4)
    household_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("households.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        UUIDBinary(),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        CHAR(64, charset="ascii", collation="ascii_bin"), nullable=False, unique=True
    )
    role_to_grant: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'MEMBER'")
    )
    expires_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    max_uses: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    uses_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("0")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    household: Mapped[Household] = relationship(back_populates="invitations")
    creator: Mapped[User] = relationship(back_populates="created_invitations")


class Space(CreatedUpdatedAtMixin, Base):
    """Reporting/planning context owned by exactly one user or household."""

    __tablename__ = "spaces"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL) <> (household_id IS NOT NULL)", name="one_owner_scope"
        ),
        CheckConstraint("type IN ('PERSONAL','HOME','CUSTOM')", name="type"),
        CheckConstraint(
            "(owner_user_id IS NOT NULL AND visibility_policy = 'PRIVATE') OR "
            "(household_id IS NOT NULL AND visibility_policy = 'ACTIVE_MEMBERS')",
            name="visibility_scope",
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
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    visibility_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    owner_user: Mapped[User | None] = relationship(back_populates="personal_spaces")
    household: Mapped[Household | None] = relationship(back_populates="spaces")
    allocations: Mapped[list[TransactionAllocation]] = relationship(back_populates="space")
    budget_plans: Mapped[list[BudgetPlan]] = relationship(back_populates="space")
    income_schedules: Mapped[list[IncomeSchedule]] = relationship(back_populates="space")
    income_occurrences: Mapped[list[IncomeOccurrence]] = relationship(back_populates="space")
    commitment_templates: Mapped[list[CommitmentTemplate]] = relationship(back_populates="space")
    commitment_occurrences: Mapped[list[CommitmentOccurrence]] = relationship(
        back_populates="space"
    )
    goals: Mapped[list[Goal]] = relationship(back_populates="space")
    fund_reservations: Mapped[list[FundReservation]] = relationship(back_populates="space")
