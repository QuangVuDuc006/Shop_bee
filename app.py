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
@app.route('/')
def home():
    cart = session.get(f"cart_{session['user']}", []) if is_logged_in() else []
    user = session.get('user')
    return render_template("index.html", products=products, cart=cart, user=user)

# ==== GIỎ HÀNG ====
@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if not is_logged_in():
        flash("Bạn cần đăng nhập để mua hàng!")
        return redirect(url_for('login'))

    username = session['user']
    cart_key = f"cart_{username}"

    if cart_key not in session:
        session[cart_key] = []

    session[cart_key].append(product_id)
    session.modified = True
    return redirect(url_for('home'))


@app.route('/cart')
def cart():
    if not is_logged_in():
        flash("Bạn cần đăng nhập để xem giỏ hàng!")
        return redirect(url_for('login'))

    cart_ids = session.get('cart', [])
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

    if 'cart' not in session:
        return redirect(url_for('cart'))

    session['cart'].append(product_id)
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    if 'cart' not in session:
        return redirect(url_for('cart'))

    try:
        session['cart'].remove(product_id)
        session.modified = True
    except ValueError:
        pass
    return redirect(url_for('cart'))

@app.route('/remove/<int:product_id>')
def remove(product_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    if 'cart' not in session:
        return redirect(url_for('cart'))

    session['cart'] = [pid for pid in session['cart'] if pid != product_id]
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
        #flash("✅ Đăng nhập thành công!")
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
