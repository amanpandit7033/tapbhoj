# TapBhoj: Requirements

Priority key: **M** = must have, **S** = should have, **C** = could have (later).

## 1. Users and roles
- **Customer:** anonymous, no login.
- **Restaurant owner:** logs in, manages one restaurant only.
- **Platform admin:** TapBhoj staff, manages all restaurants.

## 2. Functional requirements

### 2.1 Customer menu (public)
| ID | Requirement | Priority |
|---|---|---|
| C1 | Open a restaurant menu from a public URL such as /r/<slug>/ | M |
| C2 | Read the table number from the URL (?table=3) and pre-fill it | M |
| C3 | Browse by category; see name, description, price, veg/non-veg marker, tags | M |
| C4 | Hide or grey out items marked sold out | M |
| C5 | Add items to a cart with quantity buttons; see running total | M |
| C6 | Review the order, enter table number and optional note | M |
| C7 | Send the order to the restaurant's WhatsApp number as a pre-filled message | M |
| C8 | Show the restaurant name, logo, and Google review link | M |
| C9 | Show a friendly "temporarily unavailable" page when a restaurant is paused | M |
| C10 | Work well on small phones and slow mobile data | M |
| C11 | Dish photos | S |
| C12 | Hindi and English language switch | S |
| C13 | Search within the menu | C |

### 2.2 Restaurant owner dashboard
| ID | Requirement | Priority |
|---|---|---|
| O1 | Log in, log out, reset password by email | M |
| O2 | Edit restaurant profile: name, logo, WhatsApp number, address, Google review link | M |
| O3 | Create, edit, reorder and delete categories | M |
| O4 | Create, edit and delete menu items: name, description, price, veg/non-veg, photo, tags | M |
| O5 | Mark an item as sold out or available with one tap | M |
| O6 | See and download table links and QR codes for each table | M |
| O7 | Set the number of tables | S |
| O8 | Bulk import menu from a spreadsheet | C |
| O9 | See order history and popular items | S |
| O10 | Choose a menu theme or accent colour | C |

### 2.3 Platform admin
| ID | Requirement | Priority |
|---|---|---|
| A1 | Create a restaurant and its owner account in one step | M |
| A2 | Activate or pause a restaurant | M |
| A3 | View all restaurants, their status and subscription dates | M |
| A4 | Set plans, trial and expiry | S |
| A5 | Accept online payments and auto-pause on non-payment (Razorpay) | S |
| A6 | Impersonate or assist an owner to enter their menu | S |
| A7 | Platform-wide statistics | C |

## 3. Non-functional requirements
- **Performance:** menu page loads in under 2 seconds on 4G; images are resized and compressed on upload.
- **Security:** HTTPS everywhere; passwords hashed; CSRF protection; each owner can access only their own restaurant's data.
- **Privacy:** customers are not required to share personal data; no customer accounts.
- **Reliability:** daily database backups; target uptime of 99 percent or better.
- **Usability:** owner screens usable by someone with no technical background, on a phone or a laptop.
- **Accessibility:** readable contrast, tap targets of at least 44 px, keyboard focus visible.
- **Maintainability:** clear code structure, automated tests for tenant isolation and order message building.
- **Scalability:** comfortably supports hundreds of small restaurants on a single small server.

## 4. Constraints and assumptions
- Stack is fixed: Django, Django templates, Tailwind CSS, PostgreSQL.
- Orders reach the restaurant only when the customer presses send in WhatsApp; this cannot be confirmed by the platform.
- Customers pay the restaurant directly, as they do today.
- NFC cards use NTAG213 chips and store a plain URL only.
- All prices are in Indian rupees.

## 5. Out of scope for the first release
Customer payments, delivery, kitchen screens, WhatsApp Business API automation, native apps, loyalty programs.
