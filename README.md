# BAGAN BAZAR

Responsive gardening e-commerce starter built with Flask + SQLite.

## Run locally
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Create a virtual environment (recommended):
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Start: `python app.py`
6. Visit `http://127.0.0.1:5000`

The SQLite database, sample products and customer account table are created automatically on first run. Existing databases are migrated automatically when the app starts.

## Admin
- URL: `http://127.0.0.1:5000/admin/login`
- Default username: `admin`
- Default password: `admin123`

Set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `SECRET_KEY` environment variables before first production run. Change the default credentials before exposing this app to the internet.

## Included
- Responsive storefront, category navigation, product search, cart saved in browser localStorage
- Customer signup, login, logout and account page (email + password)
- Cash-on-delivery checkout and order creation
- Admin order list, customer/order detail editing, confirm/cancel/pending statuses
- Admin product add/edit/soft-delete
- SQLite relational tables for admins, categories, products, orders and order_items

## Before production
Configure HTTPS, a strong SECRET_KEY and admin password, add CSRF protection/rate limiting, validate uploaded product images, set backups for the SQLite database, and integrate a real payment gateway if online payment is needed. This starter uses cash on delivery only. Product photos are loaded from their respective image hosts; a local illustration is shown if a remote image is unavailable. A working internet connection is needed for the real product photos.

## Visual update
The storefront now uses real product/lifestyle photo URLs, an automatic hero slider, hover zoom on product/category photos, scroll reveal animations, and reduced-motion accessibility support. Product image fields in Admin accept a direct image URL. The photos are loaded from their respective image hosts, so the browser needs an internet connection to display them.
