document.addEventListener('DOMContentLoaded', () => {
    handleFlashMessages();
    setupAddToCartButtons();
    autoSlideBanner();
});

// ⚡ Flash Message tự ẩn
function handleFlashMessages() {
    const flashContainer = document.querySelector('.bottom-flash-container');
    if (!flashContainer) return;

    const flashes = flashContainer.querySelectorAll('.bottom-flash');
    flashes.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(30px)';
            msg.addEventListener('transitionend', () => msg.remove());
        }, 2000);
    });
}

// 🛒 Xử lý nút "Thêm vào giỏ hàng"
function setupAddToCartButtons() {
    const buttons = document.querySelectorAll('.add-to-cart-btn');
    const cartBadge = document.querySelector('.cart-badge');
    const toast = document.getElementById('toast');

    buttons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            const productId = button.dataset.productId;
            if (!productId) return;

            try {
                const res = await fetch(`/add-to-cart/${productId}`);
                const data = await res.json();

                if (data.success) {
                    updateCartBadge(cartBadge, data.cart_count);
                    showToast(toast);
                } else {
                    alert(data.message || "Đã có lỗi xảy ra.");
                    if (data.message === "Bạn chưa đăng nhập") {
                        window.location.href = '/login';
                    }
                }
            } catch (err) {
                console.error("Lỗi khi thêm giỏ hàng:", err);
                alert("Không thể thêm sản phẩm vào giỏ.");
            }
        });
    });
}

// 🔄 Cập nhật số lượng hiển thị ở giỏ hàng
function updateCartBadge(badge, count) {
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'block' : 'none';
    if (badge.classList.contains('hidden')) {
        badge.classList.remove('hidden');
    }
}


// 🔔 Hiện toast thông báo
function showToast(toast) {
    if (!toast) return;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

// 🖼️ Tự động chuyển slide banner
function autoSlideBanner() {
    const slides = document.querySelectorAll('.big-slide');
    if (slides.length === 0) return;

    let current = 0;

    setInterval(() => {
        slides.forEach((slide, index) => {
            slide.classList.toggle('active', index === current);
        });
        current = (current + 1) % slides.length;
    }, 3000);
}
