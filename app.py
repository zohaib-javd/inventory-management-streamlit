import streamlit as st
from abc import ABC, abstractmethod
from datetime import datetime, date
import json


# --- Product and Subclasses ---
class Product(ABC):
    def __init__(self, product_id, name, price, quantity_in_stock):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._quantity_in_stock = quantity_in_stock

    def restock(self, amount):
        self._quantity_in_stock += amount
        return f"Restocked {amount} units of '{self._name}'. Current stock: {self._quantity_in_stock}."

    def sell(self, quantity):
        if quantity > self._quantity_in_stock:
            raise ValueError(
                f"Only {self._quantity_in_stock} units of '{self._name}' in stock. Cannot sell {quantity}."
            )
        self._quantity_in_stock -= quantity
        return f"Sold {quantity} units of '{self._name}'."

    def get_total_value(self):
        return self._price * self._quantity_in_stock

    def get_id(self):
        return self._product_id

    def get_name(self):
        return self._name

    @abstractmethod
    def __str__(self):
        pass

    def to_dict(self):
        data = {
            "type": type(self).__name__,
            "product_id": self._product_id,
            "name": self._name,
            "price": self._price,
            "quantity": self._quantity_in_stock,
        }
        return data

    @staticmethod
    def from_dict(data):
        t = data.get("type")
        if t == "Electronics":
            return Electronics(
                data["product_id"],
                data["name"],
                data["price"],
                data["quantity"],
                data.get("warranty_years"),
                data.get("brand"),
            )
        if t == "Grocery":
            return Grocery(
                data["product_id"],
                data["name"],
                data["price"],
                data["quantity"],
                data.get("expiry_date"),
            )
        if t == "Clothing":
            return Clothing(
                data["product_id"],
                data["name"],
                data["price"],
                data["quantity"],
                data.get("size"),
                data.get("material"),
            )
        raise ValueError(f"Unknown product type: {t}")


class Electronics(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, warranty_years, brand):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.warranty_years = warranty_years
        self.brand = brand

    def __str__(self):
        return f"[Electronics] {self._name} ({self.brand}) - Rs{self._price}, Qty: {self._quantity_in_stock}, Warranty: {self.warranty_years}y"

    def to_dict(self):
        data = super().to_dict()
        data.update({"warranty_years": self.warranty_years, "brand": self.brand})
        return data


class Grocery(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, expiry_date):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.expiry_date = (
            datetime.strptime(expiry_date, "%Y-%m-%d").date()
            if isinstance(expiry_date, str)
            else expiry_date
        )

    def is_expired(self):
        return self.expiry_date < date.today()

    def __str__(self):
        status = "Expired" if self.is_expired() else "Fresh"
        return f"[Grocery] {self._name} - Rs{self._price}, Qty: {self._quantity_in_stock}, Expiry: {self.expiry_date} ({status})"

    def to_dict(self):
        data = super().to_dict()
        data.update({"expiry_date": self.expiry_date.isoformat()})
        return data


class Clothing(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, size, material):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.size = size
        self.material = material

    def __str__(self):
        return f"[Clothing] {self._name} - Rs{self._price}, Qty: {self._quantity_in_stock}, Size: {self.size}, Material: {self.material}"

    def to_dict(self):
        data = super().to_dict()
        data.update({"size": self.size, "material": self.material})
        return data


# --- Inventory Class ---
class Inventory:
    def __init__(self):
        self._products = {}

    def add_product(self, product):
        if product.get_id() in self._products:
            raise KeyError(f"Product ID '{product.get_id()}' already exists.")
        self._products[product.get_id()] = product

    def remove_product(self, product_id):
        if product_id not in self._products:
            raise KeyError(f"Product ID '{product_id}' not found.")
        del self._products[product_id]

    def search_by_name(self, name):
        return [
            p
            for p in self._products.values()
            if name.lower() in p.get_name().lower()
        ]

    def search_by_type(self, product_type):
        return [
            p
            for p in self._products.values()
            if type(p).__name__.lower() == product_type.lower()
        ]

    def list_all_products(self):
        return list(self._products.values())

    def sell_product(self, product_id, quantity):
        if product_id not in self._products:
            raise KeyError(f"Product ID '{product_id}' not found.")
        return self._products[product_id].sell(quantity)

    def restock_product(self, product_id, quantity):
        if product_id not in self._products:
            raise KeyError(f"Product ID '{product_id}' not found.")
        return self._products[product_id].restock(quantity)

    def total_inventory_value(self):
        return sum(p.get_total_value() for p in self._products.values())

    def remove_expired_products(self):
        removed = []
        for pid, p in list(self._products.items()):
            if isinstance(p, Grocery) and p.is_expired():
                removed.append(p)
                del self._products[pid]
        return removed

    def save_to_file(self, filename):
        data = [p.to_dict() for p in self._products.values()]
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)
        self._products = {
            item["product_id"]: Product.from_dict(item) for item in data
        }


# --- The App ---
def main():
    
    st.set_page_config(page_title="Inventory Management System", page_icon="🛠️")

   
    st.markdown(
        """
        <style>
            .sidebar .sidebar-content {
                width: 100%;
                max-width: 300px;
                position: fixed;
                top: 0;
                left: 0;
                height: 100%;
                overflow-y: auto;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # App Title
    st.title("🛠️ Inventory Management System")

    # Sidebar
    st.sidebar.title("Actions")
    actions = [
        "Add Product",
        "Remove Product",
        "List All Products",
        "Search by Name",
        "Search by Type",
        "Sell Product",
        "Restock Product",
        "Total Inventory Value",
        "Remove Expired Products",
        "Save Inventory",
        "Load Inventory",
    ]
    action = st.sidebar.radio("Select action", actions)

    # Connect with Me section
    with st.sidebar.expander("📲 Connect with me"):
        st.markdown("- [LinkedIn](https://www.linkedin.com/in/zohaib-javd )")
        st.markdown("- [GitHub](https://www.github.com/zohaib-javd )")
        st.markdown("- [Email](mailto:zohaibjaved@gmail.com)")
        st.markdown("- [X (Twitter)](https://x.com/zohaibjaved )")
        st.markdown("- [YouTube](https://www.youtube.com/@Zohaib-Javed )")

    # Special Thanks section
    with st.sidebar.expander("🧑‍🏫 Special thanks to all my teachers"):
        st.markdown("- Sir Zia Khan")
        st.markdown("- Sir Daniyal Nagori")
        st.markdown("- Sir Muhammad Qasim")
        st.markdown("- Sir Ameen Alam")
        st.markdown("- Sir Aneeq Khatri")
        st.markdown("- Sir Okasha Aijaz")
        st.markdown("- Sir Muhammad Osama")
        st.markdown("- Sir Mubashir Ali")
        st.markdown("- Sir Amjad Ali")
        st.markdown("- Sir Naeem Hussain")
        st.markdown("- Sir Fahad Ghouri")
        st.markdown("- Sir Saleem Raza")
        st.markdown("- Sir Shaikh Abdul Sami")
        st.markdown("- Sir Abdullah Arain")

    # Inventory in session state
    if "inv" not in st.session_state:
        st.session_state.inv = Inventory()
    inv = st.session_state.inv

    try:
        # Action Handlers 
        if action == "Add Product":
            ptype = st.selectbox("Product Type", ["Electronics", "Grocery", "Clothing"])
            pid = st.text_input("Product ID")
            name = st.text_input("Name")
            price = st.number_input("Price", min_value=0.0)
            qty = st.number_input("Quantity", min_value=0, step=1)
            if ptype == "Electronics":
                warranty = st.number_input("Warranty (years)", min_value=0, step=1)
                brand = st.text_input("Brand")
            elif ptype == "Grocery":
                expiry = st.date_input("Expiry Date", min_value=date.today())
            elif ptype == "Clothing":
                size = st.text_input("Size")
                material = st.text_input("Material")
            if st.button("Add Product"):
                if not pid or not name:
                    st.error("Product ID and Name are required.")
                else:
                    if ptype == "Electronics":
                        prod = Electronics(pid, name, price, qty, warranty, brand)
                    elif ptype == "Grocery":
                        prod = Grocery(pid, name, price, qty, expiry)
                    else:
                        prod = Clothing(pid, name, price, qty, size, material)
                    inv.add_product(prod)
                    st.success(f"Product '{name}' added.")

        elif action == "Remove Product":
            pid = st.text_input("Product ID to remove")
            if st.button("Remove"):
                inv.remove_product(pid)
                st.success(f"Removed product ID {pid}.")

        elif action == "List All Products":
            products = inv.list_all_products()
            if products:
                for p in products:
                    st.write(str(p))
            else:
                st.info("Inventory is empty.")

        elif action == "Search by Name":
            name = st.text_input("Enter name to search")
            if st.button("Search"):
                results = inv.search_by_name(name)
                if results:
                    for p in results:
                        st.write(str(p))
                else:
                    st.warning("No products found.")

        elif action == "Search by Type":
            ptype = st.selectbox("Enter type to search", ["Electronics", "Grocery", "Clothing"])
            if st.button("Search"):
                results = inv.search_by_type(ptype)
                if results:
                    for p in results:
                        st.write(str(p))
                else:
                    st.warning("No products found.")

        elif action == "Sell Product":
            pid = st.text_input("Product ID to sell")
            qty = st.number_input("Quantity to sell", min_value=1, step=1)
            if st.button("Sell"):
                msg = inv.sell_product(pid, qty)
                st.success(msg)

        elif action == "Restock Product":
            pid = st.text_input("Product ID to restock")
            qty = st.number_input("Quantity to restock", min_value=1, step=1)
            if st.button("Restock"):
                msg = inv.restock_product(pid, qty)
                st.success(msg)

        elif action == "Total Inventory Value":
            total = inv.total_inventory_value()
            st.write(f"**Total Inventory Value:** Rs {total:.2f}")

        elif action == "Remove Expired Products":
            removed = inv.remove_expired_products()
            if removed:
                for p in removed:
                    st.warning(f"Removed expired: {p.get_name()}")
            else:
                st.info("No expired products.")

        elif action == "Save Inventory":
            filename = st.text_input("Filename to save (e.g., inventory.json)")
            if st.button("Save"):
                inv.save_to_file(filename)
                st.success(f"Inventory saved to {filename}.")

        elif action == "Load Inventory":
            filename = st.text_input("Filename to load (e.g., inventory.json)")
            if st.button("Load"):
                inv.load_from_file(filename)
                st.success(f"Inventory loaded from {filename}.")

    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()

# Zohaib Javed
# 2025-05-17