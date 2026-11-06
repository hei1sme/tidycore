---
name: TidyCore Fluent Workspace
colors:
  primary: "#005FB8"
  primary-hover: "#0055A6"
  canvas: "#F9F9F9"
  navigation: "#F3F3F3"
  surface: "#FFFFFF"
  ink: "#1B1B1B"
  muted: "#616161"
  border: "#E5E5E5"
  selection: "#E5F1FB"
  success: "#0F6B3B"
  error: "#A4262C"
typography:
  title: {fontFamily: Segoe UI Variable, fontSize: 28px, fontWeight: 600}
  heading: {fontFamily: Segoe UI Variable, fontSize: 18px, fontWeight: 600}
  body: {fontFamily: Segoe UI, fontSize: 14px, fontWeight: 400}
  caption: {fontFamily: Segoe UI, fontSize: 12px, fontWeight: 400}
  value: {fontFamily: Segoe UI Variable, fontSize: 28px, fontWeight: 600}
rounded: {control: 4px, navigation: 6px, surface: 8px, status: 12px}
spacing: {xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px}
components:
  button-primary: {backgroundColor: "{colors.primary}", textColor: "{colors.surface}", rounded: "{rounded.control}", height: 36px}
  navigation-selected: {backgroundColor: "#E9E9E9", textColor: "{colors.ink}", rounded: "{rounded.navigation}"}
  content-surface: {backgroundColor: "{colors.surface}", rounded: "{rounded.surface}", padding: 16px}
---

# TidyCore Fluent Workspace

## Overview
Windows 11 / Fluent is the user-selected reference for v2.2. Adapt Microsoft's
navigation, typography and layering guidance to existing Qt Widgets. Keep native
window chrome, dialogs, keyboard behavior and the Python/Qt implementation.
This is a Fluent-inspired solid-surface design, not a claim of native WinUI or Mica.

## Colors
Warm neutral navigation beside a near-white workspace. White bounded surfaces
group tasks. Blue identifies the primary action, focus and selected navigation
marker; green is reserved for completed activity and red for actual errors.
Status always has words; color is supplementary. Disabled controls must look disabled.

## Typography
Segoe UI Variable / Segoe UI, with OS font fallback. Use the Windows type ramp:
28px page title, 18px section heading, 14px controls/body, 12px metadata. Fluent
system glyphs accompany meaningful controls; labels remain readable without icons.

## Layout
220px navigation pane with a compact icon/wordmark header, flat navigation rows,
selected accent marker and quiet bottom actions. Content has 24px margins.
Activity has a title/status command row, watched-folder surface, compact inline
real statistics and one dominant history surface. Avoid a grid of metric cards.
Default window 1160×800; retain the 860×600 minimum with scrolling and elision.
At shorter heights, hide the secondary metrics strip so selected history rows
and Undo retain usable space. Path details stay on two elided lines with full tooltips.

## Elevation & Depth
Establish hierarchy with tonal layers, hairline borders and restrained rounding.
Do not simulate acrylic with gradients, wallpaper or expensive blur. No decorative
drop shadows. Windows provides the native outer frame and window corners.

## Shapes
4px controls, 6px selected navigation rows, 8px main surfaces. Small status badges
have rounded ends to distinguish state metadata from actions.

## Components
Activity history is searchable and filterable across its latest 200 persisted rows.
File glyphs, readable timestamps and state badges support scanning. Selection
reveals original/destination paths and a single content-checked undo action.
Statistics count journal operations minus undo, not a live inventory; label them
as recorded moves. Folder moves count as one. Empty results distinguish no history
from no search matches. Session messages live in a collapsible activity log;
errors open it automatically. Never substitute fabricated data or progress.

Settings separates General, File type rules and Ignored items into tabs. Keep
the folder field wide, options labeled, and Save outside scrolling. Rule actions
are visible and keyboard reachable, with invalid selections disabled. About
shows version, creator, storage location and an explicit manual-update link.

## Do's and Don'ts
Do keep first launch paused and require a deliberate target. Do inspect source
and the packaged EXE, ordinary/125% scaling, minimum sizing, focus and empty/error
states. Don't hide file-operation risks behind decoration, imply that journal
counts are a live disk census, or restore an unsafe auto-updater for appearance.

## References
- [Microsoft navigation guidance](https://learn.microsoft.com/en-us/windows/apps/design/controls/navigationview)
- [Windows typography](https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography)
- [Windows layering](https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/layering)
