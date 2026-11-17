# ADR 0001 — Web-first modular monolith

**Status:** Accepted baseline  
**Date:** 2026-11-15

## Context
Spendly is being developed initially by one student developer using AI coding agents. It needs a responsive desktop/mobile web experience and a backend that can later support native clients.

## Decision
Build a Next.js + TypeScript frontend and Python + FastAPI backend with MySQL. Start as a modular monolith with documented REST APIs.

## Consequences
Positive:
- lower operational complexity;
- clear domain boundaries;
- one source of financial logic;
- future clients can reuse API.

Trade-offs:
- modular discipline is required to avoid a tangled monolith;
- future scaling may require selective extraction, but not now.
