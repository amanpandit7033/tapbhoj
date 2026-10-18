# TapBhoj: Architecture

## 1. Overview
TapBhoj is a server-rendered Django web application. One codebase and one PostgreSQL database serve all restaurants (shared-database multi-tenancy). Pages are Django templates styled with Tailwind CSS. A small amount of JavaScript (Alpine.js or HTMX) handles the cart and interactive parts.

```
Customer phone --(tap NFC / scan QR)--> https://tapbhoj.in/r/<slug>/?table=3
        |                                         |
        |                               Reverse proxy (Nginx / platform)
        |                                         |
        |                               Django app (Gunicorn)
        |                               |         |         |
        |                          PostgreSQL   Media     Email
        |                                       storage   service
        v
 WhatsApp (wa.me link, pre-filled message) --> Restaurant's WhatsApp
```

## 2. Technology stack
| Layer | Choice | Notes |
|---|---|---|
| Backend | Django (current LTS) | Auth, admin, ORM, forms |
| Templates | Django template engine | Server-rendered pages |
| Styling | Tailwind CSS | Standalone CLI build, no Node server needed |
| Interactivity | Alpine.js or HTMX | Cart, quantity buttons, small updates |
| Database | PostgreSQL | Single database, tenant column on data |
| Static files | WhiteNoise | Served by the app with caching headers |
| Media (photos) | S3-compatible storage or Cloudinary | Resized on upload |
| Email | Transactional email provider | Password reset, onboarding |
| Payments | Razorpay | Subscriptions (Phase 3) |
| Hosting | Small VPS or Render/Railway | Managed PostgreSQL preferred |
| Monitoring | Sentry plus uptime check | Error and availability alerts |

## 3. Django apps (modules)
- **accounts:** users, login, password reset, owner profile linking user to restaurant.
- **restaurants:** Restaurant model, settings, table links and QR generation.
- **menu:** Category and MenuItem models, owner CRUD views.
- **public:** customer-facing menu page and order message builder.
- **billing:** plans, subscriptions, payments (Phase 3).
- **orders:** order log and analytics (Phase 4).
- **core:** shared base templates, utilities, middleware.

## 4. Data model (main entities)
**Restaurant**
- name, slug (unique), logo, description, whatsapp_number, address, google_review_url
- number_of_tables, currency (INR), language settings
- status (trial, active, paused, expired), created_at

**OwnerProfile**
- user (one-to-one with Django user), restaurant (foreign key)

**Category**
- restaurant, name, position, is_visible

**MenuItem**
- restaurant, category, name, description, price (decimal), is_veg
- photo, tags (bestseller, chef's pick), is_available, position

**Plan and Subscription** (Phase 3)
- plan name, price, period; restaurant, plan, start, end, status, payment reference

**OrderLog** (Phase 4)
- restaurant, table, items summary, total, created_at

All tenant-owned tables carry a restaurant foreign key. Indexes on (restaurant, position) and on slug.

## 5. Multi-tenancy rules
- Every owner view looks up the restaurant from the logged-in user, never from a URL or form value.
- Queries for owner data are always filtered by that restaurant.
- Public views are read-only and filtered by slug and active status.
- Automated tests confirm that owner A cannot read or change owner B's data.

## 6. URL structure
| URL | Purpose |
|---|---|
| /r/<slug>/ | Public menu (with ?table=N) |
| /login/, /logout/, /password-reset/ | Authentication |
| /dashboard/ | Owner home |
| /dashboard/profile/ | Restaurant settings |
| /dashboard/menu/ | Categories and items |
| /dashboard/tables/ | Table links and QR codes |
| /dashboard/orders/ | Order history (Phase 4) |
| /platform/ | TapBhoj admin area (staff only) |

## 7. Order flow
1. Customer opens the menu link from the NFC card or QR code.
2. The page loads the restaurant's categories and items from the database.
3. The cart lives in the browser until the order is sent.
4. On "Send order", the page builds a text message (table, items, quantities, total, note) and opens a wa.me link with that text.
5. The customer presses send in WhatsApp. The platform optionally logs the attempt (Phase 4).

## 8. Security
- HTTPS only, secure cookies, HSTS.
- Django's CSRF, XSS auto-escaping, and password hashing stay enabled.
- Rate limiting on login and password reset.
- Uploaded images are validated by type and size, and re-encoded.
- Secrets in environment variables, never in the repository.
- Admin area restricted to staff accounts, with strong passwords.

## 9. Performance
- Database queries use select_related and indexes.
- Menu pages are cached per restaurant and cleared when the owner saves changes.
- Images are resized to a few fixed widths and served lazily.
- Tailwind output is purged and minified.

## 10. Deployment and operations
- Environments: local, staging, production, with separate settings.
- Deploy via Git push and a simple pipeline: run tests, build CSS, migrate, collect static files.
- Daily automated database backups, with a tested restore.
- Logs and error tracking through Sentry; uptime alert by email or WhatsApp.

## 11. Growth path
Custom domains per restaurant, WhatsApp Business API for automatic orders, kitchen display screens, background workers (Celery) for emails and reports, read replicas if traffic grows.
