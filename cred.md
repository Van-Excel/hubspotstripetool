# Test Credentials

## Admin
- **Email:** admin@reconciliation.local
- **Password:** admin123
- **Role:** admin
- **How created:** Auto-seeded via data migration (`0003_seed_admin`)

## API Access
- JWT tokens obtained via `POST /api/auth/login/`
- Refresh via `POST /api/auth/refresh/`

## Registering New Users
- `POST /api/auth/register/` — Creates a user with default `viewer` role
- Admins can promote users via `PATCH /api/admin/users/{id}/`
