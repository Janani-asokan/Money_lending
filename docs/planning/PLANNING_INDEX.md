# Sakthi Ledger — Enterprise Planning Package

**Product:** Sri Sakthi Thirumurugan Finance ERP  
**Planning status:** Complete — consistency audit passed  
**Implementation status:** Blocked until this package is reviewed and approved

This package is the governing plan for Sakthi Ledger. It converts the design-system principles into a complete product structure before implementation begins.

## Required planning artifacts

| Artifact | Purpose | File |
|---|---|---|
| Design System | Visual, interaction, responsive, motion, reporting, data, and consistency rules | [Design System](../DESIGN_SYSTEM.md) |
| UI Blueprint | Page compositions, module identity, responsive layouts, states, and analytical content | [UI Blueprint](UI_BLUEPRINT.md) |
| UX Flows | Role journeys, task entry/exit, validation, permissions, error recovery, and cross-module continuity | [UX Flows](UX_FLOWS.md) |
| Component Library | Complete reusable component inventory, variants, states, composition, and ownership | [Component Library](COMPONENT_LIBRARY.md) |
| Navigation Map | Global shell, module hierarchy, role visibility, deep links, and responsive navigation | [Navigation Map](NAVIGATION_MAP.md) |
| Database Diagram | Target enterprise data model, relationships, sensitive-data boundaries, and indexing | [Database Diagram](DATABASE_DIAGRAM.md) |
| Workflow Diagrams | Customer, loan, payment, collections, approvals, delinquency, reports, and day-close flows | [Workflow Diagrams](WORKFLOW_DIAGRAMS.md) |
| Screen Map | Complete screen inventory, routes, compositions, actions, and required states | [Screen Map](SCREEN_MAP.md) |

## Implementation gate

Implementation may start only when all of the following are true:

- Every required artifact exists and cross-references the same terminology.
- Every page in the Screen Map has an approved composition and responsive specification.
- Every workflow has happy path, validation, permission, failure, retry, and audit behaviour.
- Every data object needed by the UI exists in the target database model.
- Every component is defined once in the Component Library.
- Every action has a real service contract; placeholder buttons are prohibited.
- Reports have working Preview, PDF, Excel, CSV, Print, Share, and Email contracts.
- Mobile, tablet, laptop, desktop, Tamil, accessibility, reduced-motion, and offline states are planned.
- Security-sensitive actions identify masking, permission, reason capture, and audit requirements.
- Product, UX, design, frontend, and backend plans agree on state names and lifecycle transitions.

## Product boundaries

### Primary users

- Owner
- Manager
- Accountant
- Collector

### Primary operating areas

- KUN — Kundi
- SLM — Salem
- NMK — Namakkal
- ERD — Erode

### Lending products

- Daily 100-Day
- Monthly EMI

### Primary modules

- Dashboard
- Customers
- Loans
- Collections
- Reports
- Audit
- Settings

Approvals, notifications, global search, command palette, quick actions, and user preferences are global operating layers rather than disconnected template pages.

## Planning rules

- No placeholder UI, demo cards, lorem ipsum, generic charts, or template pages.
- Example content must use realistic lending concepts, explicit calculations, and named operational decisions.
- No form is visible before its permitted create/edit action is invoked.
- No page is approved from desktop alone.
- No action appears without a defined outcome, permission, failure state, and audit requirement.
- One-off components or page-specific visual systems are prohibited.
- Current code is treated as a business-capability reference, not a design or architecture constraint.

## Source-of-truth hierarchy

If planning documents conflict, resolve in this order:

1. Financial truth, security, privacy, and statutory requirements
2. Approved business workflow and role permissions
3. Database lifecycle and audit model
4. Design System
5. UI Blueprint and UX Flows
6. Component Library
7. Individual screen annotation

Any resolved conflict must update every affected artifact before implementation.

## Completion record

- UI Blueprint: complete
- UX Flows: complete
- Component Library: complete
- Navigation Map: complete
- Database Diagram: complete
- Workflow Diagrams: complete
- Screen Map: complete
- Design-system alignment: complete
- Local-link validation: passed
- Diagram-fence validation: passed
- Screen ID validation: 106 unique screen/state IDs, no duplicates
- Implementation source changes during planning: none
