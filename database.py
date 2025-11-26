import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not set in .env")

# Engine & Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ✅ Automap base
Base = automap_base()

# ✅ Reflect all tables automatically
Base.prepare(engine, reflect=True)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# # ✅ Test connection when you run this file directly
# if __name__ == "__main__":
#     try:
#         with engine.connect() as conn:
#             result = conn.execute(text("SELECT name FROM sys.tables"))
#             print("✅ Connected! Tables in DB:")
#             for row in result:
#                 print("-", row[0])
#     except Exception as e:
#         print("❌ Connection failed:", e)
