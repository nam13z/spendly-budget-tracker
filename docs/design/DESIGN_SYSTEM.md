# Design System — Spendly

## 1. Design intent

Premium, calm, modern and understated. Old-money inspiration should guide restraint, typography, materials and color—not create a dated imitation or reduce readability.

## 2. Initial visual direction

Provisional palette; final values must be validated against user-provided references and accessibility contrast.

- Warm ivory / parchment surfaces.
- Deep forest green as primary brand anchor.
- Muted antique gold as a restrained accent.
- Ink/charcoal for primary text.
- Muted stone for secondary surfaces.
- Semantic success/warning/error colors must remain legible and not depend on the brand palette.

Do not use gold for small text on cream if contrast is insufficient.

## 3. Typography

Use a clear, highly legible sans-serif for UI and numerals. A restrained display serif may be used for selected headings, but never for dense transaction data or form controls. Numerals should align consistently in tables and balances.

## 4. Layout

- Clear hierarchy: current position → commitments → safe-to-spend → actions → insights.
- Use consistent spacing scale and responsive grid.
- Keep primary actions predictable.
- Prefer readable whitespace over card overload.
- Avoid dashboards made entirely of decorative tiles.
- Transaction lists prioritize date, description, category, account and amount.

## 5. Component principles

Build reusable components:
- MoneyAmount
- CurrencyInput
- AccountSelector
- CategoryPicker
- SpaceSelector
- AllocationEditor
- TransactionForm
- BudgetProgress
- CommitmentRow
- SafeToSpendSummary
- InsightCard
- EmptyState
- ErrorState
- ConfirmDialog

Financial components must receive already-validated values and explicit currency metadata.

## 6. Money display

- Always display currency context.
- Do not truncate important balances without a way to inspect exact value.
- Use locale-aware formatting.
- Negative values must be unambiguous.
- Do not use color alone for positive/negative.
- Distinguish “balance”, “available”, “budget remaining” and “Safe-to-Spend” in labels.

## 7. Personalization

Three layers:
1. Visual: curated palettes, light/dark mode, accent.
2. Communication: refined, friendly, minimal, warm.
3. Interaction: motion intensity, optional sound, reduced motion.

Themes must preserve semantic colors and contrast. Vocabulary variants must preserve financial meaning.

## 8. Responsive behavior

- Desktop: efficient overview and transaction table.
- Tablet: adaptive two-column layouts.
- Mobile web: single-column priorities, bottom navigation if appropriate, quick-add reachable.
- Avoid horizontal scrolling for core tasks.
- Forms must work with mobile keyboards and touch targets.

## 9. Content design

Use clear, neutral language:
- “You’re LKR 1,200 over this category’s plan” rather than “You failed your budget”.
- “Your plan may need adjusting” rather than “You overspent again”.
- “Expected income” rather than presenting it as cash.
- “Not enough information yet” when data is incomplete.

## 10. Design QA

Check contrast, focus, hover, pressed, disabled, loading, empty, error, long text, large numbers, zero values, negative values, multi-currency and reduced-motion states.
