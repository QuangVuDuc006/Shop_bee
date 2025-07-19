# -*- coding: utf-8 -*-

import json
import os
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests


# ==============================================================================
# KHỞI TẠO ỨNG DỤNG FLASK
# ==============================================================================
app = Flask(__name__)
app.secret_key = 'super-secret-key-for-web-ban-hang'


# ==============================================================================
# CÁC BIẾN CẤU HÌNH VÀ HẰNG SỐ
# ==============================================================================
PRODUCTS_FILE = 'products.json'
USERS_FILE = 'users.json'
SHOPS_FILE = 'shops.json'

UPLOAD_FOLDER_MAIN_WEB = os.path.join('static', 'images')
SHOP_AVATAR_FOLDER = os.path.join('static', 'shop_assets')
os.makedirs(UPLOAD_FOLDER_MAIN_WEB, exist_ok=True)
os.makedirs(SHOP_AVATAR_FOLDER, exist_ok=True)

OWNER_INFO = {
    "facebook_link": "https://www.facebook.com/quang.vu.uc.579118",
    "zalo_link": "https://zalo.me/0399109399",
    "website_link": "https://yourglobalwebsite.com"
}

CATEGORIES = [
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

# ==============================================================================
# CÁC HÀM HỖ TRỢ (HELPER FUNCTIONS)
# ==============================================================================

def load_json_data(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default_data # Trả về mặc định nếu file JSON bị lỗi
    return default_data

def save_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users(): return load_json_data(USERS_FILE, {})
def save_users(data): save_json_data(USERS_FILE, data)
def load_shops_data(): return load_json_data(SHOPS_FILE, {})
def save_shops_data(data): save_json_data(SHOPS_FILE, data)
def load_products_raw(): return load_json_data(PRODUCTS_FILE, [])
def save_products(data): save_json_data(PRODUCTS_FILE, data)


def get_product_list():
    """
    Hàm TRUNG TÂM để lấy danh sách sản phẩm.
    Luôn trả về một danh sách các dictionary, bất kể products.json là list hay dict.
    Hàm này sẽ giải quyết tất cả các lỗi AttributeError và TypeError trước đó.
    """
    products_data = load_products_raw()
    if isinstance(products_data, dict):
        return [p for p in products_data.values() if isinstance(p, dict)]
    if isinstance(products_data, list):
        return [p for p in products_data if isinstance(p, dict)]
    return [] # Trả về danh sách rỗng nếu định dạng không hợp lệ

def is_logged_in():
    return 'user' in session

def get_shop_info_by_username(username):
    shops_data = load_shops_data()
    return shops_data.get(username, {
        "shop_name": "Shop không xác định", "hotline": "N/A", "email": "N/A",
        "address": "N/A", "facebook_link": "", "zalo_link": "",
        "website_link": "", "shop_avatar": "default_shop_avatar.png"
    })

def get_current_user_balance():
    if is_logged_in():
        user_info = load_users().get(session['user'], {})
        return user_info.get("balance", 0) if isinstance(user_info, dict) else 0
    return 0

# ==============================================================================
# CONTEXT PROCESSORS
# ==============================================================================

@app.context_processor
def inject_global_data():
    """Cung cấp các biến chung cho tất cả template."""
    cart_count = 0
    if is_logged_in() and 'carts' in session:
        cart_count = len(set(session['carts'].get(session['user'], [])))
    return {
        'global_shop_info': {"shop_name": "Shop Bee"},
        'owner_social_links': OWNER_INFO,
        'cart_count': cart_count,
        'user_balance': get_current_user_balance()
    }

# ==============================================================================
# FRONTEND ROUTES
# ==============================================================================

@app.route('/')
def home():
    """Trang chủ, hiển thị tất cả sản phẩm."""
    all_products = get_product_list() # Sử dụng hàm mới
    all_shops_data = load_shops_data()

    for product in all_products:
        seller_username = product.get("seller_username")
        shop_info = all_shops_data.get(seller_username, {})
        product['shop_name'] = shop_info.get('shop_name', "Shop không xác định")
        product['shop_avatar'] = shop_info.get('shop_avatar', "default_shop_avatar.png")

    return render_template("index.html", products=all_products, categories=CATEGORIES)
def index():
    try:
        response = requests.get("https://shop-bê-admin.onrender.com/api/products")
        products = response.json()
    except Exception as e:
        products = []
    return render_template("index.html", products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Trang chi tiết sản phẩm."""
    product = next((p for p in get_product_list() if p.get("id") == product_id), None)
    if not product:
        flash("Sản phẩm không tồn tại!", "error")
        return redirect(url_for('home'))

    seller_username = product.get("seller_username")
    product['shop_info'] = get_shop_info_by_username(seller_username)
    return render_template("product_detail.html", product=product)

@app.route('/shop_profile/<username>')
def shop_profile(username):
    """Trang thông tin công khai của một shop."""
    shop_info = get_shop_info_by_username(username)
    shop_products = [p for p in get_product_list() if p.get("seller_username") == username]
    return render_template("shop_profile.html", shop_info=shop_info, shop_products=shop_products)

@app.route('/distributors')
def distributors():
    """Trang hiển thị danh sách tất cả nhà phân phối."""
    all_shops = load_shops_data()
    list_of_shops = [{'username': username, **info} for username, info in all_shops.items()]
    return render_template("distributors.html", shops=list_of_shops)

@app.route('/category/<slug>')
def show_category_by_slug(slug):
    """Trang hiển thị sản phẩm theo danh mục."""
    category = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not category:
        return "Không tìm thấy danh mục", 404
    
    filtered_products = [p for p in get_product_list() if p.get("category_slug") == slug]
    return render_template("category.html", category=category, products=filtered_products)

# ==============================================================================
# CART SYSTEM
# ==============================================================================

@app.route('/cart')
def cart():
    """Trang giỏ hàng, xử lý dựa trên SKU của phiên bản."""
    if not is_logged_in():
        flash("Bạn cần đăng nhập để xem giỏ hàng!", "warning")
        return redirect(url_for('login'))

    user = session['user']
    cart_skus = session.get('carts', {}).get(user, [])
    cart_items, total = [], 0
    all_products = get_product_list()

    sku_counts = {sku: cart_skus.count(sku) for sku in set(cart_skus)}

    for sku, quantity in sku_counts.items():
        found_variant = None
        parent_product = None
        # Tìm sản phẩm và phiên bản tương ứng với SKU
        for product in all_products:
            for variant in product.get('variants', []):
                if variant.get('sku') == sku:
                    found_variant = variant
                    parent_product = product
                    break
            if found_variant:
                break
        
        if found_variant and parent_product:
            item = {
                "id": parent_product["id"],
                "sku": sku,
                "name": f"{parent_product['name']} ({', '.join(found_variant['attributes'].values())})",
                "price": found_variant["price"],
                "image": parent_product.get("images", ["default.jpg"])[0],
                "quantity": quantity,
                "subtotal": found_variant["price"] * quantity
            }
            cart_items.append(item)
            total += item["subtotal"]

    return render_template("cart.html", cart=cart_items, total=total)


@app.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    """Thêm một phiên bản sản phẩm (variant) vào giỏ hàng."""
    if not is_logged_in():
        return jsonify({"success": False, "message": "Bạn chưa đăng nhập"}), 401

    data = request.get_json()
    sku = data.get('sku')
    if not sku:
        return jsonify({"success": False, "message": "Thiếu thông tin phiên bản sản phẩm"}), 400

    user = session['user']
    session.setdefault('carts', {}).setdefault(user, [])
    session['carts'][user].append(sku)
    session.modified = True
    
    # Cập nhật số lượng trên icon giỏ hàng
    cart_count = len(set(session['carts'][user]))

    return jsonify({"success": True, "cart_count": cart_count, "message": "Đã thêm vào giỏ hàng!"})
@app.route('/increase/<int:product_id>')
def increase(product_id):
    if is_logged_in():
        session['carts'][session['user']].append(product_id)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease(product_id):
    if is_logged_in() and product_id in session['carts'][session['user']]:
        session['carts'][session['user']].remove(product_id)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove/<sku>')
def remove(sku):
    """Xóa hoàn toàn một loại sản phẩm (dựa trên SKU) khỏi giỏ."""
    if is_logged_in():
        user = session['user']
        # Lọc và giữ lại những sku không trùng với sku cần xóa
        if user in session.get('carts', {}):
            session['carts'][user] = [s for s in session['carts'][user] if s != sku]
            session.modified = True
    return redirect(url_for('cart'))
# ==============================================================================
# AUTHENTICATION
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash("❗ Tài khoản đã tồn tại!", "error")
            return redirect(url_for('register'))
        users[username] = {"password_hash": generate_password_hash(password), "balance": 0}
        save_users(users)
        flash("✅ Đăng ký thành công! Mời bạn đăng nhập.", "success")
        return redirect(url_for('login'))
    return render_template('auth.html', register=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = load_users().get(username)
        if not user_data or not check_password_hash(user_data.get("password_hash", ""), password):
            flash("❌ Tên đăng nhập hoặc mật khẩu không chính xác.", "error")
            return redirect(url_for('login'))
        session['user'] = username
        flash("✅ Đăng nhập thành công!", "success")
        return redirect(url_for('home'))
    return render_template('auth.html', register=False)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("👋 Bạn đã đăng xuất.", "info")
    return redirect(url_for('home'))

# ==============================================================================
# API ENDPOINTS (FOR ADMIN WEB)
# ==============================================================================

@app.route('/api/add_product', methods=['POST'])
def api_add_product():
    """API để thêm sản phẩm mới (hỗ trợ phiên bản)."""
    if not request.is_json: return jsonify({"success": False, "message": "Yêu cầu phải là JSON"}), 400
    data = request.get_json()
    
    required = ['name', 'seller_username', 'variants']
    if not all(field in data for field in required): return jsonify({"success": False, "message": "Thiếu dữ liệu bắt buộc."}), 400
    if not data['variants']: return jsonify({"success": False, "message": "Sản phẩm phải có ít nhất một phiên bản."}), 400
    if not all('price' in v for v in data['variants']): return jsonify({"success": False, "message": "Mỗi phiên bản phải có giá."}), 400

    product_list = get_product_list()
    new_id = max([p['id'] for p in product_list]) + 1 if product_list else 1

    new_product = {
        "id": new_id, "name": data['name'], "description": data.get('description', ''),
        "category_slug": data.get('category_slug', 'khac'), "seller_username": data['seller_username'],
        "images": data.get('images', ['default.jpg']), "options": data.get('options', []),
        "variants": data['variants']
    }
    
    product_list.append(new_product)
    save_products(product_list)
    return jsonify({"success": True, "message": "Thêm sản phẩm thành công!", "product_id": new_id}), 201

@app.route('/api/edit_product/<int:product_id>', methods=['POST'])
def api_edit_product(product_id):
    """API để chỉnh sửa thông tin một sản phẩm (hỗ trợ phiên bản)."""
    if not request.is_json: return jsonify({"success": False, "message": "Yêu cầu phải là JSON"}), 400
    data = request.get_json()
    seller_username = data.get('seller_username')
    if not seller_username: return jsonify({"success": False, "message": "Yêu cầu không hợp lệ"}), 400

    product_list = get_product_list()
    product_index = -1
    for i, p in enumerate(product_list):
        if p.get('id') == product_id:
            if p.get('seller_username') != seller_username:
                return jsonify({"success": False, "message": "Không có quyền chỉnh sửa sản phẩm này"}), 403
            product_index = i
            break
            
    if product_index == -1: return jsonify({"success": False, "message": "Không tìm thấy sản phẩm"}), 404

    # Cập nhật toàn bộ thông tin sản phẩm
    product_list[product_index]["name"] = data.get('name', product_list[product_index]['name'])
    product_list[product_index]["description"] = data.get('description', product_list[product_index]['description'])
    product_list[product_index]["category_slug"] = data.get('category_slug', product_list[product_index]['category_slug'])
    # Logic cập nhật ảnh, options, variants phức tạp hơn, tạm thời chỉ cập nhật thông tin cơ bản
    
    save_products(product_list)
    return jsonify({"success": True, "message": "Cập nhật sản phẩm thành công"})

@app.route('/api/delete_product/<int:product_id>', methods=['POST'])
def api_delete_product(product_id):
    """API để xóa một sản phẩm."""
    if not request.is_json: return jsonify({"success": False, "message": "Yêu cầu phải là JSON"}), 400
    data = request.get_json()
    seller_username = data.get('seller_username')
    if not seller_username: return jsonify({"success": False, "message": "Yêu cầu không hợp lệ"}), 400

    product_list = get_product_list()
    original_length = len(product_list)
    
    product_list_after_delete = [p for p in product_list if not (p.get('id') == product_id and p.get('seller_username') == seller_username)]
    
    if len(product_list_after_delete) == original_length:
        # Kiểm tra xem sản phẩm có tồn tại nhưng không thuộc quyền sở hữu hay không
        product_exists = any(p.get('id') == product_id for p in product_list)
        if product_exists:
            return jsonify({"success": False, "message": "Không có quyền xóa sản phẩm này"}), 403
        else:
            return jsonify({"success": False, "message": "Không tìm thấy sản phẩm"}), 404

    save_products(product_list_after_delete)
    return jsonify({"success": True, "message": "Đã xóa sản phẩm thành công"})

@app.route('/api/upload_product_image', methods=['POST'])
def api_upload_product_image():
    """API để nhận file ảnh sản phẩm."""
    if 'image' not in request.files: return jsonify({"success": False, "message": "Không tìm thấy file ảnh"}), 400
    file = request.files['image']
    if file.filename == '': return jsonify({"success": False, "message": "Chưa chọn file ảnh"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER_MAIN_WEB, filename))
    return jsonify({"success": True, "filename": filename}), 200

@app.route('/api/upload_shop_avatar', methods=['POST'])
def api_upload_shop_avatar():
    """API để nhận file ảnh avatar của shop."""
    if 'shop_avatar' not in request.files: return jsonify({"success": False, "message": "Không tìm thấy file avatar"}), 400
    file = request.files['shop_avatar']
    if file.filename == '': return jsonify({"success": False, "message": "Chưa chọn file avatar"}), 400
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(SHOP_AVATAR_FOLDER, filename))
    return jsonify({"success": True, "filename": filename}), 200

@app.route('/api/update_shop_info', methods=['POST'])
def api_update_shop_info():
    """API để cập nhật thông tin một shop."""
    if not request.is_json: return jsonify({"success": False, "message": "Yêu cầu phải là JSON"}), 400
    data = request.get_json()
    seller_username = data.get('seller_username')
    if not seller_username: return jsonify({"success": False, "message": "Thiếu seller_username"}), 400

    shops_data = load_shops_data()
    current_shop_info = shops_data.get(seller_username, {})
    new_avatar = data.get('shop_avatar')

    if new_avatar and current_shop_info.get('shop_avatar') and new_avatar != current_shop_info.get('shop_avatar'):
        old_avatar_path = os.path.join(SHOP_AVATAR_FOLDER, current_shop_info['shop_avatar'])
        if os.path.exists(old_avatar_path) and current_shop_info['shop_avatar'] != 'default_shop_avatar.png':
            try:
                os.remove(old_avatar_path)
            except OSError as e:
                print(f"Lỗi khi xóa avatar cũ: {e}")

    shops_data[seller_username] = {
        'shop_name': data.get('shop_name', "Tên Shop Mới"), 'hotline': data.get('hotline', ""),
        'email': data.get('email', ""), 'address': data.get('address', ""),
        'facebook_link': data.get('facebook_link', ""), 'zalo_link': data.get('zalo_link', ""),
        'website_link': data.get('website_link', ""),
        'shop_avatar': new_avatar or current_shop_info.get('shop_avatar', 'default_shop_avatar.png')
    }
    save_shops_data(shops_data)
    return jsonify({"success": True, "message": "Thông tin shop đã được cập nhật"})

@app.route('/api/get_products/<seller_username>', methods=['GET'])
def get_products_by_seller(seller_username):
    """API để lấy tất cả sản phẩm của một người bán."""
    seller_products = [p for p in get_product_list() if p.get('seller_username') == seller_username]
    return jsonify(seller_products)

# ==============================================================================
# CHẠY ỨNG DỤNG
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)