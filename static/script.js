
const $ = id => document.getElementById(id);

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}

function showMessage(message) {
    $("message").textContent = message;
}

// Display products
async function loadProducts() {
    try {
        const q = encodeURIComponent($("search").value);
        const products = await api(`/api/products?q=${q}`);

        $("products").innerHTML = products.length
            ? products.map(p => `
                <div class="card">
                    <div class="emoji">${p.emoji}</div>
                    <h3>${p.name}</h3>
                    <p>${p.category}</p>
                    <p>Price: ₹${p.price}</p>
                    <p>Stock: ${p.stock}</p>
                    <button onclick="addCart('${p.id}')"
                        ${p.stock < 1 ? "disabled" : ""}>
                        Add to Cart
                    </button>
                </div>
            `).join("")
            : "<p>No products found.</p>";
    } catch (e) {
        showMessage(e.message);
    }
}

// Add product to cart
async function addCart(pid) {
    try {
        await api("/api/cart", {
            method: "POST",
            body: JSON.stringify({
                productId: pid,
                quantity: 1
            })
        });

        showMessage("Product added to cart!");
        await loadCart();
    } catch (e) {
        showMessage(e.message);
    }
}

// Display cart
async function loadCart() {
    try {
        const cart = await api("/api/cart");

        $("count").textContent = cart.items.reduce(
            (sum, item) => sum + item.quantity, 0
        );
        $("total").textContent = cart.total;
        $("checkout").disabled = cart.items.length === 0;

        $("cart-items").innerHTML = cart.items.length
            ? cart.items.map(item => `
                <div class="cart-item">
                    <span>${item.emoji} ${item.name}
                    (₹${item.price})</span>
                    <span>
                        <button onclick="changeQty(
                            '${item.productId}', ${item.quantity - 1})">−</button>
                        ${item.quantity}
                        <button onclick="changeQty(
                            '${item.productId}', ${item.quantity + 1})">+</button>
                        <button onclick="removeItem(
                            '${item.productId}')">Remove</button>
                    </span>
                </div>
            `).join("")
            : "<p>Your cart is empty.</p>";
    } catch (e) {
        showMessage(e.message);
    }
}

// Update quantity
async function changeQty(pid, quantity) {
    try {
        await api(`/api/cart/${pid}`, {
            method: "PATCH",
            body: JSON.stringify({ quantity })
        });
        await loadCart();
    } catch (e) {
        showMessage(e.message);
    }
}

// Remove item
async function removeItem(pid) {
    try {
        await api(`/api/cart/${pid}`, {
            method: "DELETE"
        });
        await loadCart();
    } catch (e) {
        showMessage(e.message);
    }
}

// Place order
async function placeOrder() {
    try {
        const order = await api("/api/orders", {
            method: "POST",
            body: JSON.stringify({})
        });

        $("order-id").value = order.orderId;
        $("tracking").textContent =
            `Order ${order.orderId}: ${order.status}`;

        showMessage("Order placed successfully!");

        await loadCart();
        await loadProducts();
        await trackOrder();
    } catch (e) {
        showMessage(e.message);
    }
}

// Track order
async function trackOrder() {
    const id = $("order-id").value.trim();

    if (!id) {
        $("tracking").textContent = "Enter an order ID.";
        return;
    }

    try {
        const order = await api(
            `/api/orders/${encodeURIComponent(id)}`
        );

        $("tracking").innerHTML = `
            <strong>Order ID:</strong> ${order.orderId}<br>
            <strong>Status:</strong> ${order.status}<br>
            <strong>Delivery:</strong> ${order.deliveryPartner}<br>
            <strong>Items:</strong><br>
            ${order.items.map(i =>
                `${i.name} × ${i.quantity} = ₹${i.subtotal}`
            ).join("<br>")}<br>
            <strong>Total: ₹${order.total}</strong>
        `;
    } catch (e) {
        $("tracking").textContent = e.message;
    }
}

// Search while typing
$("search").addEventListener("input", loadProducts);

// Initial display
loadProducts();
loadCart();
