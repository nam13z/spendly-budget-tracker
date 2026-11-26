# ADR 0004 — Decimal-safe money representation

**Status:** Accepted baseline  
**Date:** 2026-11-15

## Context
Binary floating point cannot exactly represent many decimal fractions and is unsuitable for authoritative financial arithmetic.

## Decision
Use Python `Decimal`, MySQL `DECIMAL(19,4)` for monetary amounts, and decimal strings in API payloads. SQLAlchemy maps monetary amounts with `Numeric(19, 4, asdecimal=True)`. Frontend must use safe decimal handling. Currency minor-unit precision is distinct from storage scale; LKR and USD accept two fractional digits, and excess precision is rejected without implicit rounding.

## Consequences
- Centralize parsing and arithmetic; reject unsupported currency precision rather than silently rounding. Formatting follows currency metadata.
- Never use JS number for authoritative money calculations.
- Add currency-precision rejection and DECIMAL(19,4) boundary round-trip tests.
