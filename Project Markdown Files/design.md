# TapBhoj: Design

## 1. Principles
- **Fast and light:** customers are hungry and on mobile data. Pages must load quickly and need no install.
- **One thumb, one hand:** big tap targets, important actions at the bottom of the screen.
- **Plain language:** short words, sentence case, no jargon. Buttons say exactly what they do ("Send order on WhatsApp").
- **Restaurant first:** the restaurant's name and logo lead the page; TapBhoj stays quiet in the background.
- **Owner simplicity:** every dashboard screen does one job and works on a phone.

## 2. Brand
- **Name:** TapBhoj ("bhoj" means a meal or feast; "tap" refers to the NFC tap)
- **Tone:** warm, friendly, practical
- **Logo idea:** a simple tap or ripple mark combined with a plate or bowl shape

## 3. Colour tokens
| Token | Light | Dark | Use |
|---|---|---|---|
| Background | #F1F4F0 | #0E1714 | Page |
| Surface | #FFFFFF | #16231F | Cards, sheets |
| Ink | #14231E | #EAF1ED | Main text |
| Muted | #5D6B65 | #9FB0A8 | Secondary text |
| Brand | #123D33 | #E8A317 | Buttons, active tabs |
| Accent | #E8A317 | #E8A317 | Tags, highlights |
| Veg | #1F8A3B | #4CC16A | Veg marker |
| Non-veg | #C0392B | #EE6B5C | Non-veg marker |
| Send (WhatsApp) | #1F8A3B | #1F8A3B | Send order button |

Restaurants may later choose their own accent colour, but the veg/non-veg colours stay fixed.

## 4. Typography
- **Headings:** Bricolage Grotesque (semi-bold to extra-bold)
- **Body:** Figtree (regular, medium, semi-bold)
- Fallbacks: system sans-serif and Georgia
- Body text 16 px minimum; line length under 80 characters; prices in semi-bold

## 5. Customer screens
1. **Menu:** restaurant name, short tagline, veg/non-veg legend, sticky category tabs, item rows (marker, name, tag, description, price, Add button).
2. **Cart bar:** appears at the bottom after the first item: item count, total, "View order".
3. **Order sheet:** lines with quantity buttons, total, table number (pre-filled), optional note, "Send order on WhatsApp", "Keep browsing".
4. **Footer:** Google review button and a price note.
5. **Paused page:** restaurant name and a simple "temporarily unavailable" message.

## 6. Owner dashboard screens
1. **Home:** status, quick links, today's order count.
2. **Profile:** name, logo, WhatsApp number (with format check), review link, tables.
3. **Menu manager:** categories with drag or arrow reorder; items list with sold-out toggle.
4. **Item form:** name, description, price, veg/non-veg, photo, tags.
5. **Tables and QR:** list of tables with link, copy button, QR download, print sheet.
6. **Orders (Phase 4):** today and history.

## 7. Admin screens
Restaurant list with status filters, create restaurant form, restaurant detail (owner, subscription, pause/activate), billing overview.

## 8. Components
Category chip, item row, quantity stepper, cart bar, bottom sheet, form field with inline error, toggle switch, status badge, empty state with a clear next action.

## 9. Accessibility and quality floor
- Contrast ratio at least 4.5:1 for text
- Tap targets at least 44 px
- Visible keyboard focus outlines
- Respect reduced-motion settings
- Labels on all form fields; buttons have descriptive names
- Works in light and dark mode on small screens first (360 px wide), then up

## 10. Copy rules
- Sentence case, plain verbs, no filler
- Errors say what went wrong and how to fix it, without apologising
- Same action keeps the same name everywhere ("Send order" is always "Send order")
- Prices always in rupees with the ₹ sign

## 11. Motion
Minimal. Only respond to taps (opening the order sheet, changing quantity). No decorative animations.
