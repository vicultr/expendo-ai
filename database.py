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


# ✅  clasMappedses (all your tables)
CompletePrePayment = Base.classes.tb_CompletePrePayment
PendingBills       = Base.classes.tb_PendingBills
CompleteBills      = Base.classes.tb_CompleteBills
BillCode           = Base.classes.tb_BillCode
Client             = Base.classes.tb_Client
AccountGroup       = Base.classes.tb_AccountGroup
ActivityLog        = Base.classes.tb_ActivityLog
Bank               = Base.classes.tb_Bank
Country            = Base.classes.tb_Country
Module             = Base.classes.tb_Module
PaymentIn          = Base.classes.tb_PaymentIn
PaymentOut         = Base.classes.tb_PaymentOut
Plan               = Base.classes.tb_Plan
PendingData        = Base.classes.tb_PendingData
PendingPayment     = Base.classes.tb_PendingPayment
USSDLogs           = Base.classes.tb_USSDLogs
Reports            = Base.classes.tb_Reports
Role               = Base.classes.tb_Role
PreRegistration    = Base.classes.tb_PreRegistration
Tarrif             = Base.classes.tb_Tarrif
Accounts           = Base.classes.tb_Accounts
Transaction        = Base.classes.tb_Transaction
TransactionCharges = Base.classes.tb_TransactionCharges
TransactionDetail  = Base.classes.tb_TransactionDetail
User               = Base.classes.tb_User
Public             = Base.classes.tb_Public
PrePayment         = Base.classes.tb_PrePayment
Blog               = Base.classes.tb_Blog
Corporate          = Base.classes.tb_Corporate
Claims             = Base.classes.tb_claims


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
