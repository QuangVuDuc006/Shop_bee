from flask import Flask, render_template, redirect, url_for, session, request, flash
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super-secret-key'

# ==== KIỂM TRA ĐĂNG NHẬP ====
def is_logged_in():
    return 'user' in session

# ==== DANH SÁCH SẢN PHẨM GIẢ ====
products = [
    {"id": 1, "name": "Áo thun", "price": 120000},
    {"id": 2, "name": "Quần jeans", "price": 250000},
    {"id": 3, "name": "Giày sneaker", "price": 500000},
]

# ==== FILE USERS ====
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# ==== TRANG CHỦ ====

categories = [
    {"name": "Thời trang nam", "image": "aonam.png"},
    {"name": "Thời trang nữ", "image": "aonu.png"},
    {"name": "Điện thoại", "image": "dienthoai.png"},
    {"name": "Thiết bị điện tử", "image": "thietbi.png"},
    {"name": "Máy tính & Laptop", "image": "laptop.png"},
    {"name": "Đồ gia dụng", "image": "giadung.png"},
    {"name": "Giày dép", "image": "giaydep.png"},
    {"name": "Sức khỏe", "image": "suckhoe.png"},
    {"name": "Đồ chơi & Sở thích", "image": "dochoi.png"},
    {"name": "Thể thao & Outdoor", "image": "thethao.png"},
    {"name": "Thú cưng", "image": "thucung.png"},
    {"name": "Mẹ và bé", "image": "mevabe.png"},
    {"name": "Nhà cửa & đời sống", "image": "nhacua.png"},
    {"name": "Phụ kiện", "image": "phukien.png"},
    {"name": "Nội thất", "image": "noithat.png"},
    {"name": "Mỹ phẩm", "image": "mypham.png"},
    {"name": "Nhà sách online", "image": "nhasach.png"},
    {"name": "Khác", "image": "bacham.png"},
]


@app.context_processor
def inject_cart_count():
    if 'user' in session and 'carts' in session:
        user_cart = session['carts'].get(session['user'], [])
        unique_ids = set(user_cart)  # chỉ đếm mỗi sản phẩm 1 lần
        return {'cart_count': len(unique_ids)}
    return {'cart_count': 0}

@app.route('/')
def home():
    user = session.get('user')
    cart = session.get(f"cart_{session['user']}", []) if is_logged_in() else []
    user = session.get('user')
    return render_template("index.html", products=products, cart=cart, user=user, categories=categories)
    cart_count = len(set(cart))  # Đếm số loại sản phẩm duy nhất
    return render_template("index.html", products=products, cart=cart, user=user, cart_count=cart_count)

# ==== GIỎ HÀNG ====
@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if not is_logged_in():
        flash("Bạn cần đăng nhập để mua hàng!")
        return redirect(url_for('login'))

    user = session['user']
    if 'carts' not in session:
        session['carts'] = {}

    if user not in session['carts']:
        session['carts'][user] = []

    session['carts'][user].append(product_id)
    session.modified = True
    return redirect(url_for('home'))

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

# ==== GIỎ HÀNG: TĂNG / GIẢM / XÓA ====
@app.route('/increase/<int:product_id>')
def increase(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    user = session['user']
    session['carts'][user].append(product_id)
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    user = session['user']
    try:
        session['carts'][user].remove(product_id)
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

        users[username] = generate_password_hash(password)
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
            flash("❌ Không tìm thấy tên đăng nhập.")
            return redirect(url_for('login'))

        if not check_password_hash(users[username], password):
            flash("❌ Sai mật khẩu.")
            return redirect(url_for('login'))

        session['user'] = username
        return redirect(url_for('home'))

    return render_template('auth.html', register=False)

# ==== ĐĂNG XUẤT ====
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("👋 Bạn đã đăng xuất.")
    return redirect(url_for('home'))

# ==== CHẠY APP ====
if __name__ == '__main__':
    app.run(debug=True)
