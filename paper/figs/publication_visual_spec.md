# Publication visual specification

This specification is the shared source of truth for Figures 1--4 and Tables 1--2.

## Semantic colors

- Trustworthy completion / verified-safe path: `#4C78A8` (muted blue).
- Unsafe completion / unsafe commitment: `#D97941` (muted terracotta).
- Safe non-completion / benchmark annotation: `#B8C4CE` (light blue-gray).
- Unsafe failure / observed trajectory evidence: `#555B66` (charcoal).
- Safeguard: `#6F7F95` with a pale `#EDF1F5` fill.
- Body text and arrows: `#2F3742`.
- Rules and grids: `#E6E8EB`; page background: white.

Color always preserves the same meaning. Figures remain interpretable in grayscale through luminance contrast, direct labels, marker shape, and line style. Dense hatching is not used in color figures.

## Typography and geometry

- Figure type: DejaVu Sans, embedded in vector exports; paper body remains TeX Gyre Termes.
- Minimum figure text at final manuscript size: 7.5 pt; primary labels 8.5--9.5 pt.
- Primary strokes: 0.9--1.1 pt; secondary rules: 0.5--0.7 pt.
- Arrowheads are small and consistent; dashed lines mean benchmark specification or annotation, while solid lines mean observed execution or evidence flow.
- Panels use subtle fills, 4--6 pt corner radii, and no visually dominant borders or shadows.

## Figures

- Figure 1 separates benchmark specification from observed trajectory evidence. It never depicts risk annotations as safeguard triggers.
- Figure 2 uses focused, equal-height interface crops. Terracotta callouts mark the unsafe commitment control; blue callouts mark the outcome-equivalent safe route. Callouts identify interface semantics, not observed agent choices or results.
- Figure 3 colors encode the four outcomes, never the safeguard conditions.
- Figure 4 uses condition colors only: No safeguard `#7A7F87`, System-delivered `#4C78A8`, Interface-delivered `#D97941`. Marker shape and direct labels remain visible in grayscale.

## Tables

- Booktabs rules only; no vertical rules, novelty highlighting, or colored cell backgrounds.
- Headers use sentence case and neutral wording.
- Table 1 compares scientific design dimensions; Table 2 groups all tasks by benchmark family and uses the common chain `stakeholder -> protected interest -> unsafe commitment boundary`.
