# ADR 0003 — Separate transactions from allocations

**Status:** Accepted baseline  
**Date:** 2026-11-15

## Context
A single real purchase can benefit multiple spaces or people. Duplicating the purchase creates double-counting.

## Decision
Store one transaction and one or more allocation records. Account balance effects derive from the transaction, while space/category reporting derives from allocations.

## Example
One LKR 5,000 expense with Home allocation 2,500 and Personal allocation 2,500 remains one LKR 5,000 expense.

## Consequences
- Reports must use the correct aggregation level.
- Allocation validation is a critical server-side invariant.
- Partial allocation policy must be explicit.
