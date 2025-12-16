from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import engine, get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from logic import get_dynamic_schema_context
from fastapi.middleware.cors import CORSMiddleware
from logic import get_all_tables
import os
from dotenv import load_dotenv
from openai import OpenAI
import re


def clean_query(query: str) -> str:
    """
    Cleans the AI-generated SQL query by removing code block markers and extra whitespace.
    """
    # Remove code block markers if present
    query = re.sub(r"^```sql\s*|^```", "", query, flags=re.IGNORECASE)
    query = re.sub(r"```$", "", query)
    # Remove leading/trailing whitespace
    return query.strip()

def classify_intent(message: str) -> str:
    """
    Uses AI to detect if the user's message is a database question or a normal chat.
    Returns: "db_query" or "general_chat"
    """

    prompt = f"""
    Classify the user's intent.

    User message: "{message}"

    Categories:
    - db_query: If the user is asking about clients, payments, tables, records, counts, data, SQL, reports, or anything requiring querying the database.
    - general_chat: If the message is a normal conversation, joke, greeting, or anything not related to data.

    Respond with only one word: db_query or general_chat.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip().lower()



load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class NLRequest(BaseModel):
    question: str


@app.post("/chat")
def general_chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly conversational AI assistant. "
                    "Answer the user's message normally without generating SQL."
                )
            },
            {"role": "user", "content": request.message}
        ]
    )

    return {
        "response": response.choices[0].message.content
    }


@app.on_event("startup")
def startup_event():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sys.databases"))
            dbs = [row[0] for row in result]
            print("✅ Connected to SQL Server. Databases:", dbs)
    except Exception as e:
        print("❌ DB connection failed:", e)


@app.get("/")
async def root():
    return {"message": "welcome to hosibill"}   


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT name FROM sys.databases"))
    return [row[0] for row in result]


@app.get("/tables")
def list_tables_endpoint(db: Session = Depends(get_db)):
    tables = get_all_tables(db)
    return tables


@app.post("/ask")
def ask_database(request: NLRequest, db: Session = Depends(get_db)):
    # Step 1: Build dynamic schema for GPT
    schema = get_dynamic_schema_context(db)

    # Step 2: Ask GPT to convert NL → SQL
    prompt = f"""
    You are an expert SQL generator.
    Convert the user question into a valid SQL query using ONLY this schema:

    {schema}

    Rules:
    - Use ONLY tables and columns listed above.
    - Do NOT invent columns.
    - Return ONLY SQL query without explanations.

    User Question: "{request.question}"
    """

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    sql_query = clean_query(ai_response.choices[0].message.content)
    print("Generated SQL:", sql_query)

    # Step 3: Run the query safely
    try:
        result = db.execute(text(sql_query)).fetchall()
        rows = [dict(row._mapping) for row in result]
        return {
            "sql": sql_query,
            "rows_returned": len(rows),
            "data": rows
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/smart")
def smart_router(request: ChatRequest, db: Session = Depends(get_db)):
    user_msg = request.message

    # 1️⃣ Classify intent
    intent = classify_intent(user_msg)
    print("Intent detected:", intent)

    # 2️⃣ If it's a database question → run SQL generator
    if intent == "db_query":
        from logic import get_dynamic_schema_context
        schema = get_dynamic_schema_context(db)

        # 🟦 A: Generate SQL from user question
        ai_prompt = f"""
        You are an expert SQL generator.

        Convert the user's question into a valid SQL query using ONLY this database schema:

        {schema}

        Important rules:
        - Only use tables and columns that exist in the schema.
        - Do NOT invent or assume any fields.
        - Respond with ONLY the SQL query and nothing else.

        User Question: "{user_msg}"
        """

        ai_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ai_prompt}]
        )

        sql_query = clean_query(ai_resp.choices[0].message.content)

        try:
            # 🟦 B: Execute SQL
            result = db.execute(text(sql_query)).fetchall()
            rows = [dict(r._mapping) for r in result]

            # 🟦 C: Generate friendly human explanation
            explanation_prompt = f"""
            You are a friendly data assistant.

            Explain the results of this query in a simple, clear, conversational way.
            Avoid technical database language unless absolutely necessary.

            User Question: "{user_msg}"

            SQL Query:
            {sql_query}

            Number of rows returned: {len(rows)}

            Sample of returned data:
            {rows[:3]}

            Your explanation MUST include:
            1. What the user was trying to find
            2. What the SQL query does in plain English
            3. What the returned data means
            4. Any helpful insights, patterns, or observations
            5. A short closing summary

            Use friendly headings and bullet points (Markdown format).
            Keep the tone warm, helpful, and easy to read.
            """

            explanation_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": explanation_prompt}]
            )

            explanation = explanation_resp.choices[0].message.content.strip()

            # 🟦 D: Return combined response
            return {
                "type": "database",
                "sql": sql_query,
                "rows": len(rows),
                "data": rows,
                "explanation": explanation
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 🟩 If it's not a DB question → normal chat mode
    else:
        chat_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful conversational assistant. "
                        "Do NOT generate SQL in this mode. Just answer normally."
                    )
                },
                {"role": "user", "content": user_msg}
            ]
        )

        return {
            "type": "chat",
            "response": chat_response.choices[0].message.content
        }
