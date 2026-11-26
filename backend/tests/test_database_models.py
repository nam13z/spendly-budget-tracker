"""Tests for the approved SQLAlchemy database contract."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Numeric
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.db.models import (
    Account,
    AccountEntry,
    FinancialTransaction,
    IncomeReceipt,
    TransferDetails,
)
from app.db.types import UUIDBinary


def test_uuid_binary_round_trip_and_strict_python_type() -> None:
    value = uuid4()
    sql_type = UUIDBinary()
    dialect = mysql.dialect()

    encoded = sql_type.process_bind_param(value, dialect)

    assert encoded == value.bytes
    assert len(encoded) == 16
    assert sql_type.process_result_value(encoded, dialect) == value
    with pytest.raises(TypeError):
        sql_type.process_bind_param(str(value), dialect)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        sql_type.process_result_value(b"short", dialect)


def test_model_metadata_registers_29_entities_and_valid_relationships() -> None:
    configure_mappers()

    assert len(Base.metadata.tables) == 29
    assert "fx_rates" not in Base.metadata.tables
    assert FinancialTransaction.__mapper__.relationships["allocations"]
    assert Account.__mapper__.relationships["entries"]
    assert IncomeReceipt.__mapper__.relationships["transaction"]


def test_uuid_keys_and_money_columns_match_storage_contract() -> None:
    for table in Base.metadata.tables.values():
        for column in table.primary_key.columns:
            if isinstance(column.type, UUIDBinary):
                assert column.type.load_dialect_impl(mysql.dialect()).length == 16
        for column in table.columns:
            if column.foreign_keys and column.name in {"currency_code", "primary_currency_code"}:
                continue
            if column.foreign_keys:
                assert isinstance(column.type, UUIDBinary)
                assert column.type.load_dialect_impl(mysql.dialect()).length == 16
        for column in table.columns:
            if column.name in {
                "amount",
                "amount_signed",
                "planned_amount",
                "expected_amount",
                "received_amount",
                "applied_amount",
            }:
                assert isinstance(column.type, Numeric)
                assert (column.type.precision, column.type.scale, column.type.asdecimal) == (
                    19,
                    4,
                    True,
                )

    assert isinstance(AccountEntry.__table__.c.amount_signed.type, Numeric)
    assert isinstance(FinancialTransaction.__table__.c.amount.type, Numeric)
    assert Decimal("0.1000") + Decimal("0.2000") == Decimal("0.3000")


def test_contract_constraints_and_foreign_key_behavior_are_present() -> None:
    entries = AccountEntry.__table__
    assert {"uq_account_entries_id_transaction_id"}.issubset(
        {constraint.name for constraint in entries.constraints}
    )
    assert any(
        {"transaction_id", "currency_code"}.issubset({column.name for column in fk.columns})
        for fk in entries.foreign_key_constraints
    )
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            assert foreign_key.ondelete == "RESTRICT"
            assert foreign_key.onupdate == "RESTRICT"
    assert IncomeReceipt.__table__.c.transaction_id.unique is True
    assert any(
        "amount > 0" in str(constraint.sqltext)
        for constraint in FinancialTransaction.__table__.constraints
        if getattr(constraint, "sqltext", None) is not None
    )
    transfer_uniques = {
        constraint.name
        for constraint in TransferDetails.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert "uq_transfer_details_source_account_entry_id" in transfer_uniques
    assert "uq_transfer_details_destination_account_entry_id" in transfer_uniques


def test_uuid_python_values_are_uuid_objects() -> None:
    assert isinstance(uuid4(), UUID)
