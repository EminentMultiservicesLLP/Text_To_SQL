import json

def load_schema():
    with open("schema_dictionary.json") as f:
        return json.load(f)


def schema_to_prompt(schema):

    text = ""

    for table in schema["tables"]:
        text += f"\nTABLE {table['name']}\n"

        for col in table["columns"]:
            line = f"- {col['name']} ({col['type']})"
            if col["name"] == table.get("primary_key"):
                line += " PK"
            text += line + "\n"

        for fk in table.get("foreign_keys", []):
            text += f"  FK {fk['column']} → {fk['references']}\n"

    return text