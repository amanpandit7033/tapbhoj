# TapBhoj: Phases

Timeline assumes one developer. Part-time work takes roughly twice as long as the full-time estimates.

## Phase 0: Setup and planning (2 to 3 days)
**Tasks**
- Finalise data model and screen list
- Create Django project, PostgreSQL database, environment settings, Git repository
- Set up Tailwind (standalone CLI) and a base layout
- Choose hosting, image storage and email provider
- Register domain (tapbhoj.in) and social handles

**Done when:** an empty project runs locally and on a test server.

## Phase 1: Menu with WhatsApp ordering (1 to 2 weeks)
**Tasks**
- Models: Restaurant, Category, MenuItem
- Data entry through Django's built-in admin (by you)
- Public menu page: category tabs, veg/non-veg markers, tags, sold-out state
- Cart, order sheet, table number from URL, WhatsApp send button
- Paused-restaurant page
- Mobile-first layout and dark mode

**Done when:** one real pilot restaurant uses it on live NFC cards.

## Phase 2: Owner dashboard (2 to 3 weeks)
**Tasks**
- Owner login, logout, password reset
- Restaurant profile editor (name, logo, WhatsApp number, Google review link)
- Category and item management with photos
- One-tap sold-out toggle
- Table links and downloadable QR codes
- Tenant isolation tests

**Done when:** an owner can set up and maintain their menu without your help.

## Phase 3: Platform admin and billing (2 weeks)
**Tasks**
- Create restaurant plus owner in one form; send login details by email
- Activate/pause switch; trial and expiry dates
- Plans and Razorpay payments; auto-pause on lapse
- Admin dashboard: totals, active, expiring soon

**Done when:** you can onboard and charge a restaurant without touching the database.

## Phase 4: Order records and insights (1 to 2 weeks)
**Tasks**
- Log each order when the customer taps send
- Owner view: today's orders, popular dishes, orders per table
- Optional private feedback form

**Done when:** owners can see a useful summary of activity.

## Phase 5: Hardening and growth (ongoing)
**Tasks**
- Backups, monitoring, rate limiting, security review
- Hindi and English menus
- Custom domains, themes, installable web app (PWA)
- Later: WhatsApp Business API, kitchen screens

## Summary
| Phase | Focus | Estimate |
|---|---|---|
| 0 | Setup | 2 to 3 days |
| 1 | Public menu + WhatsApp | 1 to 2 weeks |
| 2 | Owner dashboard | 2 to 3 weeks |
| 3 | Admin + billing | 2 weeks |
| 4 | Orders + insights | 1 to 2 weeks |
| 5 | Hardening + growth | Ongoing |

## Release rule
Do not start a phase until the previous phase's "Done when" is true and the pilot restaurant has confirmed it works.
