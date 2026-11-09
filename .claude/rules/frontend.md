---
paths:
  - "apps/web/**/*"
  - "packages/ui/**/*"
---

# Frontend (LLD section 12)

- Next.js 15 App Router, TypeScript 5, Tailwind, shadcn/ui, TanStack Query, Zustand, next-auth.
- Server state lives in TanStack Query. WebSocket events invalidate query keys (`['ticket', id]`, `['approvals']`).
- Approval decisions use optimistic updates with rollback.
- The UI is role-aware via session claims, but the API stays the authority. Never hide a check only in the UI.
- `ChatWidget` is a React-built Web Component (Shadow DOM, SSE).
- Must meet WCAG 2.1 AA (NFR-16).
