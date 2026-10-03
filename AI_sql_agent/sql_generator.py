from ollama_client import generate
from schema_loader import load_schema, schema_to_prompt

schema_text = schema_to_prompt(load_schema())

def generate_sql(question):

    prompt = f"""
You are a PostgreSQL SQL expert.

Schema:
{schema_text}

Rules:
- Only output SQL
- No explanation
- Use correct joins
- Only use available tables

User Question:
{question}

SQL:
"""

    return generate(prompt)