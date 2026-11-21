import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "bagan_bazar.sqlite3"))

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS app_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
        phone TEXT DEFAULT '',
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '🌱'
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        description TEXT DEFAULT '',
        price REAL NOT NULL DEFAULT 0,
        image TEXT DEFAULT '',
        stock INTEGER NOT NULL DEFAULT 0,
        featured INTEGER NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        note TEXT DEFAULT '',
        subtotal REAL NOT NULL,
        delivery_fee REAL NOT NULL DEFAULT 60,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
    );
    """)
    if not con.execute("SELECT id FROM admins LIMIT 1").fetchone():
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "admin123")
        con.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                    (username, generate_password_hash(password)))
    if not con.execute("SELECT id FROM categories LIMIT 1").fetchone():
        cats = [("Tub & Planters","🪴"),("Garden Decor","🪴"),("Fertilizer","🌿"),("Tools","🛠️"),
                ("Seeds","🌱"),("Insecticides & Fungicide","🧴"),("Potting Mix","🪵"),
                ("Plant Nutrition","🍃"),("Combo Package","🎁"),("Sprayer & Jar","🚿")]
        con.executemany("INSERT INTO categories(name,icon) VALUES(?,?)", cats)
        samples = [
            ("Terracotta Plastic Plant Pot",1,"Durable lightweight terracotta-colour planter for indoor and outdoor plants.",180,"https://fromvictoria.co.uk/cdn/shop/files/recycledplasticplantpots_1080x.jpg?v=1692274120",40,1),
            ("Terracotta Garden Tub",1,"Classic terracotta-style tub for your garden.",350,"https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=900&q=85&fit=crop",25,1),
            ("Premium Round Planter",1,"A beautiful planter for home gardening.",420,"https://photo.floraccess.com/dtsnb7f6cje8gor003s0qjql2vjjb3ob4g1u984n_big.jpg",30,1),
            ("Indoor Money Plant",2,"Healthy indoor plant, ready for your home.",250,"https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=900&q=85&fit=crop",18,1),
            ("Organic Garden Fertilizer",3,"Balanced nutrition for healthy plant growth.",220,"https://cdn.pflanzen-koelle.de/media/ca/0b/5c/1775006363/1580200090-91-92-93-94-95-bluetengefluester-gross-2_243518.jpg",50,1),
            ("Hand Garden Hoe",4,"Useful hand tool for loosening soil.",160,"https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=900&q=85&fit=crop",20,0),
            ("Flower Seed Collection",5,"A colourful mix of seasonal flower seeds.",120,"https://www.jamiesonbrothers.com/media/catalog/product/s/e/seed_mockup_-_bundle_10_flower_kit.jpg",60,1),
            ("Coco Coir Potting Mix",7,"Lightweight growing medium for potted plants.",280,"https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=900&q=85&fit=crop",35,1),
            ("Garden Spray Bottle",10,"Easy-to-use hand sprayer for plant care.",190,"https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=900&q=85&fit=crop",22,0),
            ("Plant Nutrition Pack",8,"Everyday nutrition support for your plants.",320,"https://cdn.pflanzen-koelle.de/media/ca/0b/5c/1775006363/1580200090-91-92-93-94-95-bluetengefluester-gross-2_243518.jpg",16,1),
            ("Balcony Garden Combo",9,"A starter bundle for your balcony garden.",790,"https://www.jamiesonbrothers.com/media/catalog/product/s/e/seed_mockup_-_bundle_10_flower_kit.jpg",12,1),
            ("Neem Oil Insect Control",6,"Plant-care solution for common garden pests.",260,"https://images.unsplash.com/photo-1497250681960-ef046c08a56e?w=900&q=85&fit=crop",24,0)
        ]
        con.executemany("""INSERT INTO products(name,category_id,description,price,image,stock,featured)
                           VALUES(?,?,?,?,?,?,?)""", samples)
    # One-time catalogue photo migration. Do not overwrite future admin-edited image URLs.
    if not con.execute("SELECT 1 FROM app_meta WHERE key='catalogue_photos_v2'").fetchone():
        # Remote source URLs below were visually checked; the frontend also has a local fallback.
        con.execute("UPDATE products SET name='Terracotta Plastic Plant Pot', description='Durable lightweight terracotta-colour planter for indoor and outdoor plants.' WHERE name='White Plastic Plant Pot'")
        photo_map = {
            "Terracotta Plastic Plant Pot": "https://www.wilko.com/en-uk/assets/bWFzdGVyfGltYWdlc3wyMjI3NDV8aW1hZ2UvanBlZ3xoYjUvaGNkLzkzMzgwOTM5Mjg0NzgvMDQ4NzYyNl8xLmpwZ3w0MjJlN2VhMWEzYTUwYmM0ZjYzODFhNDA1YWUxOWNkMmMzODBmMjAyNzg2YmZmNTg4MTI1OWVjYjNmZDdjOWIx/0487626-1.jpg",
            "Terracotta Garden Tub": "https://www.wilko.com/en-uk/assets/bWFzdGVyfGltYWdlc3wyMjI3NDV8aW1hZ2UvanBlZ3xoYjUvaGNkLzkzMzgwOTM5Mjg0NzgvMDQ4NzYyNl8xLmpwZ3w0MjJlN2VhMWEzYTUwYmM0ZjYzODFhNDA1YWUxOWNkMmMzODBmMjAyNzg2YmZmNTg4MTI1OWVjYjNmZDdjOWIx/0487626-1.jpg",
            "Premium Round Planter": "https://www.urbanplant.in/cdn/shop/files/Green_Money_Plant.jpg?v=1753960317&width=900",
            "Indoor Money Plant": "https://www.urbanplant.in/cdn/shop/files/Green_Money_Plant.jpg?v=1753960317&width=900",
            "Organic Garden Fertilizer": "https://www.bioferamarket.com/cdn/shop/files/DSC01177_1.jpg?v=1723451002",
            "Hand Garden Hoe": "https://media.adeo.com/mkp/58c32aaac6635ced4c509d92acd4b933/media.jpeg",
            "Flower Seed Collection": "https://www.stocksandgreen.com/cdn/shop/files/MG_3141.jpg?v=1754404207",
            "Coco Coir Potting Mix": "https://cdn.myikas.com/images/dc30a1bd-ebaf-4439-8cf1-5dfc33967cdc/23c32896-9232-40ec-98b7-993afeac032f/1080/coco10.jpg",
            "Garden Spray Bottle": "https://hillshome.com.au/cdn/shop/files/100723_1LTriggerSprayer_5428_WEB.jpg?v=1713249049",
            "Plant Nutrition Pack": "https://rougenlove.com/cdn/shop/files/IMG-6379.jpg?v=1737670998&width=1024",
            "Balcony Garden Combo": "https://gardentrails.in/cdn/shop/files/Untitled_design_-_2026-05-28T151113.957.png?v=1779961319",
            "Neem Oil Insect Control": "https://i5.walmartimages.com/asr/78bb491f-31db-4a2c-8001-1c200e7a85be.19df279447d245fd4a82727cf36383ae.jpeg"
        }
        for product_name, image_url in photo_map.items():
            con.execute("UPDATE products SET image=? WHERE name=?", (image_url, product_name))
        con.execute("INSERT INTO app_meta(key,value) VALUES('catalogue_photos_v2','done')")
    con.commit()
    con.close()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.template_filter("money")
def money(value):
    return "৳{:,.0f}".format(value or 0)

@app.route("/")
def home():
    con = db()
    categories = con.execute("SELECT * FROM categories ORDER BY id").fetchall()
    products = con.execute("""SELECT p.*, c.name category_name FROM products p
                              LEFT JOIN categories c ON c.id=p.category_id
                              WHERE p.active=1 ORDER BY p.featured DESC,p.id DESC""").fetchall()
    con.close()
    category_images = {
        1: "https://www.wilko.com/en-uk/assets/bWFzdGVyfGltYWdlc3wyMjI3NDV8aW1hZ2UvanBlZ3xoYjUvaGNkLzkzMzgwOTM5Mjg0NzgvMDQ4NzYyNl8xLmpwZ3w0MjJlN2VhMWEzYTUwYmM0ZjYzODFhNDA1YWUxOWNkMmMzODBmMjAyNzg2YmZmNTg4MTI1OWVjYjNmZDdjOWIx/0487626-1.jpg",
        2: "https://media.adeo.com/mkp/8cc2d380b0366ef92327adccccb40a17/media.jpeg",
        3: "https://www.bioferamarket.com/cdn/shop/files/DSC01177_1.jpg?v=1723451002",
        4: "https://media.adeo.com/mkp/58c32aaac6635ced4c509d92acd4b933/media.jpeg",
        5: "https://www.stocksandgreen.com/cdn/shop/files/MG_3141.jpg?v=1754404207",
        6: "https://i5.walmartimages.com/asr/78bb491f-31db-4a2c-8001-1c200e7a85be.19df279447d245fd4a82727cf36383ae.jpeg",
        7: "https://cdn.myikas.com/images/dc30a1bd-ebaf-4439-8cf1-5dfc33967cdc/23c32896-9232-40ec-98b7-993afeac032f/1080/coco10.jpg",
        8: "https://rougenlove.com/cdn/shop/files/IMG-6379.jpg?v=1737670998&width=1024",
        9: "https://gardentrails.in/cdn/shop/files/Untitled_design_-_2026-05-28T151113.957.png?v=1779961319",
        10: "https://hillshome.com.au/cdn/shop/files/100723_1LTriggerSprayer_5428_WEB.jpg?v=1713249049"
    }
    con.close()
    return render_template("index.html", categories=categories, products=products, category_images=category_images)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    con = db()
    product = con.execute("""SELECT p.*,c.name category_name FROM products p
                             LEFT JOIN categories c ON c.id=p.category_id
                             WHERE p.id=? AND p.active=1""", (product_id,)).fetchone()
    con.close()
    if not product: abort(404)
    return render_template("product.html", product=product)

@app.route("/checkout", methods=["GET","POST"])
def checkout():
    if request.method == "POST":
        cart = request.form.get("cart_json", "[]")
        import json
        try: items = json.loads(cart)
        except Exception: items = []
        if not items:
            flash("আপনার কার্টে কোনো পণ্য নেই।", "error")
            return redirect(url_for("home"))
        name = request.form.get("customer_name","").strip()
        phone = request.form.get("phone","").strip()
        address = request.form.get("address","").strip()
        note = request.form.get("note","").strip()
        if not name or not phone or not address:
            flash("নাম, ফোন ও ঠিকানা পূরণ করুন।", "error")
            return redirect(url_for("checkout"))
        con = db()
        valid_items, subtotal = [], 0
        for item in items:
            try:
                pid, qty = int(item["id"]), max(1, min(99, int(item["qty"])))
            except Exception:
                continue
            p = con.execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone()
            if p and p["stock"] >= qty:
                valid_items.append((p, qty))
                subtotal += p["price"] * qty
        if not valid_items:
            con.close()
            flash("পণ্যগুলো বর্তমানে স্টকে নেই।", "error")
            return redirect(url_for("home"))
        fee = 60
        cur = con.execute("""INSERT INTO orders(customer_name,phone,address,note,subtotal,delivery_fee,total)
                             VALUES(?,?,?,?,?,?,?)""", (name,phone,address,note,subtotal,fee,subtotal+fee))
        oid = cur.lastrowid
        for p, qty in valid_items:
            con.execute("""INSERT INTO order_items(order_id,product_id,product_name,price,quantity)
                           VALUES(?,?,?,?,?)""", (oid,p["id"],p["name"],p["price"],qty))
            con.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty,p["id"]))
        con.commit()
        con.close()
        return render_template("success.html", order_id=oid)
    return render_template("checkout.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("customer_id"):
        return redirect(url_for("account"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or len(password) < 8:
            flash("নাম, সঠিক ইমেইল এবং কমপক্ষে ৮ অক্ষরের পাসওয়ার্ড দিন।", "error")
        elif password != confirm:
            flash("দুইটি পাসওয়ার্ড মিলছে না।", "error")
        else:
            con = db()
            try:
                cur = con.execute("INSERT INTO customers(name,email,phone,password_hash) VALUES(?,?,?,?)",
                                  (name, email, phone, generate_password_hash(password)))
                con.commit()
                session["customer_id"] = cur.lastrowid
                session["customer_name"] = name
                flash("আপনার অ্যাকাউন্ট তৈরি হয়েছে।", "success")
                con.close()
                return redirect(url_for("account"))
            except sqlite3.IntegrityError:
                flash("এই ইমেইল দিয়ে আগে থেকেই অ্যাকাউন্ট আছে। Login করুন।", "error")
            finally:
                try: con.close()
                except Exception: pass
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def customer_login():
    if session.get("customer_id"):
        return redirect(url_for("account"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        con = db()
        customer = con.execute("SELECT * FROM customers WHERE email=?", (email,)).fetchone()
        con.close()
        if customer and check_password_hash(customer["password_hash"], password):
            session["customer_id"] = customer["id"]
            session["customer_name"] = customer["name"]
            flash("সফলভাবে Login হয়েছে।", "success")
            return redirect(url_for("account"))
        flash("ইমেইল অথবা পাসওয়ার্ড সঠিক নয়।", "error")
    return render_template("login.html")

@app.route("/logout")
def customer_logout():
    session.pop("customer_id", None)
    session.pop("customer_name", None)
    flash("আপনি Logout করেছেন।", "success")
    return redirect(url_for("home"))

@app.route("/account")
def account():
    if not session.get("customer_id"):
        return redirect(url_for("customer_login"))
    con = db()
    customer = con.execute("SELECT id,name,email,phone,created_at FROM customers WHERE id=?",
                            (session["customer_id"],)).fetchone()
    con.close()
    if not customer:
        session.pop("customer_id", None)
        session.pop("customer_name", None)
        return redirect(url_for("customer_login"))
    return render_template("account.html", customer=customer)

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        con = db()
        admin = con.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
        con.close()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        flash("Username অথবা password সঠিক নয়।", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    con = db()
    orders = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    stats = {
        "total": con.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "pending": con.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0],
        "confirmed": con.execute("SELECT COUNT(*) FROM orders WHERE status='Confirmed'").fetchone()[0],
        "cancelled": con.execute("SELECT COUNT(*) FROM orders WHERE status='Cancelled'").fetchone()[0],
        "products": con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    }
    con.close()
    return render_template("admin.html", orders=orders, stats=stats)

@app.route("/admin/order/<int:order_id>", methods=["GET","POST"])
@admin_required
def admin_order(order_id):
    con = db()
    order = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        con.close(); abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            con.execute("""UPDATE orders SET customer_name=?,phone=?,address=?,note=? WHERE id=?""",
                        (request.form.get("customer_name","").strip(),
                         request.form.get("phone","").strip(),
                         request.form.get("address","").strip(),
                         request.form.get("note","").strip(), order_id))
            flash("Order details আপডেট হয়েছে।", "success")
        elif action in ("confirm","cancel","pending"):
            status = {"confirm":"Confirmed","cancel":"Cancelled","pending":"Pending"}[action]
            con.execute("UPDATE orders SET status=? WHERE id=?", (status,order_id))
            flash("Order status পরিবর্তন হয়েছে।", "success")
        con.commit()
        con.close()
        return redirect(url_for("admin_order", order_id=order_id))
    items = con.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    con.close()
    return render_template("admin_order.html", order=order, items=items)

@app.route("/admin/products", methods=["GET","POST"])
@admin_required
def admin_products():
    con = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            con.execute("""INSERT INTO products(name,category_id,description,price,image,stock,featured)
                           VALUES(?,?,?,?,?,?,?)""",
                        (request.form["name"],request.form.get("category_id") or None,
                         request.form.get("description",""),float(request.form.get("price",0)),
                         request.form.get("image","🌱"),int(request.form.get("stock",0)),
                         1 if request.form.get("featured") else 0))
            flash("নতুন পণ্য যোগ হয়েছে।", "success")
        elif action == "update":
            con.execute("""UPDATE products SET name=?,category_id=?,description=?,price=?,image=?,stock=?,featured=?
                           WHERE id=?""",
                        (request.form["name"],request.form.get("category_id") or None,
                         request.form.get("description",""),float(request.form.get("price",0)),
                         request.form.get("image","🌱"),int(request.form.get("stock",0)),
                         1 if request.form.get("featured") else 0,int(request.form["id"])))
            flash("পণ্যের তথ্য আপডেট হয়েছে।", "success")
        elif action == "delete":
            con.execute("UPDATE products SET active=0 WHERE id=?", (int(request.form["id"]),))
            flash("পণ্যটি ওয়েবসাইট থেকে সরানো হয়েছে।", "success")
        con.commit()
    products = con.execute("""SELECT p.*,c.name category_name FROM products p LEFT JOIN categories c
                              ON c.id=p.category_id WHERE p.active=1 ORDER BY p.id DESC""").fetchall()
    categories = con.execute("SELECT * FROM categories").fetchall()
    con.close()
    return render_template("admin_products.html", products=products, categories=categories)

@app.route("/api/products")
def api_products():
    con=db()
    rows=con.execute("SELECT id,name,price,image,stock FROM products WHERE active=1").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"),404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
