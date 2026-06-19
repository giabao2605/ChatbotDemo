import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
server = os.getenv('SQL_SERVER', r'localhost\SQLEXPRESS')
database = os.getenv('SQL_DATABASE', 'Mech_Chatbot_DB')

driver = 'ODBC Driver 17 for SQL Server'
conn_str = f'mssql+pyodbc:///?odbc_connect=' + urllib.parse.quote_plus(
    f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
)
engine = create_engine(conn_str)

with engine.begin() as conn:
    try:
        conn.execute(text("CREATE INDEX IX_BangKeVatTu_DocID ON BangKeVatTu(DocID)"))
        conn.execute(text("CREATE INDEX IX_BangKeVatTu_MaHang ON BangKeVatTu(MaHang)"))
        conn.execute(text("CREATE INDEX IX_BangKeVatTu_VatLieu ON BangKeVatTu(VatLieu)"))
        print("Indexes created successfully.")
    except Exception as e:
        print("Error or index already exists:", e)
