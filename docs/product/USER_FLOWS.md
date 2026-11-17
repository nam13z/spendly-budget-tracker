# User Flows

## 1. First-time setup

1. Landing page → create account.
2. Verify email (policy and provider to be selected).
3. Set name, country/locale and primary currency.
4. Choose: personal use / set up household / join household.
5. Add one account and opening balance (or skip).
6. Add income pattern (received vs expected clearly separated) or skip.
7. Choose budgeting approach: guided flexible default; optional category plan.
8. Set optional savings goal.
9. Choose appearance and communication preferences.
10. Arrive at overview with a concise checklist to finish setup later.

**Principle:** user must reach value quickly. Do not demand a complete financial biography during onboarding.

## 2. Quick expense entry

1. Tap/click Add.
2. Default to Expense; user can switch to Income or Transfer.
3. Enter amount and currency.
4. Select account.
5. Select category; suggest recent/default category but never silently misclassify.
6. Date defaults to today in user's timezone.
7. Optional description, space allocation and note.
8. Review split allocation if used.
9. Save.
10. Show confirmation and updated relevant figures.

Validation:
- amount must be positive;
- currency must match account rules or an explicit FX policy;
- allocation total must equal transaction amount for fully allocated transactions;
- if partial allocation is allowed, remainder must be visibly unallocated;
- duplicate retry must be idempotent.

## 3. Split expense across spaces

Example: one LKR 5,000 grocery purchase paid from a personal bank account.

1. Create one expense for LKR 5,000.
2. Choose “Split across spaces”.
3. Add Home LKR 2,500.
4. Add Personal LKR 2,500.
5. Review total allocated = LKR 5,000.
6. Save one transaction with two allocation records.

The account balance reduces by LKR 5,000. Home and Personal reports attribute 2,500 each. Combined reports count 5,000 once.

## 4. Household creation and invitation

1. User creates household.
2. System creates household boundary and default Home space.
3. Owner generates invitation.
4. Invitation has expiry, use limit, revocation and secure random token.
5. Display QR as a convenience representation of the invitation URL/token.
6. Invitee authenticates or registers.
7. Invitee previews household name and role before joining.
8. Server validates token, expiry, usage and owner permission.
9. Membership is created; invitation is consumed/revoked according to policy.

Do not encode private household data in the QR code.

## 5. Budget setup and adjustment

1. Choose weekly or monthly period.
2. Start with suggested categories or blank flexible plan.
3. Allocate planned amounts.
4. Keep an optional unallocated pool.
5. Review total planned amount against available/expected funds.
6. Save.
7. During the period, show actual spend and remaining budget separately.
8. Allow user to revise future allocations without altering transactions.
9. If over budget, show neutral recovery options.

## 6. Safe-to-Spend explanation

1. User selects Safe-to-Spend.
2. Show amount and “as of” timestamp.
3. Expand “How this is calculated”.
4. Show confirmed available balances, upcoming commitments, reserved amounts, safety buffer and optional scenario income.
5. Show data gaps and assumptions.
6. Offer editable assumptions.
7. Recalculate deterministically on the server.

## 7. Bill payment

1. Open upcoming bill.
2. Choose Mark paid.
3. Select existing transaction or create a new expense.
4. Confirm amount/date/account.
5. Link payment transaction to bill occurrence.
6. Update bill status.
7. Prevent duplicate payment linking.

## 8. Recovery after overspending

1. Identify the budget/category that exceeded plan.
2. Explain actual vs planned amount and period.
3. Offer choices: adjust remaining categories, use a buffer, reduce a future allocation, or leave plan unchanged.
4. Explain trade-offs.
5. User chooses; system never moves funds or edits actual history automatically.
