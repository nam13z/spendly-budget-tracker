"""Application service boundary for use-case orchestration and domain rules.

Services must not depend on FastAPI request/response types. Persistence belongs
behind repositories; services own transaction boundaries and domain policy.
"""
