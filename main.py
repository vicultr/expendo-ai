from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import engine, get_db
from models import ChatRequest, NLRequest
from services import classify_intent, generate_sql_query, execute_query, generate_explanation, chat_service
from logic import get_dynamic_schema_context, get_all_tables

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/chat")
def general_chat(request: ChatRequest):
    response = chat_service(request.message)
    return {"response": response}


@app.post("/ask")
def ask_database(request: NLRequest, db: Session = Depends(get_db)):
    schema = get_dynamic_schema_context(db)
    sql_query = generate_sql_query(request.question, schema)
    
    print("Generated SQL:", sql_query)
    
    try:
        result = execute_query(db, sql_query)
        return {
            "sql": sql_query,
            "rows_returned": len(result),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/smart")
def smart_router(request: ChatRequest, db: Session = Depends(get_db)):
    user_msg = request.message
    intent = classify_intent(user_msg)
    
    print("Intent detected:", intent)
    
    if intent == "db_query":
        schema = get_dynamic_schema_context(db)
        sql_query = generate_sql_query(user_msg, schema)
        
        try:
            rows = execute_query(db, sql_query)
            explanation = generate_explanation(user_msg, sql_query, rows)
            
            return {
                "type": "database",
                "sql": sql_query,
                "rows": len(rows),
                "data": rows,
                "explanation": explanation
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        return {
            "type": "chat",
            "response": chat_service(user_msg)
        }