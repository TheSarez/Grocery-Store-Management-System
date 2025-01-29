import os
import pyodbc as odbc
import customtkinter as ctk
from tkinter import messagebox, ttk

# Database Configuration
SERVER = os.getenv("DB_SERVER", "LAPTOP-3BI5GIVH\\MSSQLSERVER01")
DATABASE = os.getenv("DB_NAME", "GROCERY")

# UI Settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Database Connection
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

# Fetch Data
def fetch_data(query):
    conn = get_connection()
    if not conn:
        return [], []

    try:
        cursor = conn.cursor()
        cursor.execute(query)
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
def load_data(tree, query):
    columns, rows = fetch_data(query)
    tree["columns"] = columns
    tree.delete(*tree.get_children())

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor='center')

    for row in rows:
        tree.insert("", "end", values=row)

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
        self.create_sales_tab(notebook)

        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(button_frame, text="Exit", font=("Arial", 16, "bold"), command=self.window.destroy).pack(side="right", padx=20, pady=10)

        self.window.mainloop()

    # Product Tab
    def create_product_tab(self, notebook):
        frame = ctk.CTkFrame(notebook)
        notebook.add(frame, text="📦 Products")
        self.product_tree = create_treeview(frame, [])
        self.load_products()
        self.create_crud_buttons(frame, self.product_tree, self.load_products, "Products",
                                 "ProductID", ["ProductName", "Category", "Price", "StockQuantity"])

    # Employee Tab
    def create_employee_tab(self, notebook):
        frame = ctk.CTkFrame(notebook)
        notebook.add(frame, text="👥 Employees")
        self.employee_tree = create_treeview(frame, [])
        self.load_employees()
        self.create_crud_buttons(frame, self.employee_tree, self.load_employees, "Employees",
                                 "EmployeeID", ["EmployeeName", "JobTitle", "HireDate", "Email", "Salary"])

    # Sales Tab
    def create_sales_tab(self, notebook):
        frame = ctk.CTkFrame(notebook)
        notebook.add(frame, text="💰 Sales")
        self.sales_tree = create_treeview(frame, [])
        self.load_sales()
        self.create_crud_buttons(frame, self.sales_tree, self.load_sales, "Sales",
                                 "SaleID", ["EmployeeID", "CustomerName", "SaleDate", "TotalAmount"])

    # CRUD Buttons
    def create_crud_buttons(self, frame, tree, reload_data_func, table_name, id_column, columns):
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", pady=10)

        entry_vars = {col: ctk.StringVar() for col in columns}
        entry_widgets = {}

        for col in columns:
            label = ctk.CTkLabel(button_frame, text=col, font=("Arial", 14))
            label.pack(side="left", padx=5)
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

            record_id = item_values[0]
            values = [entry_vars[col].get() for col in columns]
            query = f"UPDATE {table_name} SET {', '.join([f'{col} = ?' for col in columns])} WHERE {id_column} = ?"
            if execute_query(query, values + [record_id]):
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

    def load_sales(self):
        load_data(self.sales_tree, 'SELECT * FROM Sales')

# Run App
if __name__ == "__main__":
    App()
