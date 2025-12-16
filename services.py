import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session
from utils import clean_query

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


def generate_sql_query(question: str, schema: str) -> str:
    """
    Generates SQL query from natural language question using AI.
    """
    prompt = f"""
    You are an expert SQL generator.
    Convert the user question into a valid SQL query using ONLY this schema:

    {schema}

    Rules:
    - Use ONLY tables and columns listed above.
    - Do NOT invent columns.
    - Return ONLY SQL query without explanations.

    User Question: "{question}"
    """

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return clean_query(ai_response.choices[0].message.content)


def execute_query(db: Session, sql_query: str) -> list:
    """
    Executes SQL query and returns results as list of dictionaries.
    """
    result = db.execute(text(sql_query)).fetchall()
    return [dict(row._mapping) for row in result]


def generate_explanation(question: str, sql_query: str, rows: list) -> str:
    """
    Generates a friendly explanation of query results.
    """
    explanation_prompt = f"""
    You are a friendly data assistant.

    Explain the results of this query in a simple, clear, conversational way.
    Avoid technical database language unless absolutely necessary.

    User Question: "{question}"

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

    return explanation_resp.choices[0].message.content.strip()


def chat_service(message: str) -> str:
    """
    Handles general chat conversations (non-database queries).
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful conversational assistant. "
                    "Do NOT generate SQL in this mode. Just answer normally."
                )
            },
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content