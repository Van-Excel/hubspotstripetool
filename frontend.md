# Frontend — Unified Commerce Reconciliation Dashboard

## Tech Stack
- React 19 + Vite + TypeScript
- Tailwind CSS v4 + shadcn/ui
- React Router v7
- TanStack Query v5
- Axios (JWT interceptor)
- Sonner (toasts)
- Lucide React (icons)

## Design
- **Typeface**: Inter (sans), JetBrains Mono (mono)
- **Palette**: 90% monochrome, bright accents for severity/states
- **Inspiration**: Linear (tight sidebar), Stripe (card layouts), Apple (rounded, clean)

## Routes

| Route | Permission | Page |
|---|---|---|
| `/login` | public | Login form |
| `/dashboard` | `view_dashboard` | Stat cards, recent anomalies |
| `/anomalies` | `view_anomalies` | Filterable table, resolve dialog |
| `/payments` | `view_payments` | Payment list with status filters |
| `/deals` | `view_deals` | Deal list |
| `/customers` | `view_customers` | Customer list |
| `/audit` | `view_audit_logs` | Audit log viewer |
| `/admin/users` | `manage_users` | User management |

## Directory Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── components.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── types/index.ts
│   ├── providers/auth-provider.tsx
│   ├── hooks/
│   │   ├── use-anomalies.ts
│   │   ├── use-payments.ts
│   │   ├── use-deals.ts
│   │   ├── use-customers.ts
│   │   ├── use-dashboard.ts
│   │   ├── use-audit.ts
│   │   └── use-users.ts
│   ├── components/
│   │   ├── ui/            # shadcn (auto)
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── app-layout.tsx
│   │   ├── protected-route.tsx
│   │   ├── anomaly-badge.tsx
│   │   └── stat-card.tsx
│   └── pages/
│       ├── login.tsx
│       ├── dashboard.tsx
│       ├── anomalies.tsx
│       ├── payments.tsx
│       ├── deals.tsx
│       ├── customers.tsx
│       ├── audit.tsx
│       └── admin/users.tsx
```

## shadcn Components
button, input, label, card, table, badge, dialog, select, dropdown-menu, avatar, separator, skeleton, sonner, tabs, sheet, alert-dialog

## API Proxy
Vite proxies `/api/*` to `http://localhost:8000` for local dev.
