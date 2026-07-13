"""Sample data generator for ShopFlow e-commerce analytics."""

import csv
import json
import os
import random
from datetime import date, timedelta

from faker import Faker

fake = Faker("en_US")
Faker.seed(42)
random.seed(42)

REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = {
    "Electronics": ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras"],
    "Clothing": ["T-Shirts", "Pants", "Jackets", "Shoes", "Accessories"],
    "Home": ["Kitchen", "Bathroom", "Living Room", "Garden", "Cleaning"],
    "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports", "Winter Sports"],
    "Books": ["Non-Fiction", "Novel", "Textbook", "Children", "Guides"],
    "Groceries": ["Beverages", "Snacks", "Organic", "Spices", "Sweets"],
}
BRANDS = [
    "TechPro",
    "StyleWear",
    "HomeComfort",
    "SportElite",
    "BioNature",
    "DigitalPlus",
    "UrbanStyle",
    "KitchenCraft",
    "FitLife",
    "ReadWell",
    "AlpineGear",
    "FreshFoods",
    "SmartHome",
    "TrendMode",
    "GardenJoy",
    "PowerTech",
    "NordicDesign",
    "VitalFit",
    "BookPearl",
    "GourmetArt",
]
PRODUCT_NAMES = {
    "Electronics": {
        "Smartphones": [
            "Premium Smartphone 128GB",
            "Compact Smartphone Pro",
            "Budget Smartphone Lite",
        ],
        "Laptops": ["Business Laptop 15 inch", "Gaming Laptop Pro", "Ultrabook Slim 14"],
        "Tablets": ["Tablet Pro 10 inch", "Mini Tablet 8 inch", "Drawing Tablet XL"],
        "Headphones": [
            "Premium Bluetooth Headphones",
            "In-Ear Sport Headphones",
            "Noise-Cancelling Over-Ear",
        ],
        "Cameras": ["Digital Camera 24MP", "Action Camera 4K", "Instant Camera Retro"],
    },
    "Clothing": {
        "T-Shirts": ["Basic Cotton T-Shirt", "Premium V-Neck Shirt", "Sport Performance Shirt"],
        "Pants": ["Slim Fit Jeans", "Chino Pants Classic", "Jogger Pants Comfort"],
        "Jackets": ["Winter Jacket Thermo", "Light Transition Jacket", "Rain Jacket Outdoor"],
        "Shoes": ["Running Shoes Pro", "Business Leather Shoes", "Sneaker Urban Style"],
        "Accessories": ["Leather Belt Classic", "Wool Beanie Winter", "Sunglasses UV400"],
    },
    "Home": {
        "Kitchen": [
            "Knife Set Stainless 5-piece",
            "Cookware Set Induction",
            "Food Processor Multi",
        ],
        "Bathroom": ["Towel Set Premium", "Soap Dispenser Ceramic", "Bathroom Mirror LED"],
        "Living Room": ["Throw Pillow 2-pack", "Floor Lamp Modern", "Wall Clock Minimalist"],
        "Garden": ["Garden Gloves Set", "Flower Pot Terracotta", "LED Solar Light 4-pack"],
        "Cleaning": ["Vacuum Cleaner Bagless", "Steam Cleaner Compact", "Microfiber Cloth 10-pack"],
    },
    "Sports": {
        "Fitness": ["Dumbbell Set 20kg", "Yoga Mat Premium", "Resistance Bands Set"],
        "Outdoor": ["Hiking Backpack 40L", "Trekking Pole Carbon", "Camping Tent 2 Person"],
        "Team Sports": ["Soccer Training Ball", "Basketball Indoor", "Volleyball Competition"],
        "Water Sports": ["Swim Goggles Pro", "Wetsuit 3mm", "SUP Board Inflatable"],
        "Winter Sports": ["Ski Gloves Thermo", "Snowboard Helmet Safety", "Thermal Underwear Set"],
    },
    "Books": {
        "Non-Fiction": ["History of Europe", "Psychology Basics", "Understanding Economics"],
        "Novel": ["The Last Summer", "Still Waters", "Night Lights"],
        "Textbook": [
            "Python Programming",
            "Data Science Handbook",
            "Mechanical Engineering Basics",
        ],
        "Children": ["Adventure in the Forest", "Little Explorers", "Bedtime Stories"],
        "Guides": ["Healthy Cooking", "Mindfulness Practice", "Mastering Finances"],
    },
    "Groceries": {
        "Beverages": ["Organic Oat Milk 1L", "Smoothie Mix 500ml", "Herbal Tea Blend"],
        "Snacks": ["Nut Mix Premium", "Protein Bar Box", "Dried Fruit Box"],
        "Organic": [
            "Organic Olive Oil Extra",
            "Organic Whole Wheat Flour 1kg",
            "Organic Honey 500g",
        ],
        "Spices": ["Spice Set Asian", "Pepper Mill with Pepper", "Sea Salt Flakes"],
        "Sweets": [
            "Dark Chocolate 85%",
            "Fruit Gummy Bears",
            "Oatmeal Cookies",
        ],
    },
}
COST_RANGES = {
    "Electronics": (20, 500),
    "Clothing": (8, 80),
    "Home": (5, 120),
    "Sports": (10, 150),
    "Books": (5, 40),
    "Groceries": (1, 15),
}


def _random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_customers(filepath, count=2000):
    customers = []
    start = date(2023, 1, 1)
    end = date(2025, 12, 31)
    for i in range(1, count + 1):
        segment = random.choices(["B2C", "B2B"], weights=[70, 30])[0]
        row = {
            "customer_id": f"C{i:04d}",
            "name": fake.name(),
            "email": fake.email(),
            "region": random.choice(REGIONS),
            "city": fake.city(),
            "segment": segment,
            "signup_date": _random_date(start, end).isoformat(),
        }
        customers.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
        writer.writeheader()
        writer.writerows(customers)
    print(f"  customers.csv  -> {len(customers)} rows")
    return customers


def generate_suppliers(filepath, count=50):
    suppliers = []
    country_pool = ["DE"] * 50 + ["AT"] * 15 + ["CH"] * 10 + ["PL"] * 15 + ["CN"] * 10
    for i in range(1, count + 1):
        country = random.choice(country_pool)
        if country in ("DE", "AT", "CH"):
            lead = random.randint(3, 12)
        else:
            lead = random.randint(10, 30)
        row = {
            "supplier_id": f"SUP-{i:02d}",
            "name": fake.company(),
            "country": country,
            "lead_time_days": lead,
            "reliability_rating": round(random.uniform(2.5, 5.0), 1),
        }
        suppliers.append(row)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(suppliers, f, ensure_ascii=False, indent=2)
    print(f"  suppliers.json -> {len(suppliers)} entries")
    return suppliers


def generate_products(filepath, suppliers, count=300):
    products = []
    supplier_ids = [s["supplier_id"] for s in suppliers]
    cat_list = list(CATEGORIES.keys())

    for i in range(1, count + 1):
        category = random.choice(cat_list)
        subcategory = random.choice(CATEGORIES[category])
        names = PRODUCT_NAMES[category][subcategory]
        name = random.choice(names)
        low, high = COST_RANGES[category]
        cost = round(random.uniform(low, high), 2)
        markup = round(random.uniform(1.3, 2.5), 2)
        row = {
            "product_id": f"P{i:03d}",
            "name": name,
            "category": category,
            "subcategory": subcategory,
            "brand": random.choice(BRANDS),
            "supplier_id": random.choice(supplier_ids),
            "cost_price": cost,
            "retail_price": round(cost * markup, 2),
        }
        products.append(row)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"  products.json  -> {len(products)} entries")
    return products


def generate_orders(filepath, customers, products, count=12000):
    orders = []
    customer_ids = [c["customer_id"] for c in customers]
    product_map = {p["product_id"]: p for p in products}
    product_ids = list(product_map.keys())

    cat_weights = {
        "Electronics": 30,
        "Clothing": 25,
        "Home": 15,
        "Sports": 12,
        "Books": 10,
        "Groceries": 8,
    }
    weights = [cat_weights.get(product_map[pid]["category"], 10) for pid in product_ids]

    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    discount_choices = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 10, 10, 10, 15, 20]

    for i in range(1, count + 1):
        pid = random.choices(product_ids, weights=weights)[0]
        retail = product_map[pid]["retail_price"]
        variation = round(retail * random.uniform(0.95, 1.05), 2)
        order_date = _random_date(start, end)
        month = order_date.month
        if month in (11, 12):
            if random.random() < 0.3:
                order_date = _random_date(start, end)
        elif month in (1, 2):
            if random.random() < 0.4:
                order_date = _random_date(date(order_date.year, 3, 1), end)

        qty_choices = [1] * 40 + [2] * 30 + [3] * 15 + list(range(4, 11))
        row = {
            "order_id": f"ORD-{i:05d}",
            "customer_id": random.choice(customer_ids),
            "product_id": pid,
            "quantity": random.choice(qty_choices),
            "unit_price": variation,
            "discount_pct": random.choice(discount_choices),
            "order_date": order_date.isoformat(),
            "status": random.choices(["completed", "pending", "cancelled"], weights=[85, 10, 5])[0],
        }
        orders.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(orders[0].keys()))
        writer.writeheader()
        writer.writerows(orders)
    print(f"  orders.csv     -> {len(orders)} rows")
    return orders


def generate_returns(filepath, orders):
    returns = []
    completed = [o for o in orders if o["status"] == "completed"]
    sample_size = int(len(completed) * 0.10)
    returned_orders = random.sample(completed, sample_size)

    reasons = (
        ["Nicht gefallen"] * 35
        + ["Falsche Groesse"] * 25
        + ["Defekt"] * 20
        + ["Falsch geliefert"] * 15
        + ["Sonstiges"] * 5
    )

    for idx, order in enumerate(returned_orders, start=1):
        odate = date.fromisoformat(order["order_date"])
        rdate = odate + timedelta(days=random.randint(5, 30))
        row = {
            "return_id": f"RET-{idx:04d}",
            "order_id": order["order_id"],
            "return_date": rdate.isoformat(),
            "reason": random.choice(reasons),
        }
        returns.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(returns[0].keys()))
        writer.writeheader()
        writer.writerows(returns)
    print(f"  returns.csv    -> {len(returns)} rows")
    return returns


def generate_shipping(filepath, orders):
    shipping = []
    carrier_pool = ["DHL"] * 40 + ["DPD"] * 25 + ["Hermes"] * 20 + ["GLS"] * 15
    base_costs = {"DHL": 4.99, "DPD": 4.49, "Hermes": 3.99, "GLS": 5.49}

    non_cancelled = [o for o in orders if o["status"] != "cancelled"]
    for order in non_cancelled:
        odate = date.fromisoformat(order["order_date"])
        carrier = random.choice(carrier_pool)
        shipped = odate + timedelta(days=random.randint(1, 3))
        if random.random() < 0.08:
            delivered = shipped + timedelta(days=random.randint(8, 14))
        else:
            delivered = shipped + timedelta(days=random.randint(2, 7))

        order_value = order["unit_price"] * order["quantity"]
        base = base_costs[carrier]
        if order_value > 100:
            cost = round(base + random.uniform(2.0, 8.0), 2)
        else:
            cost = round(base + random.uniform(0.0, 3.0), 2)
        cost = min(cost, 12.99)

        row = {
            "order_id": order["order_id"],
            "carrier": carrier,
            "shipped_date": shipped.isoformat(),
            "delivered_date": delivered.isoformat(),
            "shipping_cost": cost,
        }
        shipping.append(row)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(shipping, f, ensure_ascii=False, indent=2)
    print(f"  shipping_events.json -> {len(shipping)} entries")
    return shipping


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
    os.makedirs(data_dir, exist_ok=True)

    print("Generating sample data...")
    customers = generate_customers(os.path.join(data_dir, "customers.csv"))
    suppliers = generate_suppliers(os.path.join(data_dir, "suppliers.json"))
    products = generate_products(os.path.join(data_dir, "products.json"), suppliers)
    orders = generate_orders(os.path.join(data_dir, "orders.csv"), customers, products)
    generate_returns(os.path.join(data_dir, "returns.csv"), orders)
    generate_shipping(os.path.join(data_dir, "shipping_events.json"), orders)
    print(f"Done. Generated data in {data_dir}/")
