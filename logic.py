from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_all_tables(db: Session) -> list:
    """
    Returns a list of all table names in the connected database.
    """
    try:
        query = text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        result = db.execute(query)
        tables = [row[0] for row in result]

        if not tables:
            raise HTTPException(status_code=404, detail="No tables found in the database")

        return tables

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tables: {e}")


# NEW: Extract schema for AI context
def get_dynamic_schema_context(db: Session) -> str:
    tables = get_all_tables(db)
    schema_output = ""

    for table in tables:
        cols = db.execute(text(f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}'
        """)).fetchall()

        schema_output += f"\nTable: {table}\n"
        for col in cols:
            schema_output += f"  - {col[0]} ({col[1]})\n"

    return schema_output