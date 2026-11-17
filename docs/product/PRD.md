# Product Requirements Document (PRD)

**Version:** 1.0 | **Status:** Draft baseline

## 1. Product summary

Spendly is a responsive web application for personal and household financial organization and decision support. It begins with manual financial entry and provides accounts, transactions, spaces, flexible budgets, bills, goals, Safe-to-Spend and contextual analytics.

## 2. Goals

- Make everyday financial recording quick and forgiving.
- Show the difference between actual balances and committed money.
- Support irregular income and flexible budgeting.
- Support personal and household finances without double counting.
- Make every important derived figure explainable.
- Protect privacy and financial data.
- Establish a maintainable architecture for future mobile clients.

## 3. Non-goals for MVP

No bank credential collection, payment execution, AI chatbot, investment advice, public social feed, automated financial advice, native mobile apps or complex accounting/tax reporting.

## 4. Personas and jobs-to-be-done

### Student / allowance recipient
“When I receive money irregularly, help me see what remains until my next expected allowance.”

### Salaried individual
“When bills and recurring payments are approaching, help me see what I can safely use.”

### Freelancer
“When income arrives unpredictably, help me plan using confirmed money and clearly label uncertain future income.”

### Household participant
“When I pay for something shared, let me attribute the cost fairly without duplicating the purchase.”

### Household owner
“When my household manages shared expenses, let me invite members and control what is shared.”

## 5. Functional requirements

Priority definitions: P0 = launch blocker; P1 = MVP; P2 = later.

### Identity and onboarding
- P0: register, login, logout, password reset, authenticated sessions.
- P1: profile, primary currency, locale/timezone, optional PIN/app lock.
- P1: progressive onboarding with skip/complete-later options.
- P1: optional household create/join.
- P2: passkeys/social login after security review.

### Spaces and household
- P0: Personal space created for every user.
- P1: Home space available through household setup; custom spaces later.
- P0: server-enforced ownership and membership authorization.
- P1: temporary, revocable invitation code and QR; expiry and usage limit.
- P1: Owner and Member roles only at first.
- P1: personal transactions private by default.
- P2: granular role/permission matrix.

### Accounts
- P0: create account with name, type, currency and opening balance.
- P0: list account and current balance.
- P0: archive account without destroying history.
- P1: edit metadata and reconcile opening balance through an adjustment event.
- P1: account transfers.
- P2: account reconciliation tools.

### Transactions
- P0: create income and expense.
- P0: edit, view, search, filter and archive/delete according to retention policy.
- P0: category, account, date, currency, amount and description.
- P0: split allocations across spaces/categories.
- P1: transfers and refunds.
- P1: attachments/receipts only after storage/privacy design.
- P1: idempotent create endpoint.
- P2: bulk import and rules.

### Budgeting
- P0: create period-based budget.
- P0: allocate planned amount to categories or a flexible unallocated pool.
- P0: show spent, remaining and utilization with clear definitions.
- P1: adjust budget without rewriting actual transaction history.
- P1: weekly and monthly periods.
- P2: zero-based and advanced envelope workflows.

### Safe-to-Spend
- P0: show a transparent baseline calculation.
- P0: label as estimate and show “as of” timestamp.
- P0: separate confirmed and expected income.
- P0: include due commitments and user-designated reserves.
- P0: explain included/excluded inputs.
- P1: user-adjustable assumptions and safety buffer.
- P1: insufficient-data state rather than false precision.

### Bills and recurring activity
- P1: create one-time or recurring commitment.
- P1: due date, expected amount, currency, recurrence and status.
- P1: mark paid by linking to an actual transaction.
- P1: reminder preferences.
- P2: automatic recurring transaction suggestions.

### Goals
- P1: target, optional date, contribution history and progress.
- P1: goal contributions represented as transfers/reservations, not expenses unless money is actually spent.
- P2: shared household goals.

### Insights and reports
- P1: category totals, income vs expense, trend, budget progress, upcoming bills and goal progress.
- P1: comparison period and data completeness shown.
- P1: no insight if data is insufficient.
- P2: personalized narrative explanations and forecasts.

### Privacy and export
- P0: authorization isolation.
- P1: export user data in documented format.
- P1: account deletion workflow and retention policy.
- P1: session/device management.
- P2: advanced privacy controls and field-level sharing.

## 6. Core user stories and acceptance criteria

### Record an expense
Given an authenticated user with an active account, when they submit a valid expense, then exactly one transaction is created, account balance effects are correct, allocations validate, and a retry with the same idempotency key does not create a duplicate.

### Split an expense
Given an LKR 5,000 grocery transaction, when the user allocates LKR 2,500 to Home and LKR 2,500 to Personal, then the transaction remains LKR 5,000 and total actual spending remains LKR 5,000. Space reports show each attributed share.

### Transfer between accounts
Given two accounts owned by the same user, when LKR 10,000 is transferred from cash to bank, then source decreases and destination increases by the same amount, with no income or expense created.

### Expected income
Given an expected salary entry, when the user views current account balances, then the expected amount is not included in cash already received. It may appear separately in forecast scenarios.

### Mark a bill paid
Given a bill due, when the user marks it paid, the system must either link an actual transaction or create one through an explicit confirmed action. It must not silently mark paid without an auditable financial event.

### Safe-to-Spend
Given known balances, commitments and reserves, when the user opens the overview, then the displayed amount includes an explanation, date, assumptions and a warning if required data is missing or stale.

### Household privacy
Given two members in a household, when one member views the household, then only shared/authorized records are returned. Another member's private personal records are not exposed by direct API calls or guessed identifiers.

## 7. UX requirements

- Quick entry should be optimized for common expense capture.
- Optional fields should be progressively disclosed.
- Forms must preserve user input after recoverable validation errors.
- Destructive actions require confirmation and clear consequences.
- Every page has loading, empty, error and populated states.
- Empty states explain a useful next step.
- Avoid shame-based copy and manipulative engagement loops.
- Respect accessibility and reduced-motion preferences.

## 8. Quality attributes

- Financial correctness and auditability.
- Strong tenant/household isolation.
- Responsive performance.
- Maintainable modular code.
- Documented API.
- Automated test coverage for critical business rules.
- Secure backups and recoverability.

## 9. Release acceptance

MVP is releasable only when P0/P1 scope agreed for launch is complete, critical financial and authorization tests pass, backup/restore has been tested, privacy and deletion policies are published, and known limitations are communicated.
