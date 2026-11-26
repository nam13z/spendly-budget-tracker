"""Database-specific Python types shared by model and migration metadata."""

from uuid import UUID

from sqlalchemy.dialects import mysql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import LargeBinary, TypeDecorator


class UUIDBinary(TypeDecorator[UUID]):
    """Map ``uuid.UUID`` to the contract's 16-byte MySQL BINARY representation."""

    impl = LargeBinary
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> LargeBinary:
        if dialect.name == "mysql":
            return dialect.type_descriptor(mysql.BINARY(16))
        return dialect.type_descriptor(LargeBinary(16))

    def process_bind_param(self, value: UUID | None, dialect: Dialect) -> bytes | None:
        """Serialize UUIDs using RFC 4122 byte order."""
        del dialect
        if value is None:
            return None
        if not isinstance(value, UUID):
            raise TypeError("UUIDBinary values must be uuid.UUID instances")
        return value.bytes

    def process_result_value(
        self, value: bytes | bytearray | memoryview | None, dialect: Dialect
    ) -> UUID | None:
        """Deserialize 16-byte values using the matching byte order."""
        del dialect
        if value is None:
            return None
        raw = bytes(value)
        if len(raw) != 16:
            raise ValueError("UUIDBinary database values must contain exactly 16 bytes")
        return UUID(bytes=raw)
