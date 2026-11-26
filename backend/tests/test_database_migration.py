"""Checks that the initial migration is discoverable and reversible."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_initial_migration_is_registered_and_covers_29_tables() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    revision = scripts.get_revision("head")
    source = Path(revision.path).read_text(encoding="utf-8")

    assert revision.revision == "0001_database_foundation"
    assert revision.down_revision is None
    assert source.count("op.create_table(") == 29
    assert source.count("op.drop_table(") == 29
    assert "fx_rates" not in source
    assert '"code": "LKR"' in source
    assert '"code": "USD"' in source
