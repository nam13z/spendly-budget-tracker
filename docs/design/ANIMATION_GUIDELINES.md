# Animation & Interaction Guidelines

## 1. Purpose

Motion should explain cause and effect, acknowledge actions and create a coherent sense of quality. It must never delay urgent financial tasks or obscure changing numbers.

## 2. Motion principles

- Purposeful, not constant.
- Fast for direct feedback; slower for spatial transitions.
- Consistent easing and duration tokens.
- Interruptible and reduced-motion aware.
- Avoid animation that changes the perceived value of money.
- Do not animate a financial amount in a way that could be mistaken for a live market feed.

## 3. Recommended motion tokens

Starting points, subject to usability testing:
- Micro feedback: 100–160 ms.
- Small state transition: 160–240 ms.
- Panel/modal transition: 180–280 ms.
- Page transition: 200–320 ms.
- Decorative/illustrative motion: rare and optional.

Use subtle ease-out for entrances and ease-in for exits. Avoid spring overshoot on balances, error messages or destructive actions.

## 4. Appropriate motion

- Button press feedback.
- Success confirmation after save.
- Progress bar update.
- Chart reveal when first shown.
- Navigation state change.
- Sheet/modal entrance.
- Reordering budget allocations with clear state.
- Skeleton-to-content transition.

## 5. Avoid

- Constant pulsing balances.
- Confetti for ordinary spending.
- Shame-based streaks or loss animations.
- Long mandatory onboarding animations.
- Motion that blocks keyboard or screen-reader interaction.
- Unnecessary parallax or heavy 3D effects on core screens.

## 6. Accessibility and performance

- Respect `prefers-reduced-motion`.
- Provide a user setting for reduced/subtle motion.
- Ensure animations do not cause layout shifts.
- Keep interaction responsive on lower-end devices.
- Do not convey status through animation alone.
- Test with keyboard, touch and screen reader.

## 7. Haptics and sound

Web MVP: do not depend on haptics or sound. Future native clients may add optional, subtle haptics for confirmation and navigation. Sound must be opt-in and never play unexpectedly.
