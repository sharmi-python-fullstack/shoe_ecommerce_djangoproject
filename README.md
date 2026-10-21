# StepUp.in Shoe Store

## Overview
This Django storefront follows the supplied StepUp.in Figma prototype and screenshots. It includes a responsive landing page, dedicated About and Contact pages, customer login and registration, category mega-menus, a timed/interactive offer carousel, a shoe-image lookbook carousel, searchable and filterable product cards, product details, a manageable shopping cart, and checkout. Contact enquiries are stored for review in Django Admin. All 65 images in the supplied ZIP are included in `static/images/figma_assets/`; the homepage uses the product, campaign, and payment images.

Product images on catalogue, product-detail, and cart pages open in an accessible zoom viewer with zoom-in, zoom-out, and reset controls. The cart includes category-based shoe-size selection (EU 36–46 for adult shoes and 25–35 for kids), quantity controls, and a local test-payment page.

## Quick Start
```bash
# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # on Windows

# Install dependencies and initialize the database
pip install -r requirements.txt
python manage.py migrate

# Load the demo catalogue if the database is empty
python manage.py seed_demo_products

# Create an administrator account
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in a browser.

## Razorpay test checkout
Install dependencies with `pip install -r requirements.txt`, then set your Razorpay **Test Mode** credentials in your local environment:

```powershell
$env:RAZORPAY_KEY_ID = "rzp_test_your_key_id"
$env:RAZORPAY_KEY_SECRET = "your_test_key_secret"
python manage.py runserver
```

Locally, Razorpay checkout is enabled when `DEBUG=True`, the Key ID starts with `rzp_test_`, and both credentials are configured. The secret stays on the Django server. Django creates the Razorpay order and verifies the payment signature before marking the store order as paid. Use Razorpay's test payment methods and test credentials from its official documentation; no real payment is processed.

To enable **test payments on Render**, keep `DEBUG=False` and add these environment variables to the web service:

- `RAZORPAY_TEST_MODE_ENABLED` = `True`
- `RAZORPAY_KEY_ID` = your Test Mode Key ID (starts with `rzp_test_`)
- `RAZORPAY_KEY_SECRET` = your Test Mode Key Secret

Razorpay checkout will only be enabled with an `rzp_test_` Key ID and a configured secret, even when the test-mode flag is enabled. Never put either credential in source code or commit them. Remove the test flag and test credentials when you no longer want to expose test checkout.

The Google Pay, PayPal, Clearpay, and Klarna checkout buttons remain visual demo choices only. Selecting one records an unpaid demo order. With `DEBUG=True`, a separate local simulation is also available when no payment method is selected. Neither demo flow contacts a payment provider.

## Product administration and categories
- Open `http://127.0.0.1:8000/admin/` and sign in with the superuser account.
- Customers can create an account or log in at `http://127.0.0.1:8000/account/`. The admin login remains available separately.
- About Us and Contact Us in the header open dedicated pages. Contact form submissions are available in Django Admin under **Contact inquiries**.
- Password reset emails use Django's console email backend in local development; reset links appear in the runserver terminal.
- Use **Products** to add or edit a product's name, slug, category, price, description, and image.
- The public header's **Log in** link opens the Django admin sign-in page.
- Product uploads are stored under `media/products/`; the bundled demo-product images are also included as static assets so they load on Render. For durable images uploaded through Django Admin in production, configure persistent media storage.
- The optional `figma_products` fixture adds the four featured products and their supplied images.
- The **Womens**, **Mens**, **Kids**, **Brands**, and **Offers** menus open the prototype-style navigation panels. Category and style links filter the catalogue.
- Selecting Womens, Mens, or Kids in the navigation opens that category's catalogue. The demo-category fixture supplies sample mens and kids products with images; categorize products you add in Django Admin using the Product category field.
- The footer newsletter form stores unique email subscriptions in the database; manage them from Django Admin.
- The offer carousel advances automatically, supports arrow and dot controls, and respects reduced-motion settings. Product and lookbook carousels can be scrolled with their arrow buttons.

## Deployment (Render)
1. Push the project to GitHub and create a Render **Web Service** from that repository.
2. Use **Python 3** as the runtime and configure:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_demo_products`
   - **Start Command**: `gunicorn shoe_ecommerce.wsgi:application`
3. Add a Render PostgreSQL database and set `DATABASE_URL` on the web service to its **Internal Database URL**.
4. Set these web-service environment variables:
   - `DEBUG` = `False`
   - `SECRET_KEY` = a newly generated Django secret key
   - `ALLOWED_HOSTS` = the service hostname, for example `shoe-ecommerce.onrender.com`
   - `CSRF_TRUSTED_ORIGINS` = the full HTTPS origin, for example `https://shoe-ecommerce.onrender.com`

The seed command adds the included demo products only when the catalogue is empty, so repeating it on later deploys does not overwrite products managed in Django Admin. To populate an existing deployment, update its build command and deploy again.

The app uses SQLite for local development when `DATABASE_URL` is not set. Keep `db.sqlite3`, `.env`, and `cookie.jar` out of Git; uploaded media on Render's local filesystem is not persistent across deploys, so use object storage if you need durable product uploads.

## Project Structure
```
shoe_ecommerce/
├─ shoe_ecommerce/      # project settings
├─ store/               # core app (models, views, urls, templates)
├─ static/              # CSS and images
│   ├─ css/style.css
│   ├─ js/storefront.js
│   └─ images/           # Supplied Figma brand, campaign, payment, and shoe assets
├─ templates/           # base and store templates
├─ manage.py
└─ requirements.txt
```

## License
MIT © 2026
