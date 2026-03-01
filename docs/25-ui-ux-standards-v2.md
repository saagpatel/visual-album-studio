# UI/UX Standards V2 (Blocking Gates)

This document defines mandatory UI quality contracts for V2 implementation.

## Design direction
- Primary interaction language: platform-native desktop patterns.
- Visual consistency source: VAS token system (colors, spacing, typography, motion, elevation, semantic states).
- UX intent: low-cognitive-load workflows with explicit recovery and clear feedback.

## Required state matrix (all changed surfaces)
1. Loading
2. Empty
3. Error
4. Success
5. Disabled
6. Focus-visible
7. Keyboard-only path

## Accessibility baseline
- WCAG 2.2 criteria coverage for critical workflows.
- WAI-ARIA APG interaction semantics for command surfaces and composite widgets.
- Keyboard navigation map for top user paths.
- Reduced motion support for transitions and high-motion UI elements.
- Contrast policy checks for text, status chips, and actionable controls.

## UX quality gates (blocking)
1. Accessibility assertions pass on core workflow surfaces.
2. Visual regression checks pass for critical state matrix.
3. Interaction tests pass for keyboard/focus/command palette flows.
4. Responsive behavior checks pass for supported desktop window sizes.
5. Usability heuristic review completed each train (with tracked actions).

## Usability contracts for critical journeys
- First run to first successful export must remain streamlined.
- Export failure diagnosis must be actionable in <= 2 interactions.
- Collaboration conflict prompts must show clear resolution choices and consequences.
- Publishing flows must show provider-specific policy constraints before submission.

## Design tokens (minimum required sets)
- Color roles: background, surface, accent, text, semantic states.
- Typography: scale and hierarchy roles.
- Spacing: canonical spacing scale and layout rhythm.
- Motion: durations, easing presets, reduced-motion alternatives.
- Elevation: layer and modal depth contracts.

## Evidence expectations per train
Each train must publish:
1. UI gate report summary
2. Accessibility findings and remediation status
3. Visual regression baseline update notes
4. Known UX debt items with ownership and target train
