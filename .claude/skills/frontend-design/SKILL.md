---
name: frontend-design
description: Use when building or modifying frontend interfaces. Trigger words include UI, page, component, interface, frontend, hpc-ui, styling, layout, design, beautify. Generates distinctive, production-grade frontend code avoiding generic AI aesthetics.
---

# Frontend Design Constraints

## Overview

Create distinctive, production-grade frontend interfaces. Reject generic AI-generated aesthetics.

**Core principle:** Choose a bold aesthetic direction, then execute it with precision. The key is intentionality, not intensity.

## Design Thinking (before coding)

1. **Purpose** — What problem does this interface solve? Who uses it?
2. **Tone** — Pick a clear direction: brutally minimal, industrial, retro-futuristic, organic/natural, luxury/refined, editorial/magazine, brutalist, soft/pastel, geometric, utilitarian
3. **Constraints** — Framework, performance, accessibility requirements
4. **Differentiation** — What makes this unforgettable? The one thing someone will remember?

## Requirements by Dimension

### Typography
- Choose beautiful, unique, characterful fonts
- Pair a distinctive display font with a refined body font
- **BANNED:** Inter, Roboto, Arial, system default fonts

### Color
- Commit to a cohesive aesthetic, use CSS variables for consistency
- Dominant colors with sharp accents > timid, evenly-distributed palettes
- **BANNED:** Purple gradients on white backgrounds

### Motion
- Prefer CSS-only solutions
- React projects: use Motion (framer-motion) library
- One well-orchestrated page load animation (staggered delays) > scattered micro-interactions
- Use scroll-triggering and hover states that surprise

### Layout
- Bold spatial composition: asymmetry, overlap, diagonal flow, grid-breaking
- Generous negative space OR controlled density
- Avoid cookie-cutter card grids

### Backgrounds & Visual Details
- Create atmosphere and depth, don't default to solid colors
- Use: gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, grain overlays

## Blacklist — Absolute Bans

These are hallmarks of generic AI-generated interfaces:
- Inter / Roboto / Arial / system fonts
- Purple gradient + white background
- Cookie-cutter card layouts
- Generic component styling without context-specific character
- Converging on "safe choices" every time

## Implementation Principles

- Match complexity to vision: minimal designs need precision and restraint, maximalist designs need rich detail
- Elegance comes from executing the vision precisely, not from template stacking
- Every design should be different — vary themes, fonts, aesthetics
