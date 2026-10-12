
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

products = [
    {"id": "P101", "name": "Milk", "category": "Dairy",
     "price": 30, "stock": 20, "emoji": "🥛"},
    {"id": "P102", "name": "Bread", "category": "Bakery",
     "price": 40, "stock": 15, "emoji": "🍞"},
    {"id": "P103", "name": "Apples", "category": "Fruits",
     "price": 120, "stock": 12, "emoji": "🍎"},
    {"id": "P104", "name": "Rice (1 kg)", "category": "Staples",
     "price": 65, "stock": 25, "emoji": "🍚"},
    {"id": "P105", "name": "Eggs (6)", "category": "Eggs",
     "price": 55, "stock": 18, "emoji": "🥚"},
    {"id": "P106", "name": "Tomatoes", "category": "Vegetables",
     "price": 25, "stock": 30, "emoji": "🍅"}
]

cart = {}
orders = {}
next_order = 101


def find_product(pid):
    return next((p for p in products if p["id"] == pid), None)


@app.route("/")
def home():
    return render_template("index.html")


# Search products
@app.route("/api/products")
def search_products():
    q = request.args.get("q", "").lower()
    result = [
        p for p in products
        if q in p["name"].lower()
        or q in p["category"].lower()
    ]
    return jsonify(result)


# View cart
@app.route("/api/cart")
def view_cart():
    items = []
    total = 0

    for pid, qty in cart.items():
        p = find_product(pid)
        if p:
            subtotal = p["price"] * qty
            items.append({
                "productId": pid,
                "name": p["name"],
                "price": p["price"],
                "quantity": qty,
                "subtotal": subtotal,
                "emoji": p["emoji"]
            })
            total += subtotal

    return jsonify({"items": items, "total": total})


# Add product to cart
@app.route("/api/cart", methods=["POST"])
def add_cart():
    data = request.get_json(silent=True) or {}
    pid = data.get("productId")
    qty = data.get("quantity", 1)
    p = find_product(pid)

    if not p:
        return jsonify({"error": "Product not found"}), 404

    if type(qty) is not int or qty < 1:
        return jsonify({"error": "Invalid quantity"}), 400

    if cart.get(pid, 0) + qty > p["stock"]:
        return jsonify({"error": "Insufficient stock"}), 409

    cart[pid] = cart.get(pid, 0) + qty
    return jsonify({"message": "Added to cart"}), 201


# Update cart quantity
@app.route("/api/cart/<pid>", methods=["PATCH"])
def update_cart(pid):
    data = request.get_json(silent=True) or {}
    qty = data.get("quantity")
    p = find_product(pid)

    if not p or pid not in cart:
        return jsonify({"error": "Cart item not found"}), 404

    if type(qty) is not int or qty < 0:
        return jsonify({"error": "Invalid quantity"}), 400

    if qty > p["stock"]:
        return jsonify({"error": "Insufficient stock"}), 409

    if qty == 0:
        cart.pop(pid)
    else:
        cart[pid] = qty

    return view_cart()


# Remove cart item
@app.route("/api/cart/<pid>", methods=["DELETE"])
def remove_cart(pid):
    if pid not in cart:
        return jsonify({"error": "Cart item not found"}), 404

    cart.pop(pid)
    return view_cart()


# Place order
@app.route("/api/orders", methods=["POST"])
def place_order():
    global next_order

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    # Check all stock before changing inventory
    for pid, qty in cart.items():
        p = find_product(pid)
        if not p or qty > p["stock"]:
            return jsonify({"error": "Insufficient stock"}), 409

    items = []
    total = 0

    for pid, qty in cart.items():
        p = find_product(pid)
        subtotal = p["price"] * qty
        total += subtotal
        items.append({
            "productId": pid,
            "name": p["name"],
            "quantity": qty,
            "price": p["price"],
            "subtotal": subtotal
        })

    # Reduce stock after validation
    for pid, qty in cart.items():
        find_product(pid)["stock"] -= qty

    oid = f"O{next_order}"
    next_order += 1

    orders[oid] = {
        "orderId": oid,
        "status": "Order confirmed",
        "deliveryPartner": "QuickCommerce Delivery",
        "items": items,
        "total": total
    }

    cart.clear()
    return jsonify(orders[oid]), 201


# Track order
@app.route("/api/orders/<oid>")
def track_order(oid):
    order = orders.get(oid.upper())

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


if __name__ == "__main__":
    app.run(debug=True)
