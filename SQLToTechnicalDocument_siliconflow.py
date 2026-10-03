import os
import re
import logging
import time
from datetime import datetime
from unittest import result
from urllib import response
from openai import OpenAI
import pyodbc
import shutil

# ---------------------------
# CONFIGURATION
# ---------------------------
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=bismarvel;"
    "Trusted_Connection=yes;"
)
API_KEY="sk-oorjzczoeglcbuzjlvonboraagfdzlrkkoftygltebzwmzso"
OUTPUT_FOLDER = r"E:\BIS\Bismarvel\BISDB\SP\Output\TechnicalDocuments"
PROMPT_FOLDER = r"E:\BIS\Bismarvel\BISDB\SP\Prompts"
SP_FOLDER = r"E:\BIS\Bismarvel\BISDB\SP\PendingSPs"
MOVE_COMPLETED_SP_FILES = r"E:\BIS\Bismarvel\BISDB\SP\ReadCompletedSPs"
LOG_FOLDER = r"E:\BIS\Bismarvel\BISDB\SP\logs"
PROMPT_OUTPUT_FOLDER = r"E:\BIS\Bismarvel\BISDB\SP\Output\FullPrompts"

MODEL_NAME = "deepseek-ai/DeepSeek-V3.1"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Setup the client with your free API key
os.environ.pop("OPENAI_API_KEY", None)
client = OpenAI(
    api_key=API_KEY, 
    base_url="https://api.siliconflow.cn/v1",
    default_headers={"Authorization": f"Bearer {API_KEY}"}
)


# ---------------------------
# LOGGING SETUP
# ---------------------------
def setup_logging():
    log_file = os.path.join(
        LOG_FOLDER,
        f"sp_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logging.info("===== Documentation Generation Started =====")

setup_logging()

# --------------------------
# SQL CLEANING
# --------------------------
def clean_sql(sql):
    # Remove multi-line comments
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

    # Remove single line comments
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)

    # Remove GO
    sql = re.sub(r'^\s*GO\s*$', '', sql, flags=re.MULTILINE)

     # Remove USE [DatabaseName]
    sql = re.sub(r'^\s*USE\s+\[?.+?\]?\s*;?\s*$',
                 '',
                 sql,
                 flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove SQL noise
    noise = ["SET ANSI_NULLS ON", "SET QUOTED_IDENTIFIER ON"]
    for n in noise:
        sql = re.sub(n, '', sql, flags=re.IGNORECASE)

    # Remove extra whitespace
    sql = re.sub(r'\n\s*\n+', '\n\n', sql)

    return sql.strip()

# --------------------------
# GET TABLES USED BY SP
# --------------------------

def get_tables_from_sp(sp_name):
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT DISTINCT referenced_entity_name
        FROM sys.dm_sql_referenced_entities(?, 'OBJECT') r
        INNER JOIN sys.objects o
        ON r.referenced_id = o.object_id
        WHERE o.type = 'U'
        """, sp_name)

        return [row[0] for row in cursor.fetchall()]

# --------------------------
# GET SCHEMA FOR TABLES
# --------------------------

def get_table_schema(tables):
    schema_text = ""

    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()

        for table in tables:
            cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            """, table)

            cols = cursor.fetchall()

            col_text = ", ".join(
                f"{c.COLUMN_NAME} ({c.DATA_TYPE})"
                for c in cols
            )

            schema_text += f"\n"
            schema_text += f"------------------------------\n"
            schema_text += f"Table: [{table}] ({col_text})\n"
            schema_text += f"------------------------------\n"

    return schema_text

# ---------------------------
# FILE READ FUNCTIONS
# ---------------------------

def read_file(path):
    logging.info(f"Reading file: {path}")
    try:
        # Try UTF-8 first
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to UTF-16 (common for SSMS)
        with open(path, "r", encoding="utf-16") as f:
            return f.read()


def load_prompt(prompt_type):
    file_name = f"{prompt_type}_prompt.txt"
    prompt_path = os.path.join(PROMPT_FOLDER, file_name)

    logging.info(f"Loading prompt: {prompt_path}")

    if not os.path.exists(prompt_path):
        logging.error(f"Prompt file missing: {prompt_path}")
        raise FileNotFoundError(prompt_path)

    return read_file(prompt_path)


def load_sp_files():
    logging.info("Scanning stored procedure folder")

    sp_files = [
        os.path.join(SP_FOLDER, f)
        for f in os.listdir(SP_FOLDER)
        if f.endswith(".sql")
    ]

    logging.info(f"Found {len(sp_files)} stored procedures")

    return sp_files


# ---------------------------
# API CALL FUNCTION
# ---------------------------
def call_api(prompt_string):

    logging.info("Calling API")
    try:
        response = client.chat.completions.create(
            # Using DeepSeek-V3 for best SQL reasoning/documentation balance
            model=MODEL_NAME, 
            messages=[
                {"role": "system", "content": "Generate structured SQL help documentation."},
                {"role": "user", "content": prompt_string}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"SiliconFlow Error: {e}")
        return None
        

# ---------------------------
# HTML SAVE FUNCTION
# ---------------------------

def save_html(sp_name, mode, content):

    logging.info(f"Saving HTML output for: {sp_name}")

    # html_template = f"""
    # <html>
    # <head>
    #     <title>{sp_name} - {mode}</title>
    #     <style>
    #         body {{
    #             font-family: Segoe UI, Arial;
    #             margin: 40px;
    #         }}
    #     </style>
    # </head>
    # <body>
    #     {content.replace("\n", "<br>")}
    # </body>
    # </html>
    # """
    

    # CLEANUP: Remove potential Markdown wrappers (```html ... ```) 
    clean_content = content.replace("```html", "").replace("```", "").strip()

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{sp_name} - {mode}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1000px;
                margin: 40px auto;
                padding: 0 20px;
            }}
            h1 {{ border-bottom: 2px solid #0056b3; color: #0056b3; padding-bottom: 10px; }}
            h2 {{ color: #0078d4; margin-top: 30px; border-left: 5px solid #0078d4; padding-left: 10px; }}
            h3 {{ color: #444; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; background: #fff; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f4f4f4; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
            .risk-high {{ color: #d11; font-weight: bold; }} /* Style for the logic risks */
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        {clean_content}
    </body>
    </html>
    """

    output_file = os.path.join(OUTPUT_FOLDER, f"{sp_name}_{mode}_GeminiFlash.html")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    logging.info(f"Saved file: {output_file}")

def write_to_file(sp_name, content):

    logging.info(f"Saving prompt content for: {sp_name}")

    output_file = os.path.join(PROMPT_OUTPUT_FOLDER, f"{sp_name}_prompt.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"Saved file: {output_file}")

# ---------------------------
# MAIN DOCUMENT GENERATION
# ---------------------------

def generate_docs(prompt_type="full"):

    logging.info(f"Using prompt type: {prompt_type}")
    fileProcessedCount = 0;
    prompt_template = load_prompt(prompt_type)
    sp_files = load_sp_files()
    sp_files = sp_files[:1]  # TEMP LIMIT FOR TESTING, REMOVE THIS IN PRODUCTION
    for sp_path in sp_files:

        start_time = time.time()

        try:
            sp_name = os.path.splitext(os.path.basename(sp_path))[0]
            logging.info(f"Processing SP: {sp_name}")

            sp_content = read_file(sp_path)
            logging.info("SP content read successfully")
            sp_content = clean_sql(sp_content)

            spName_u = "[dbo].[" + sp_name + "]";
            logging.info(f"SP content cleaned for sp: {spName_u}")
            tables = get_tables_from_sp(spName_u)
            logging.info(f"Tables used by SP: {tables}")
            schema = get_table_schema(tables)
            logging.info(f"Table schema retrieved, {schema}")

            prompt_with_SP = prompt_template.replace("{sp_cotent}", sp_content)
            logging.info("SP content injected into prompt")
            final_prompt = prompt_with_SP.replace("{sp_tables_schema}", schema)
            logging.info("Table schema injected into prompt")
            
            write_to_file(sp_name, final_prompt)

            logging.info(f"Final prompt prepared, calling GROQ API : {final_prompt}")
            result = call_api(final_prompt)

            save_html(sp_name, prompt_type, result)
            shutil.move(sp_path, os.path.join(MOVE_COMPLETED_SP_FILES, f"{sp_name}.sql"))

            elapsed = round(time.time() - start_time, 2)
            logging.info(f"Completed {sp_name} in {elapsed} sec")

            time.sleep(5)  # Short pause between calls to avoid hitting rate limits
            fileProcessedCount += 1
            if fileProcessedCount % 10 == 0:
                logging.info(f"Processed {fileProcessedCount} files so far, sleeping for 60 seconds...") 
                time.sleep(60)
        except Exception as e:
            logging.exception(f"Error processing {sp_path}: {e}")


# ---------------------------
# EXECUTION
# ---------------------------

if __name__ == "__main__":

    generate_docs("full")
    #generate_docs("compact")

    logging.info("===== Documentation Generation Finished =====")