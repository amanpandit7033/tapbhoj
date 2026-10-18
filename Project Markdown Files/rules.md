# TapBhoj: Rules

These rules apply to everyone building or changing the project, including AI coding assistants.

## 1. Product rules
- Keep it simple: a restaurant owner with no technical skills must be able to use every owner screen.
- Customers never need an account or an app.
- Do not add customer payments, delivery, or kitchen features before the roadmap says so.
- Each NFC card holds one plain URL. Do not mix purposes (menu and review links stay on separate cards).

## 2. Multi-tenant data rules
- Every tenant-owned model has a restaurant foreign key.
- Owner views get the restaurant from the logged-in user, never from the URL, form, or query string.
- All queries on tenant data must be filtered by restaurant. No unscoped queries in owner views.
- Public views expose only active restaurants and available items.
- Every new feature that touches tenant data needs a test showing another restaurant's data stays hidden.

## 3. Security rules
- Never commit secrets, keys, passwords, or .env files.
- Keep Django's CSRF, auto-escaping, and password hashing enabled.
- Validate all uploads (type, size) and re-encode images.
- Validate the WhatsApp number format (country code plus digits, no spaces or symbols).
- Rate limit login, password reset, and public endpoints that write data.
- Use HTTPS only; set secure cookie flags in production.
- Staff and admin accounts use strong passwords and, when possible, two-factor authentication.

## 4. Code rules
- Follow Django conventions and PEP 8; format with an automatic formatter and run a linter.
- Keep views thin; put business logic in models, services, or helpers.
- Use migrations for every schema change; never edit the database by hand in production.
- Write tests for tenant isolation, order message building, permissions, and billing state changes.
- Prefer small, readable functions and clear names over clever code.
- No unused dependencies. Pin versions.
- Keep JavaScript small; do not add a frontend framework.

## 5. Template and styling rules
- Use Tailwind utility classes; extract repeated patterns into template includes.
- Mobile-first: design for 360 px width, then scale up.
- Use the colour and type tokens in design.md; do not invent new ones without updating design.md.
- Support light and dark mode on all customer pages.
- Never trust user content in templates: rely on auto-escaping and avoid marking user text as safe.

## 6. Performance rules
- Menu page target: under 2 seconds on 4G.
- Resize and compress uploaded photos; serve appropriate sizes with lazy loading.
- Avoid database queries inside loops; use select_related and prefetch_related.
- Cache each restaurant's public menu and clear the cache on any menu or profile save.

## 7. Content and policy rules
- Do not offer discounts or rewards for Google reviews, and do not filter who gets asked. Google's policies prohibit this.
- Do not collect customer personal data unless a feature clearly needs it and the customer agrees.
- Prices must be shown clearly in rupees; note if taxes are included.
- Do not claim the platform confirms orders; the customer must press send in WhatsApp.

## 8. Git and workflow rules
- Work in short-lived branches; merge to main through reviewed changes.
- Commit messages say what changed and why.
- Tests must pass before merging.
- Deploy to staging first, then production.
- Database backups run daily; test a restore at least once before launch.

## 9. Release rules
- A phase is finished only when its "Done when" condition in phase.md is true.
- A new restaurant goes live only after the owner has tested a real order on their own phone and an iPhone and an Android have both opened the NFC card.

## 10. Rules for AI assistants working in this repository
- Read goal.md, requirements.md, architecture.md, design.md and phase.md before making changes.
- Stay within the current phase; do not build later-phase features unasked.
- Do not change the stack (Django, Django templates, Tailwind, PostgreSQL).
- Do not weaken security or tenant-isolation rules to make something work.
- If a request conflicts with these rules, say so and suggest an alternative.
