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
        conn.execute(text("""
            CREATE TABLE BangKeVatTu (
                ID INT IDENTITY(1, 1) PRIMARY KEY,
                DocID INT NOT NULL,
                TrangSo INT,
                MaHang NVARCHAR(255),
                TenVatTu NVARCHAR(500),
                VatLieu NVARCHAR(255),
                SoLuong INT,
                GhiChu NVARCHAR(MAX),
                FOREIGN KEY (DocID) REFERENCES TaiLieu(DocID) ON DELETE CASCADE
            )
        """))
        print("BangKeVatTu created successfully.")
    except Exception as e:
        print("Error or table already exists:", e)
