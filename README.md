# 🛒 Shop / Product Management Module (Python & Django)

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/Django-6.1.1-green.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-blue.svg)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205.3.3-purple.svg)](https://getbootstrap.com/)
[![FontAwesome](https://img.shields.io/badge/Icons-FontAwesome%206%20%7C%20django--icons-orange.svg)](https://fontawesome.com/)

A modular, robust, and production-ready **Shop and Product Management Web Application** built with **Python** and **Django**. This platform features full authentication (allowing both Email ID and Username login), automated product code generation, comprehensive pricing and taxation calculations (GST and custom cess/surcharges), smart delivery constraints, multi-file image management, reference URL auto-validation, a dual-layout catalog (Amazon-style large card preview and tabular view), a 30-day soft-delete trash and revive lifecycle, creator-based access control, and an integrated icon subsystem powered by `django-icons` and FontAwesome 6.

---

## 📑 Table of Contents

- [Key Features & Highlights](#-key-features--highlights)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Data Models & Schema](#-data-models--schema)
- [URL Routing & Endpoints](#-url-routing--endpoints)
- [Business Rules & Validations](#-business-rules--validations)
- [Icon Subsystem (`django-icons`)](#-icon-subsystem-django-icons)
- [Project Directory Structure](#-project-directory-structure)
- [Setup & Installation Guide](#-setup--installation-guide)
  - [Prerequisites](#prerequisites)
  - [Option A: Using Pipenv (Recommended)](#option-a-using-pipenv-recommended)
  - [Option B: Using Standard Virtual Environment (`venv`)](#option-b-using-standard-virtual-environment-venv)
- [Database Configuration](#-database-configuration)
  - [PostgreSQL Configuration](#postgresql-configuration)
  - [SQLite Quick-Start Alternative](#sqlite-quick-start-alternative)
- [Database Migrations & Seeding](#-database-migrations--seeding)
- [Running the Development Server](#-running-the-development-server)
- [Django Admin Interface](#-django-admin-interface)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🌟 Key Features & Highlights

### 1. Dual-Identifier Authentication
- **Sign Up**: Clean registration requiring unique Email address, Username, and secure Password.
- **Flexible Login (`EmailOrUsernameBackend`)**: Authenticate seamlessly using **either Email ID or Username** alongside password.
- **Web Panel Redirection**: Authenticated users land automatically on the Web Panel Dashboard (`/home/`).
- **Session Security**: Protected views enforce `@login_required` decorators with standard login redirection.

### 2. Product Creation & Smart Automation (`/create-product/`)
- **Auto-Generated Product Code**: Generates standard `PRD-XXXXXX` identifiers (e.g. `PRD-000001`) automatically upon product creation.
- **Dynamic Delivery Synchronization**:
  - Selecting a **Delivery Type** automatically populates the **Delivery Time** field in real time.
  - Delivery time inputs are strictly read-only and non-editable by the user.
  - Selecting **Store Pickup** locks the **Delivery Charges** to `Rs. 0.00` and disables the charge input automatically.
- **Multi-File Image Upload**: Supports selecting and uploading multiple product images simultaneously (`JPG`, `PNG`, `WEBP`), designating the first uploaded image as primary.
- **URL Syntax Auto-Fix**: Automatically prepends `https://` to plain domains entered without a protocol (e.g., `example.com` $\rightarrow$ `https://example.com`), followed by standard `URLValidator` inspection.

### 3. Product Catalog & Dual-View Presentation (`/products/`)
- **Large Cards**: Showcases products with large previews (200px container), category badges, product codes, Rs. formatting, GST breakdown, delivery indicators, and action buttons.
- **Table Catalog View**: Alternate dense tabular layout featuring 80px image thumbnails, quick stats, and compact action controls.
- **Interactive View Switcher**: Instant switching between Large Cards and Table View without reloading the page.

### 4. Creator Ownership & Permissions
- **Strict Authorization**: Products can **only be edited or deleted by their original creator** (`product.created_by_id == request.user.id`).
- Attempted updates or deletions by unauthorized users are strictly rejected with an alert and redirect to `/products/`.
- UI action buttons (Edit, Delete, Revive, Purge) are conditionally rendered exclusively for the product creator.

### 5. Soft-Delete & 30-Day Retention Trash Lifecycle (`/products/trash/`)
- **Safe Soft Deletion**: Deleting a product marks `is_deleted=True` and records `deleted_at=timezone.now()`, removing it from the public catalog without dropping database records.
- **30-Day Purge Countdown**: The Trash view shows live remaining days before permanent purge (`days_until_purge`, `purge_date`).
- **One-Click Revival (`/products/<id>/revive/`)**: Restores soft-deleted products instantly back into the active catalog.
- **Permanent Purge Option (`/products/<id>/purge/`)**: Allows creators to immediately delete products and associated images permanently.

### 6. Robust Edit & Image Deletion Architecture
- Solves nested HTML form DOM parser collisions by isolating image deletion actions into dedicated external forms, preventing premature form termination and enabling smooth product updates.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Language** | Python 3.10 – 3.14 | Modern Python backend runtime |
| **Framework** | Django 6.1.1 | High-level Python Web framework |
| **Database** | PostgreSQL 14+ / SQLite 3 | Relational database storage |
| **Database Driver** | `psycopg2-binary` | High-performance PostgreSQL adapter |
| **Authentication** | Django Auth + Custom Backend | Dual Email or Username authentication |
| **Image Processing** | Pillow 12.3.0 | Product image validation and storage |
| **Form Rendering** | `django-crispy-forms` + `crispy-bootstrap5` | Clean, accessible Bootstrap form layouts |
| **Icon Framework** | `django-icons` | FontAwesome 6 semantic icon rendering |
| **Frontend Styling** | Bootstrap 5.3.3 | Responsive modern grid & UI components |
| **Icon Font** | FontAwesome 6.5.1 CDN | Solid vector icon library |

---

## 📊 Data Models & Schema

```text
       +------------------+
       |   auth.User      |
       +------------------+
                 | 1
                 |
                 | (created_by)
                 v *
+------------------------------------+          * +------------------+
|           main.Product             |----------->|  main.Category   |
+------------------------------------+ (category) +------------------+
| id: AutoField (PK)                 |
| code: CharField(50) [Unique]       |
| name: CharField(100)               |
| description: TextField             |
| base_price: DecimalField(10,2)     |
| gst: DecimalField(5,2)             |
| other_taxes: TextField             |
| delivery_type: CharField(20)       |
| delivery_time: CharField(100)      |
| delivery_charges: DecimalField     |
| other_information: TextField       |
| is_deleted: BooleanField           |
| deleted_at: DateTimeField          |
| created_at, updated_at             |
+------------------------------------+
       | 1                    | 1
       |                      |
       v * (images)           v * (urls)
+--------------------+   +--------------------+
| main.ProductImage  |   |  main.ProductURL   |
+--------------------+   +--------------------+
| id (PK)            |   | id (PK)            |
| product_id (FK)    |   | product_id (FK)    |
| image (ImageField) |   | title: CharField   |
| is_primary: Bool   |   | url: URLField      |
| uploaded_at        |   | created_at         |
+--------------------+   +--------------------+
```

### Core Models Summary

1. **`Category`** (`main.models.Category`):
   - Stores catalog categories (e.g., *Electronics*, *Home & Kitchen*, *Fashion*, *Books*, *Sports & Fitness*).
   - Relationship: Referenced by `Product` with `PROTECT` rule to avoid accidental cascade loss.

2. **`Product`** (`main.models.Product`):
   - Core entity capturing name, code, description, pricing, tax, shipping, and soft-delete state.
   - Contains calculated helper properties: `gst_amount`, `total_price`, `primary_image`, `purge_date`, and `days_until_purge`.

3. **`ProductImage`** (`main.models.ProductImage`):
   - Stores media files uploaded to `media/products/`.
   - Tracks primary thumbnail designation via `is_primary`.

4. **`ProductURL`** (`main.models.ProductURL`):
   - Captures external documentation, reference links, or partner web addresses.

---

## 🚦 URL Routing & Endpoints

| Endpoint | View Name | Methods | Auth Required | Description |
|---|---|---|---|---|
| `/` or `/home/` | `main:home` | `GET` | Yes | Web Panel Dashboard with statistics & quick actions |
| `/sign-up/` | `main:sign_up` | `GET`, `POST` | No | User registration with Email, Username & Password |
| `/login/` | `main:login` | `GET`, `POST` | No | Dual Email / Username login |
| `/logout/` | `main:logout` | `GET`, `POST` | Yes | Terminates session and redirects to login |
| `/create-product/` | `main:create_product` | `GET`, `POST` | Yes | Product creation form with image upload |
| `/products/` | `main:product_list` | `GET` | Yes | Product catalog (Large Cards / Table view toggle) |
| `/products/<id>/` | `main:product_detail` | `GET` | Yes | Comprehensive product detail view |
| `/products/<id>/edit/` | `main:edit_product` | `GET`, `POST` | Yes (Creator Only) | Update product info, add images, and modify URLs |
| `/products/<id>/delete/` | `main:delete_product` | `GET`, `POST` | Yes (Creator Only) | Soft-deletes product into 30-day retention Trash |
| `/products/trash/` | `main:trash_list` | `GET` | Yes (Creator Only) | View soft-deleted items with purge countdown |
| `/products/<id>/revive/` | `main:revive_product` | `POST` | Yes (Creator Only) | Restores soft-deleted product to active catalog |
| `/products/<id>/purge/` | `main:permanent_delete_product` | `POST` | Yes (Creator Only) | Permanently deletes product and images from database |
| `/products/<id>/images/<img_id>/delete/` | `main:delete_product_image` | `POST` | Yes (Creator Only) | Deletes an individual product image |
| `/admin/` | `admin:index` | `GET`, `POST` | Staff / Admin | Django Administration portal |

---

## 📐 Business Rules & Validations

The application enforces business rules across client JavaScript, Django Forms, and Django Models (`full_clean`):

| Parameter | Validation Rule | Enforcement Layer | Failure Message |
|---|---|---|---|
| **Base Price** | Strictly $\ge 0.00$ | Model Validator, Form Clean, HTML Input | *"Base price cannot be negative."* |
| **GST** | Strictly $0.00 \le \text{GST} \le 18.00\%$ | Model Validator, Form Clean, Model Clean | *"GST cannot exceed 18%."* |
| **Delivery Charges** | Strictly $0.00 \le \text{Charges} \le 100.00$ | Model Validator, Form Clean, Model Clean | *"Delivery charges cannot exceed 100."* |
| **Store Pickup** | Delivery charges must be Rs. 0.00 | JS Auto-set, Form Clean, Model Clean | *"Store pickup cannot have delivery charges (must be Rs. 0.00)."* |
| **Delivery Time** | Auto-mapped based on Delivery Type | JS Auto-set, Form Clean, Model Clean | Fixed to Delivery Type mapping |
| **URLs** | Must be valid HTTP/HTTPS URLs; automatically prefixes `https://` if protocol omitted | Form Clean (`clean_urls`), `URLValidator` | *"Invalid URL entered: '...'. Please enter a valid URL."* |
| **Ownership** | User must be creator to Edit, Delete, Revive, or Purge | View Permission checks | *"Permission Denied: You cannot modify a product created by another user."* |

### Delivery Time Mapping Matrix

| Delivery Type Code | Selection Label | Default Delivery Time | Delivery Charge Restriction |
|---|---|---|---|
| `STANDARD` | Standard Delivery | `3-5 Business Days` | $\le Rs. 100.00$ |
| `EXPRESS` | Express Delivery | `1-2 Business Days` | $\le Rs. 100.00$ |
| `SAME_DAY` | Same Day Delivery | `Within 24 Hours` | $\le Rs. 100.00$ |
| `PICKUP` | Store Pickup | `Immediate / Store Hours` | **Strictly Rs. 0.00 (Non-editable)** |

---

## 🎨 Icon Subsystem (`django-icons`)

The module integrates `django-icons`:

1. **Settings-Level Semantic Mapping**:
   Configured in `settings.py` under `DJANGO_ICONS`:
   - `edit` $\rightarrow$ `fa-solid fa-pen-to-square`
   - `trash` / `delete` $\rightarrow$ `fa-solid fa-trash`
   - `view` / `eye` $\rightarrow$ `fa-solid fa-eye`
   - `home` $\rightarrow$ `fa-solid fa-house`
   - `plus` $\rightarrow$ `fa-solid fa-plus`
   - `list` $\rightarrow$ `fa-solid fa-list`
 
2. **Template Tag Compatibility**:
   Supports standard `{% load icons %}`
3. **Spacing Utility Support**:
   Supports passing Bootstrap spacing classes directly (e.g. `{% icon "edit" "me-1" %}` $\rightarrow$ `<i class="fa-solid fa-pen-to-square me-1"></i>`).

---

## 📁 Project Directory Structure

```text
shopmodule/
├── manage.py                       # Django CLI management script
├── Pipfile                         # Pipenv dependency specifications
├── Pipfile.lock                    # Locked dependency versions
├── requirements.txt                # Pip requirements file
├── README.md                       # Comprehensive project documentation
├── media/                          # Uploaded product media files
│   └── products/                   # Product image storage
├── shopmodule/                     # Root Django project configuration
│   ├── __init__.py
│   ├── asgi.py                     # ASGI entrypoint
│   ├── backends.py                 # Custom authentication backend
│   ├── settings.py                 # Core Django configuration & DJANGO_ICONS
│   ├── urls.py                     # Global URL router & media server
│   └── wsgi.py                     # WSGI production entrypoint
└── main/                           # Core shop & product application
    ├── __init__.py
    ├── admin.py                    # Django Admin registrations & inlines
    ├── apps.py                     # Application configuration
    ├── backends.py                 # EmailOrUsernameBackend
    ├── forms.py                    # RegisterForm & ProductForm (with MultiFileField)
    ├── models.py                   # Category, Product, ProductImage, ProductURL
    ├── urls.py                     # Shop module URL endpoints
    ├── views.py                    # Authentication, dashboard & CRUD views
    ├── templatetags/               # Custom template tags
    │   └── __init__.py
    ├── migrations/                 # Database migrations
    │   ├── 0001_initial.py
    │   ├── 0002_productimage_producturl.py
    │   ├── 0003_product_created_by.py
    │   ├── 0004_seed_categories.py # Seeds default product categories
    │   ├── 0005_alter_product_base_price_...py
    │   ├── 0006_alter_product_base_price_...py
    │   └── 0007_product_deleted_at_...py
    └── templates/                  # HTML templates
        ├── main/
        │   ├── base.html           # Base layout, navbar with icons, flash messages
        │   └── home.html           # Web Panel Dashboard
        ├── products/
        │   ├── create_product.html # Product creation form with real-time scripts
        │   ├── edit_product.html   # Product edit form with image deletion
        │   ├── product_list.html   # Dual-view catalog (Large Cards / Table)
        │   ├── product_detail.html # Full product specifications & media gallery
        │   ├── trash_list.html     # Soft-deleted products with 30-day countdown
        │   └── delete_confirm.html # Confirmation modal for soft deletion
        └── registration/
            ├── login.html          # Login view (Email or Username)
            └── sign_up.html        # Registration view
```

---

## 🚀 Setup & Installation Guide

### Prerequisites
- **Python**: Version 3.10 to 3.14 installed.
- **Database**: PostgreSQL 14+ installed and running (or use SQLite for quick evaluation).
- **Package Manager**: `pip` or `pipenv`.

---

### Option A: Using Pipenv (Recommended)

1. **Navigate to the project root:**
   ```bash
   cd shopmodule
   ```

2. **Install all dependencies from Pipfile:**
   ```bash
   pipenv install
   ```

3. **Activate the Pipenv virtual environment:**
   ```bash
   pipenv shell
   ```

---

### Option B: Using Standard Virtual Environment (`venv`)

1. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Windows (CMD)
   python -m venv .venv
   .\.venv\Scripts\activate.bat

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install project dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🗄️ Database Configuration

### PostgreSQL Configuration

By default, `shopmodule/settings.py` reads database configuration from environment variables with sensible defaults:

```python
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'shopmodule_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

1. **Create the PostgreSQL database:**
   ```sql
   -- Log into psql
   psql -U postgres

   -- Run SQL:
   CREATE DATABASE shopmodule_db;
   ```

2. **(Optional) Configure environment variables via `.env` file in the project root:**
   ```env
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=shopmodule_db
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

---

### SQLite Quick-Start Alternative

If you do not have PostgreSQL installed and wish to run the project immediately using SQLite, set the following environment variables:

```bash
# Windows PowerShell
$env:DB_ENGINE="django.db.backends.sqlite3"
$env:DB_NAME="db.sqlite3"

# Linux / macOS
export DB_ENGINE="django.db.backends.sqlite3"
export DB_NAME="db.sqlite3"
```

---

## ⚙️ Database Migrations & Seeding

1. **Apply all migrations:**
   ```bash
   python manage.py migrate
   ```
   > **Note:** Migration `0004_seed_categories` automatically populates default categories (*Electronics*, *Home & Kitchen*, *Fashion*, *Books*, *Sports & Fitness*).

2. **Create a superuser for Django Admin:**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to enter a username, email, and password.

---

## 🌐 Running the Development Server

Start the local Django development server:

```bash
python manage.py runserver
```

Once started, open your web browser and navigate to:

- **Web Panel Dashboard**: [http://127.0.0.1:8000/home/](http://127.0.0.1:8000/home/)
- **Product Catalog**: [http://127.0.0.1:8000/products/](http://127.0.0.1:8000/products/)
- **Create Product Form**: [http://127.0.0.1:8000/create-product/](http://127.0.0.1:8000/create-product/)
- **Trash / Soft-Deleted Items**: [http://127.0.0.1:8000/products/trash/](http://127.0.0.1:8000/products/trash/)
- **User Login**: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **User Registration**: [http://127.0.0.1:8000/sign-up/](http://127.0.0.1:8000/sign-up/)
- **Django Administration**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---