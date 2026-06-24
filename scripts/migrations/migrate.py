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
        conn.execute(text("ALTER TABLE TaiLieu ADD TrangThai NVARCHAR(50) DEFAULT 'published'"))
        conn.execute(text("ALTER TABLE TaiLieu ADD NgayDuyet DATETIME"))
        conn.execute(text("ALTER TABLE TaiLieu ADD NguoiDuyet NVARCHAR(255)"))
        conn.execute(text("ALTER TABLE TaiLieu ADD LyDoTuChoi NVARCHAR(MAX)"))
    except Exception as e:
        print("Column may already exist")
        
    conn.execute(text("UPDATE TaiLieu SET TrangThai = 'published' WHERE TrangThai IS NULL"))
    print("Migration TaiLieu successful.")
