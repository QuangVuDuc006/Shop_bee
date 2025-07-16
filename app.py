from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super-secret-key'

# ==== KIỂM TRA ĐĂNG NHẬP ====
def is_logged_in():
    return 'user' in session

# ==== DANH MỤC ====
categories = [
    {"id": 1, "name": "Thời trang nam", "image": "aonam.png", "slug": "thoitrang-nam"},
    {"id": 2, "name": "Thời trang nữ", "image": "aonu.png", "slug": "thoitrang-nu"},
    {"id": 3, "name": "Điện thoại", "image": "dienthoai.png", "slug": "dien-thoai"},
    {"id": 4, "name": "Thiết bị điện tử", "image": "thietbi.png", "slug": "dien-tu"},
    {"id": 5, "name": "Máy tính & Laptop", "image": "laptop.png", "slug": "may-tinh"},
    {"id": 6, "name": "Đồ gia dụng", "image": "giadung.png", "slug": "dogia-dung"},
    {"id": 7, "name": "Giày dép", "image": "giaydep.png", "slug": "giay-dep"},
    {"id": 8, "name": "Sức khỏe", "image": "suckhoe.png", "slug": "suc-khoe"},
    {"id": 9, "name": "Đồ chơi & Sở thích", "image": "dochoi.png", "slug": "do-choi"},
    {"id": 10, "name": "Thể thao & Outdoor", "image": "thethao.png", "slug": "the-thao"},
    {"id": 11, "name": "Thú cưng", "image": "thucung.png", "slug": "thu-cung"},
    {"id": 12, "name": "Mẹ và bé", "image": "mevabe.png", "slug": "meva-be"},
    {"id": 13, "name": "Nhà cửa & đời sống", "image": "nhacua.png", "slug": "nha-cua"},
    {"id": 14, "name": "Phụ kiện", "image": "phukien.png", "slug": "phu-kien"},
    {"id": 15, "name": "Nội thất", "image": "noithat.png", "slug": "noi-that"},
    {"id": 16, "name": "Mỹ phẩm", "image": "mypham.png", "slug": "my-pham"},
    {"id": 17, "name": "Nhà sách online", "image": "nhasach.png", "slug": "nha-sach"},
    {"id": 18, "name": "Khác", "image": "bacham.png", "slug": "khac"},
]

# ==== SẢN PHẨM ====
PRODUCTS_FILE = 'products.json'

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

products = load_products()

# ==== USERS ====
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# ==== CART COUNT ====
@app.context_processor
def inject_cart_count():
    if 'user' in session and 'carts' in session:
        user_cart = session['carts'].get(session['user'], [])
        unique_count = len(set(user_cart))
        return {'cart_count': unique_count}
    return {'cart_count': 0}

# ==== TRANG CHỦ ====
@app.route('/')
def home():
    user = session.get('user')
    users_data = load_users()

    cart = session.get('carts', {}).get(user, []) if user else []
    user_balance = 0
    if user:
        info = users_data.get(user)
        if isinstance(info, dict):
            user_balance = info.get("balance", 1500000)

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        cart=cart,
        user=user,
        user_balance=user_balance
    )

# ==== THÊM VÀO GIỎ HÀNG ====
@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if not is_logged_in():
        return jsonify({"success": False, "message": "Bạn chưa đăng nhập"})

    user = session['user']
    session.setdefault('carts', {})
    session['carts'].setdefault(user, [])
    session['carts'][user].append(product_id)
    session.modified = True

    unique_count = len(set(session['carts'][user]))
    return jsonify({"success": True, "cart_count": unique_count})

# ==== TRANG GIỎ HÀNG ====
@app.route('/cart')
def cart():
    if not is_logged_in():
        flash("Bạn cần đăng nhập để xem giỏ hàng!")
        return redirect(url_for('login'))

    user = session['user']
    cart_ids = session.get('carts', {}).get(user, [])
    cart_items = []
    total = 0

    counts = {}
    for pid in cart_ids:
        counts[pid] = counts.get(pid, 0) + 1

    for pid, quantity in counts.items():
        product = next((p for p in products if p["id"] == pid), None)
        if product:
            item = {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": product["price"] * quantity
            }
            cart_items.append(item)
            total += item["subtotal"]

    return render_template("cart.html", cart=cart_items, total=total)

# ==== TĂNG / GIẢM / XÓA ====
@app.route('/increase/<int:product_id>')
def increase(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    session['carts'][session['user']].append(product_id)
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        session['carts'][session['user']].remove(product_id)
        session.modified = True
    except ValueError:
        pass
    return redirect(url_for('cart'))

@app.route('/remove/<int:product_id>')
def remove(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    user = session['user']
    session['carts'][user] = [pid for pid in session['carts'][user] if pid != product_id]
    session.modified = True
    return redirect(url_for('cart'))

# ==== ĐĂNG KÝ ====
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users:
            flash("❗ Tài khoản đã tồn tại!")
            return redirect(url_for('register'))

        users[username] = {
            "password_hash": generate_password_hash(password),
            "balance": 0
        }
        save_users(users)
        flash("✅ Đăng ký thành công! Đăng nhập nhé 😎")
        return redirect(url_for('login'))
    return render_template('auth.html', register=True)

# ==== ĐĂNG NHẬP ====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username not in users:
            flash("❌ Tài khoản không tồn tại.")
            return redirect(url_for('login'))

        user_data = users[username]
        hashed_password = user_data.get("password_hash")

        if not hashed_password or not check_password_hash(hashed_password, password):
            flash("❌ Mật khẩu không chính xác.")
            return redirect(url_for('login'))

        session['user'] = username
        flash("✅ Đăng nhập thành công!")
        return redirect(url_for('home'))

    return render_template('auth.html', register=False)

# ==== ĐĂNG XUẤT ====
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("👋 Bạn đã đăng xuất.")
    return redirect(url_for('home'))

# ==== HIỂN THỊ THEO DANH MỤC ====
@app.route('/category/<slug>')
def show_category_by_slug(slug):
    category = next((c for c in categories if c["slug"] == slug), None)
    if not category:
        return "Không tìm thấy danh mục", 404
    filtered_products = [p for p in products if p.get("category_slug") == slug]
    return render_template("category.html", category=category, products=filtered_products)

# ==== CHẠY APP ====
if __name__ == '__main__':
    app.run(debug=True)

