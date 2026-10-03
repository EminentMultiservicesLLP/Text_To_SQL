import pyodbc
import json

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Live_BELLONA;"
    "Trusted_Connection=yes;"
)

cur = conn.cursor()

# -----------------------------
# GET TABLES
# -----------------------------
cur.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema='dbo' AND table_name in ('Rista_SaleInvoices', 'Rista_SaleItems','Rista_SaleSourceInfo','Rista_SalePayments',
'Rista_SaleCustomers','Rista_SaleDelivery','Rista_SaleDeliveryBy')
AND table_type='BASE TABLE';
""")

tables = [row[0] for row in cur.fetchall()]

schema = {"tables": []}

# -----------------------------
# LOOP TABLES
# -----------------------------
for table in tables:

    table_obj = {
        "name": table,
        "columns": [],
        "primary_key": None,
        "foreign_keys": []
    }

    # -----------------------------
    # COLUMNS
    # -----------------------------
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name=?
    """, (table,))

    cols = cur.fetchall()

    for col in cols:
        table_obj["columns"].append({
            "name": col[0],
            "type": col[1],
            "nullable": col[2] == "YES",
            "default": col[3]
        })

    # -----------------------------
    # PRIMARY KEY
    # -----------------------------
    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name=?
        AND tc.constraint_type='PRIMARY KEY'
    """, (table,))

    pk = cur.fetchone()
    if pk:
        table_obj["primary_key"] = pk[0]

    # -----------------------------
    # FOREIGN KEYS
    # -----------------------------
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type='FOREIGN KEY'
        AND tc.table_name=?;
    """, (table,))

    fks = cur.fetchall()

    for fk in fks:
        table_obj["foreign_keys"].append({
            "column": fk[0],
            "references": f"{fk[1]}.{fk[2]}"
        })

    schema["tables"].append(table_obj)

def to_llm_text(schema):
    text = ""

    for table in schema["tables"]:
        text += f"\nTABLE {table['name']}\n"

        for col in table["columns"]:
            line = f"- {col['name']} ({col['type']})"
            if col["name"] == table["primary_key"]:
                line += " PK"
            text += line + "\n"

        for fk in table["foreign_keys"]:
            text += f"  FK {fk['column']} → {fk['references']}\n"

    return text

# -----------------------------
# SAVE FILE
# -----------------------------
with open("schema_dictionary.json", "w") as f:
    json.dump(schema, f, indent=2)

print("Schema exported successfully!")
with open("schema_dictionary.txt", "w", encoding="utf-8") as f:
    llm_text = to_llm_text(schema)
    f.write(llm_text)
    print(llm_text)
    
print("LLM Text Generated successfully!")