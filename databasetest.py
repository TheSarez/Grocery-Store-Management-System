import os
import pyodbc as odbc
import customtkinter as ctk
from tkinter import messagebox, ttk


SERVER = os.getenv("DB_SERVER", "LAPTOP-3BI5GIVH\\MSSQLSERVER01")
DATABASE = os.getenv("DB_NAME", "GROCERY")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_connection():
    try:
        return odbc.connect(
            f'Driver={{ODBC Driver 17 for SQL Server}};'
            f'Server={SERVER};'
            f'Database={DATABASE};'
            'TrustServerCertificate=yes;'
            'Trusted_Connection=yes;'
        )
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to connect: {e}")
        return None

# Predefined Categories and Units
CATEGORIES = [
    "Fresh Produce", "Dairy & Eggs", "Meat & Seafood", "Bakery & Breads",
    "Beverages", "Pantry Staples", "Frozen Foods", "Snacks & Sweets",
    "Household Essentials", "Health & Personal Care"
]

UNITS = ["Piece", "Dozen", "Kg"]

# Fetch Data
def fetch_data(query, params=()):
    conn = get_connection()
    if not conn:
        return [], []

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return columns, rows
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching data: {e}")
        return [], []
    finally:
        conn.close()

# Execute Queries (INSERT, UPDATE, DELETE)
def execute_query(query, params=()):
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Database Error", f"Query execution failed: {e}")
        return False
    finally:
        conn.close()

# Create TreeView Table
def create_treeview(parent, columns):
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 14), rowheight=30)
    style.configure("Treeview.Heading", font=("Arial", 16, "bold"))

    tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor='center')

    tree.pack(fill="both", expand=True, padx=10, pady=10)
    return tree

# Load Data into TreeView
def load_data(tree, query, params=()):
    columns, rows = fetch_data(query, params)

    if not columns:
        return

    # Set columns only once
    if not tree["columns"]:
        tree["columns"] = columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')

    # Clear existing rows
    tree.delete(*tree.get_children())

    # Insert updated rows with formatted values
    for row in rows:
        formatted_row = tuple(str(item) for item in row)  # Ensure clean string values
        tree.insert("", "end", values=formatted_row)

# Main Application
class App:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Department Store Management")
        self.window.geometry(f"{self.window.winfo_screenwidth()}x{self.window.winfo_screenheight()}+0+0")

        ctk.CTkLabel(self.window, text="🛒 Department Store Management", font=("Arial", 30, "bold")).pack(pady=20)

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=30, pady=20)

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 16, "bold"), padding=[20, 10])

        self.create_product_tab(notebook)
        self.create_employee_tab(notebook)

        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(button_frame, text="Exit", font=("Arial", 16, "bold"), command=self.window.destroy).pack(side="right", padx=20, pady=10)

        self.window.mainloop()

    # Product Tab
    def create_product_tab(self, notebook):
        frame = ctk.CTkFrame(notebook)
        notebook.add(frame, text="📦 Products")

        # Search Bar
        search_frame = ctk.CTkFrame(frame)
        search_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(search_frame, text="Search Product:", font=("Arial", 14)).pack(side="left", padx=10)
        search_var = ctk.StringVar()  # Variable to store search query
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, width=300)
        search_entry.pack(side="left", padx=10)

        def search_products():
            search_query = search_var.get().strip()
            if search_query:
                # Ensure ProductID is part of the search result
                query = f"SELECT ProductID, ProductName, Category, Price, StockQuantity, Unit FROM Products WHERE ProductName LIKE ? OR Category LIKE ?"
                like_query = f"%{search_query}%"
                load_data(self.product_tree, query, (like_query, like_query))
            else:
                self.load_products()

        ctk.CTkButton(search_frame, text="Search", command=search_products).pack(side="left", padx=10)
        ctk.CTkButton(search_frame, text="Reset", command=self.load_products).pack(side="left", padx=10)

        # Product TreeView
        self.product_tree = create_treeview(frame, [])
        self.load_products()

        # CRUD Buttons
        self.create_crud_buttons(
            frame, self.product_tree, self.load_products, "Products",
            "ProductID", ["ProductName", "Category", "Price", "StockQuantity", "Unit"]
        )
    # Employee Tab
    def create_employee_tab(self, notebook):
        frame = ctk.CTkFrame(notebook)
        notebook.add(frame, text="👥 Employees")
        self.employee_tree = create_treeview(frame, [])
        self.load_employees()
        self.create_crud_buttons(frame, self.employee_tree, self.load_employees, "Employees",
                                 "EmployeeID", ["EmployeeName", "JobTitle", "HireDate", "Email", "Salary"])

    # CRUD Buttons
    def create_crud_buttons(self, frame, tree, reload_data_func, table_name, id_column, columns):
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", pady=10)

        # Entry variables and widgets
        entry_vars = {col: ctk.StringVar() for col in columns}
        entry_widgets = {}

        for col in columns:
            label = ctk.CTkLabel(button_frame, text=col, font=("Arial", 14))
            label.pack(side="left", padx=5)

            # Use dropdowns for Category and Unit fields
            if col == "Category":
                entry = ctk.CTkComboBox(button_frame, values=CATEGORIES, variable=entry_vars[col], width=150)
                entry.set(CATEGORIES[0])  # Default selection
            elif col == "Unit":
                entry = ctk.CTkComboBox(button_frame, values=UNITS, variable=entry_vars[col], width=100)
                entry.set(UNITS[0])  # Default selection
            else:
                entry = ctk.CTkEntry(button_frame, textvariable=entry_vars[col], width=150)

            entry.pack(side="left", padx=5)
            entry_widgets[col] = entry

        # Add New Data
        def add_data():
            values = [entry_vars[col].get() for col in columns]

            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in values])})"
            if execute_query(query, values):
                reload_data_func()

        # Modify Selected Data
        def modify_data():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a record to modify.")
                return

            item_values = tree.item(selected_item[0])['values']
            if not item_values:
                return

            record_id = item_values[0]  # Ensure this corresponds to ProductID
            values = {col: entry_vars[col].get().strip() for col in columns}

            # Build the UPDATE query
            update_clauses = []
            params = []
            for col, val in values.items():
                if val:  # Only include non-empty fields
                    update_clauses.append(f"{col} = ?")
                    params.append(val)

            if not update_clauses:
                messagebox.showwarning("Warning", "No changes detected.")
                return

            params.append(record_id)
            query = f"UPDATE {table_name} SET {', '.join(update_clauses)} WHERE {id_column} = ?"

            if execute_query(query, params):
                reload_data_func()

        # Delete Selected Data
        def delete_data():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a record to delete.")
                return

            record_id = tree.item(selected_item[0])['values'][0]
            query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            if execute_query(query, [record_id]):
                reload_data_func()

        # Buttons
        ctk.CTkButton(button_frame, text="Add", command=add_data).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Modify", command=modify_data).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Delete", command=delete_data).pack(side="left", padx=5)

    # Load Data
    def load_products(self):
        load_data(self.product_tree, 'SELECT * FROM Products')

    def load_employees(self):
        load_data(self.employee_tree, 'SELECT * FROM Employees')

if __name__ == "__main__":
    App()