"""Sample data generator for ShopFlow e-commerce analytics."""

import csv
import json
import os
import random
from datetime import date, timedelta

from faker import Faker

fake = Faker("de_DE")
Faker.seed(42)
random.seed(42)

REGIONS = ["Nord", "Sued", "Ost", "West", "Mitte"]
CATEGORIES = {
    "Elektronik": ["Smartphones", "Laptops", "Tablets", "Kopfhoerer", "Kameras"],
    "Kleidung": ["T-Shirts", "Hosen", "Jacken", "Schuhe", "Accessoires"],
    "Haushalt": ["Kuechen", "Badezimmer", "Wohnzimmer", "Garten", "Reinigung"],
    "Sport": ["Fitness", "Outdoor", "Teamsport", "Wassersport", "Wintersport"],
    "Buecher": ["Sachbuch", "Roman", "Fachbuch", "Kinderbuch", "Ratgeber"],
    "Lebensmittel": ["Getraenke", "Snacks", "Bio", "Gewuerze", "Suessigkeiten"],
}
BRANDS = [
    "TechPro",
    "StyleWear",
    "HomeComfort",
    "SportElite",
    "BioNatur",
    "DigitalPlus",
    "UrbanStyle",
    "KuechenKraft",
    "FitLife",
    "LeseWelt",
    "AlpinGear",
    "FreshFoods",
    "SmartHome",
    "ModeTrend",
    "GartenGlueck",
    "PowerTech",
    "NordDesign",
    "VitalFit",
    "BuchPerle",
    "GenussArt",
]
PRODUCT_NAMES = {
    "Elektronik": {
        "Smartphones": [
            "Premium Smartphone 128GB",
            "Kompakt Smartphone Pro",
            "Budget Smartphone Lite",
        ],
        "Laptops": ["Business Laptop 15 Zoll", "Gaming Laptop Pro", "Ultrabook Slim 14"],
        "Tablets": ["Tablet Pro 10 Zoll", "Mini Tablet 8 Zoll", "Zeichentablet XL"],
        "Kopfhoerer": [
            "Premium Bluetooth Kopfhoerer",
            "In-Ear Sport Kopfhoerer",
            "Noise-Cancelling Over-Ear",
        ],
        "Kameras": ["Digitalkamera 24MP", "Action Kamera 4K", "Sofortbildkamera Retro"],
    },
    "Kleidung": {
        "T-Shirts": ["Basic T-Shirt Baumwolle", "Premium V-Neck Shirt", "Sport Funktionsshirt"],
        "Hosen": ["Slim Fit Jeans", "Chino Hose Classic", "Jogginghose Komfort"],
        "Jacken": ["Winterjacke Thermo", "Leichte Uebergangsjacke", "Regenjacke Outdoor"],
        "Schuhe": ["Laufschuhe Pro", "Business Lederschuhe", "Sneaker Urban Style"],
        "Accessoires": ["Lederguertel Classic", "Wollmuetze Winter", "Sonnenbrille UV400"],
    },
    "Haushalt": {
        "Kuechen": [
            "Messerset Edelstahl 5-teilig",
            "Kochtoepfe Set Induktion",
            "Kuechenmaschine Multi",
        ],
        "Badezimmer": ["Handtuch Set Premium", "Seifenspender Keramik", "Badezimmerspiegel LED"],
        "Wohnzimmer": ["Dekokissen 2er Set", "Stehlampe Modern", "Wanduhr Minimalist"],
        "Garten": ["Gartenhandschuhe Set", "Blumentopf Terrakotta", "LED Solarleuchte 4er"],
        "Reinigung": ["Staubsauger Beutellos", "Dampfreiniger Kompakt", "Mikrofasertuch 10er Pack"],
    },
    "Sport": {
        "Fitness": ["Kurzhantel Set 20kg", "Yogamatte Premium", "Widerstandsbaender Set"],
        "Outdoor": ["Wanderrucksack 40L", "Trekkingstock Carbon", "Campingzelt 2 Personen"],
        "Teamsport": ["Fussball Trainingsball", "Basketball Indoor", "Volleyball Wettkampf"],
        "Wassersport": ["Schwimmbrille Profi", "Neoprenanzug 3mm", "SUP Board Aufblasbar"],
        "Wintersport": ["Skihandschuhe Thermo", "Snowboardhelm Safety", "Thermounterwaesche Set"],
    },
    "Buecher": {
        "Sachbuch": ["Geschichte Europas", "Psychologie Grundlagen", "Wirtschaft Verstehen"],
        "Roman": ["Der Letzte Sommer", "Stille Wasser", "Nachtlichter"],
        "Fachbuch": ["Python Programmierung", "Data Science Handbuch", "Maschinenbau Basics"],
        "Kinderbuch": ["Abenteuer im Wald", "Kleine Entdecker", "Gute Nacht Geschichten"],
        "Ratgeber": ["Gesund Kochen", "Achtsamkeit Praxis", "Finanzen Meistern"],
    },
    "Lebensmittel": {
        "Getraenke": ["Bio Hafermilch 1L", "Smoothie Mix 500ml", "Kraeutertee Mischung"],
        "Snacks": ["Nussmischung Premium", "Proteinriegel Box", "Trockenfruechtebox"],
        "Bio": ["Bio Olivenoel Extra", "Bio Vollkornmehl 1kg", "Bio Honig 500g"],
        "Gewuerze": ["Gewuerzset Asiatisch", "Pfeffermuehle mit Pfeffer", "Meersalz Flocken"],
        "Suessigkeiten": [
            "Schokolade Edelbitter 85%",
            "Gummibaerchen Fruchtmix",
            "Kekse Haferflocken",
        ],
    },
}
COST_RANGES = {
    "Elektronik": (20, 500),
    "Kleidung": (8, 80),
    "Haushalt": (5, 120),
    "Sport": (10, 150),
    "Buecher": (5, 40),
    "Lebensmittel": (1, 15),
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
        "Elektronik": 30,
        "Kleidung": 25,
        "Haushalt": 15,
        "Sport": 12,
        "Buecher": 10,
        "Lebensmittel": 8,
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
