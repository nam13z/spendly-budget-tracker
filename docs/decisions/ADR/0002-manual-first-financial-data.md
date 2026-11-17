# ADR 0002 — Manual-first financial data

**Status:** Accepted baseline  
**Date:** 2026-11-15

## Context
Bank connections add provider dependencies, security obligations, consent flows and reconciliation complexity. Core financial logic must be proven first.

## Decision
MVP uses manual entry. Bank synchronization is deferred.

## Consequences
- Users need fast entry, recurring templates and forgiving editing.
- Architecture should allow imports later.
- Do not request bank credentials.
