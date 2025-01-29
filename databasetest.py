import pyodbc as odbc
import customtkinter as ctk
from tkinter import messagebox, ttk

# Global connection and cursor to avoid redundancy
def get_connection():
    return odbc.connect(
        'Driver={ODBC Driver 17 for SQL Server};'
        'Server=LAPTOP-3BI5GIVH\\MSSQLSERVER01;'
        'Database=GROCERY;'
        'TrustServerCertificate=yes;'
        'Trusted_Connection=yes;'
    )

def fetch_data():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Products')
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        conn.close()
        return columns, rows
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching data: {e}")
        return [], []

def add_row_form(tree, columns):
    def submit():
        # Collect values from entry widgets
        row_values = [entry.get() for entry in entry_widgets]

        if any(value.strip() == "" for value in row_values):
            messagebox.showwarning("Warning", "All fields must be filled!")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Insert data into the table
            placeholders = ', '.join(['?'] * len(row_values))
            sql = f"INSERT INTO Products ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(sql, row_values)
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Row added successfully!")
            popup.destroy()
            refresh_table(tree)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add row: {e}")

    popup = ctk.CTkToplevel()
    popup.title("Add New Row")
    popup.geometry("400x400")

    ctk.CTkLabel(popup, text="Enter values for the new row:", font=("Arial", 14)).pack(pady=10)

    entry_widgets = []
    for column in columns:
        ctk.CTkLabel(popup, text=f"{column}:", font=("Arial", 12)).pack(anchor="w", padx=20)
        entry = ctk.CTkEntry(popup, width=300)
        entry.pack(pady=5)
        entry_widgets.append(entry)

    ctk.CTkButton(popup, text="Submit", command=submit).pack(pady=20)

def refresh_table(tree):
    columns, rows = fetch_data()

    for item in tree.get_children():
        tree.delete(item)

    if rows:
        for row in rows:
            tree.insert("", "end", values=list(row))

def display_data():
    columns, rows = fetch_data()

    if not columns:
        return

    window = ctk.CTk()
    window.title("SQL Table Data")
    window.geometry("800x600")

    ctk.CTkLabel(window, text="Department Store Management", font=("Arial", 18, "bold")).pack(pady=10)

    tree_frame = ctk.CTkFrame(window)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Use ttk.Treeview for displaying data
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
    for column in columns:
        tree.heading(column, text=column)
        tree.column(column, width=120)
    tree.pack(fill="both", expand=True)

    for row in rows:
        tree.insert("", "end", values=list(row))

    button_frame = ctk.CTkFrame(window)
    button_frame.pack(fill="x", padx=20, pady=10)
    ctk.CTkButton(button_frame, text="Add New Row", command=lambda: add_row_form(tree, columns[1:])).pack()

    window.mainloop()

display_data()
