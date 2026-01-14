import os
import json
import re
import logging
from flask import Flask, render_template, url_for, session, request, redirect, jsonify
from dotenv import load_dotenv
load_dotenv()


# ------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# ------------------------------
# CONFIGURACIÓN DE LA APP
# Secret key segura desde variable de entorno
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

# Logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------
# FUNCIONES AUXILIARES
# ------------------------------
def is_valid_string(s):
    """Valida que la cadena solo tenga letras, números o guiones bajos"""
    pattern = r'^[\w]+$'
    return bool(re.match(pattern, s))

def load_products():
    """Carga productos desde JSON"""
    with open("static/data/products.json", "r") as f:
        return json.load(f)

# ------------------------------
# RUTAS
# ------------------------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/shop")
def shop():
    products = load_products()
    return render_template("shop.html", products=products)

@app.route("/apparel")
def apparel():
    products = load_products()
    return render_template("apparel.html", products=products)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/cart")
def cart():
    products = load_products()
    cart_items_dict = {}
    total = 0

    if "cart" in session:
        for item_id in session["cart"]:
            prod = next((p for p in products if p["id"] == item_id), None)
            if prod:
                price = float(prod["price"].replace("$", ""))
                if item_id not in cart_items_dict:
                    cart_items_dict[item_id] = {
                        "id": prod["id"],
                        "name": prod["name"],
                        "img": url_for("static", filename=prod["imgs"][0]),
                        "quantity": 1,
                        "unit_price": price,
                        "subtotal": price
                    }
                else:
                    cart_items_dict[item_id]["quantity"] += 1
                    cart_items_dict[item_id]["subtotal"] += price
                total += price

    cart_items = list(cart_items_dict.values())
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity", 1))
    except:
        return jsonify({"error": "Invalid data"}), 400

    if "cart" not in session:
        session["cart"] = []

    for _ in range(quantity):
        session["cart"].append(product_id)

    session.modified = True
    return jsonify({"total_items": len(session["cart"])})

@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    if "cart" in session:
        session["cart"] = [pid for pid in session["cart"] if pid != product_id]
        session.modified = True
    return redirect(url_for("cart"))

@app.route("/update_cart", methods=["POST"])
def update_cart():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity"))
    except:
        return jsonify({"error": "Invalid data"}), 400

    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1"}), 400

    if "cart" not in session:
        session["cart"] = []

    session["cart"] = [pid for pid in session["cart"] if pid != product_id]
    for _ in range(quantity):
        session["cart"].append(product_id)

    session.modified = True
    return jsonify({"success": True, "total_items": len(session["cart"])})

@app.route("/payment")
def payment():
    products = load_products()
    cart_items = []

    if "cart" in session:
        for pid in session["cart"]:
            prod = next((p for p in products if p["id"] == pid), None)
            if prod:
                cart_items.append({
                    "name": prod["name"],
                    "quantity": 1,
                    "unit_price": float(prod["price"].replace("$", ""))
                })

    total = sum(item["quantity"] * item["unit_price"] for item in cart_items)

    logger.info("Cart loaded for payment: %s", cart_items)
    logger.info("Total: $%.2f", total)

    return render_template("register1.html", cart_items=cart_items, total=total)

@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    if "cart" not in session or not session["cart"]:
        logger.warning("Payment attempted with empty cart")
        return jsonify({"error": "Empty cart"}), 400

    products = load_products()
    cart_items_details = []
    total_amount = 0

    for pid in session["cart"]:
        prod = next((p for p in products if p["id"] == pid), None)
        if prod:
            item_data = {
                "id": prod["id"],
                "name": prod["name"],
                "unit_price": float(prod["price"].replace("$", "")),
                "quantity": 1,
                "subtotal": float(prod["price"].replace("$", ""))
            }
            cart_items_details.append(item_data)
            total_amount += item_data["subtotal"]

    session.pop("cart", None)  # Vaciar carrito tras pago

    return jsonify({
        "message": "Simulated payment approved",
        "total_amount": total_amount,
        "cart": cart_items_details
    })

@app.route('/submit', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return "No JSON received", 400

    buyer_id = data.get('buyer_billing_id')
    product = data.get('chosen_product')
    address = data.get('shipping_address')
    contact_method = data.get('contact_method')
    contact_info = data.get('contact_info')

    logger.info("BUYER: %s", buyer_id)
    logger.info("ADDRESS: %s", address)
    logger.info("CONTACT: %s %s", contact_method, contact_info)
    logger.info("PRODUCTS IN CART: %s", product)

    return render_template("ok.html"), 200

if __name__ == "__main__":
    app.run(debug=True)  # solo para desarrollo

