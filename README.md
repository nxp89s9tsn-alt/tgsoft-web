# TGSoft Web — Deploy Guide

## Deploy to Vercel

1. Go to https://vercel.com and login
2. Import this `web/` folder as a new project
3. Set Environment Variables:
   - `ADMIN_LOGIN` = `admin`
   - `ADMIN_PASSWORD` = `your_secure_password`
   - `KV_REST_API_URL` = (from Vercel KV)
   - `KV_REST_API_TOKEN` = (from Vercel KV)
4. Create Vercel KV storage (Storage > KV > Create)
5. Deploy

## Admin Panel

- URL: `https://your-app.vercel.app/`
- Login: `admin`
- Password: (from ADMIN_PASSWORD env var)

## API Endpoints

| Endpoint | Method | Body | Description |
|---|---|---|---|
| `/api/register` | POST | `{login, password}` | Create user |
| `/api/login` | POST | `{login, password, machine_id}` | Login + check period |
| `/api/check` | POST | `{login}` | Check period status |
| `/api/admin` | POST | `{admin_login, admin_password, action}` | Admin operations |

## Admin Actions

- `action: "list"` — list all users
- `action: "set_period"` + `{login, days}` — set period for user
- `action: "revoke"` + `{login}` — revoke access
- `action: "info"` + `{login}` — get user info

## Update API URL in TGSoft

In `core/auth_client.py`:
```python
API_URL = "https://your-app.vercel.app"
```
