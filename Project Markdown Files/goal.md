# TapBhoj: Goal

## Vision
Make every small restaurant in India able to run a digital menu and take table orders over WhatsApp, started by a single tap of a phone on an NFC card.

## Problem
- Small restaurants and cafes still print menus, which are costly to update and easy to damage.
- Existing QR/ordering apps are built for large chains: expensive, complicated, and often locked to payments or delivery.
- Owners rarely get Google reviews, because customers have to search and navigate by themselves.
- Staff are busy taking orders by hand, and orders get missed or misheard.

## Solution
TapBhoj is a multi-restaurant web platform. Each restaurant gets an account, adds its own menu, prices and WhatsApp number, and receives a unique menu link. The link is written on NFC cards (one per table) and shown as a QR code. A customer taps, browses, picks dishes and sends the order to the restaurant's WhatsApp.

## Target users
| User | Need |
|---|---|
| Restaurant owner or manager (small cafe, dhaba, restaurant, 3 to 30 tables) | Cheap, simple menu and order setup; no technical skills |
| Customer (diner) | Fast menu on their own phone, no app install, no login |
| TapBhoj admin (platform owner) | Onboard restaurants, control access, collect payments |

## Primary goals
1. A restaurant owner can go from signup to a live menu in under 30 minutes without help.
2. A customer can open a menu and send an order in under 1 minute, with no app and no account.
3. The platform can serve many restaurants from one codebase and one database, safely separated.
4. Running cost stays low enough to charge small restaurants a monthly fee that they will actually pay.

## Secondary goals
- Increase Google reviews for each restaurant via a dedicated review NFC card and link.
- Give owners simple insights (popular dishes, orders per table).
- Support Hindi and English menus.

## Success metrics
- Restaurants onboarded and active (pilot target: 5 within the first 2 months, 25 within 6 months)
- Time to first published menu, per restaurant
- Orders sent via WhatsApp per restaurant per week
- Monthly retention of paying restaurants (target: above 80 percent)
- Menu page load time on a 4G phone (target: under 2 seconds)

## Non-goals (for the first release)
- No online payments for customers' food orders
- No delivery or rider management
- No kitchen display system
- No automatic WhatsApp Business API orders (considered later)
- No native mobile apps

## Business model (initial idea, to be validated)
- Monthly subscription per restaurant, with a free trial period
- Optional one-time setup fee that includes menu entry and NFC cards
- Possible add-ons later: custom domain, extra themes, order analytics
