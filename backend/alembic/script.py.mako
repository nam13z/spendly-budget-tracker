"""${message}"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.mysql as mysql

${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: Sequence[str] | None = ${repr(branch_labels)}
depends_on: Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Apply this revision."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Reverse this revision."""
    ${downgrades if downgrades else "pass"}
