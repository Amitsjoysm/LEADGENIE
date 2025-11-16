# LeadGen Pro - Enterprise Lead Generation Platform

Production-ready B2B lead generation platform with FastAPI + React + MongoDB + Redis + Celery

## Quick Start

```bash
# Run automated setup
chmod +x /app/setup.sh
/app/setup.sh
```

## Features
- Advanced profile search with 200M+ record support
- Credit-based contact reveal (1 for email, 3 for phone)
- Bulk CSV/Excel upload with field mapping
- MongoDB sharding for scalability
- Celery async processing
- JWT authentication with password reset
- Professional B2B UI with SEO optimization

## Tech Stack
**Backend**: FastAPI, MongoDB, Redis, Celery, Motor
**Frontend**: React 19, Tailwind CSS, Shadcn UI, Axios
**Architecture**: SOLID principles, Service pattern, Sharded database

## API Endpoints
- `POST /api/auth/login` - User login
- `POST /api/profiles/search` - Search profiles
- `POST /api/profiles/{id}/reveal` - Reveal contacts (costs credits)
- `POST /api/bulk-upload` - Bulk upload (Super Admin)

See `/docs` for full API documentation

## Default Credentials
Create super admin manually in MongoDB:
```javascript
db.users.updateOne(
  {email: "admin@example.com"},
  {$set: {role: "super_admin"}}
)
```

## Services
- Backend: http://localhost:8001
- Frontend: http://localhost:3000
- Celery: Background workers
- MongoDB: localhost:27017
- Redis: localhost:6379

Check status: `sudo supervisorctl status`

## Environment Setup
Configure `/app/backend/.env`:
- Update `SMTP_EMAIL` and `SMTP_PASSWORD` for emails
- Change `SECRET_KEY` for production
