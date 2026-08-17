# Render Backend Deployment

## Service

- Type: Web Service
- Root Directory: `interview-backend`
- Build Command: `./build.sh`
- Start Command: `daphne -b 0.0.0.0 -p $PORT config.asgi:application`

## Required Environment Variables

Set these on the Render web service:

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-a-long-random-secret>
ALLOWED_HOSTS=<your-service-name>.onrender.com
DATABASE_URL=<your-render-postgres-internal-database-url>
INTERVIEW_ROOM_MAX_USERS=2
INTERVIEW_ROOM_PRESENCE_TTL_SECONDS=90
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
```

For quick testing, `CORS_ALLOW_ALL_ORIGINS=True` can stay enabled. For production, set it to `False` and add your frontend origins:

```env
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com
```

## Frontend / Desktop App Values

After Render gives you a backend URL such as:

```text
https://interview-backend.onrender.com
```

build the frontend or desktop app with:

```env
VITE_API_BASE_URL=https://interview-backend.onrender.com
VITE_WS_HOST=interview-backend.onrender.com
VITE_BACKEND_HOST=interview-backend.onrender.com
```

The frontend automatically uses `wss://` when it is served from HTTPS.
