# ADR 0004 — Decimal-safe money representation

**Status:** Accepted baseline  
**Date:** 2026-11-15

## Context
Binary floating point cannot exactly represent many decimal fractions and is unsuitable for authoritative financial arithmetic.

## Decision
Use Python Decimal, SQL DECIMAL and decimal strings in API payloads. Frontend must use safe decimal handling.

## Consequences
- Centralize parsing, arithmetic, rounding and formatting.
- Never use JS number for authoritative money calculations.
- Add precision/rounding tests for supported currencies.
