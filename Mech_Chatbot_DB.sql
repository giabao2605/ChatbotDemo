-- ==========================================
-- DATABASE HO TRO CHATBOT CO KHI (da sua - them cot RefImages cho FIX C5)
-- ==========================================
IF NOT EXISTS (
    SELECT *
    FROM sys.databases
    WHERE name = 'Mech_Chatbot_DB'
) BEGIN CREATE DATABASE Mech_Chatbot_DB;
END
GO USE Mech_Chatbot_DB;
GO -- Xoa Foreign keys neu co
    WHILE (
        EXISTS (
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'
        )
    ) BEGIN
DECLARE @sql NVARCHAR(2000);
SELECT TOP 1 @sql = (
        'ALTER TABLE ' + TABLE_SCHEMA + '.[' + TABLE_NAME + '] DROP CONSTRAINT [' + CONSTRAINT_NAME + ']'
    )
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY';
EXEC (@sql);
END
GO -- Xoa cac bang cu (dung thu tu phu thuoc)
IF OBJECT_ID('dbo.LichSuChat', 'U') IS NOT NULL DROP TABLE dbo.LichSuChat;
IF OBJECT_ID('dbo.BangKeVatTu', 'U') IS NOT NULL DROP TABLE dbo.BangKeVatTu;
IF OBJECT_ID('dbo.TaiLieuKyThuat', 'U') IS NOT NULL DROP TABLE dbo.TaiLieuKyThuat;
IF OBJECT_ID('dbo.TaiLieu', 'U') IS NOT NULL DROP TABLE dbo.TaiLieu;
IF OBJECT_ID('dbo.IngestionJobs', 'U') IS NOT NULL DROP TABLE dbo.IngestionJobs;
GO -- ==========================================
    -- PHAN 1: QUAN LY TAI LIEU (Documents) & QUEUE
    -- ==========================================
    CREATE TABLE IngestionJobs (
        JobID INT IDENTITY(1, 1) PRIMARY KEY,
        TenFile NVARCHAR(255) NOT NULL,
        FilePath NVARCHAR(500) NOT NULL,
        ThuMuc NVARCHAR(255),
        Status NVARCHAR(50) DEFAULT 'pending', -- pending, extracting, embedding, failed, pending_review, published
        ErrorMessage NVARCHAR(MAX),
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
GO
    CREATE TABLE TaiLieu (
        DocID INT IDENTITY(1, 1) PRIMARY KEY,
        TenFile NVARCHAR(255) NOT NULL,
        ThuMuc NVARCHAR(255),
        NgayTaiLen DATETIME DEFAULT GETDATE(),
        TrangThaiVector BIT DEFAULT 0,
        TrangThai NVARCHAR(50) DEFAULT 'published',
        NgayDuyet DATETIME,
        NguoiDuyet NVARCHAR(255),
        LyDoTuChoi NVARCHAR(MAX)
    );
GO -- ==========================================
    -- PHAN 2: DU LIEU KY THUAT CO KHI
    -- ==========================================
    CREATE TABLE TaiLieuKyThuat (
        ID INT IDENTITY(1, 1) PRIMARY KEY,
        DocID INT,
        TrangSo INT,
        LoaiTaiLieu NVARCHAR(255),
        -- Nhan tai lieu
        MaDoiTuong NVARCHAR(MAX),
        -- Danh sach ma doi tuong dang JSON string
        TenSanPham NVARCHAR(500),
        -- Ten san pham / Tieu de
        CongDoan NVARCHAR(255),
        -- To san xuat / Quy trinh
        VatLieu NVARCHAR(255),
        -- Vat lieu
        SoLuong INT,
        -- So luong
        NguoiLap NVARCHAR(255),
        -- Noi rong (cu NVARCHAR(100)) tranh truncate
        NgayVe DATE,
        -- Ngay phat hanh / Ngay ve
        DungSaiDay NVARCHAR(255),
        -- Noi rong (cu NVARCHAR(100))
        DungSaiKhac NVARCHAR(255),
        -- Noi rong (cu NVARCHAR(100))
        KichThuocTongThe NVARCHAR(255),
        -- Noi rong (cu NVARCHAR(100))
        HDCV NVARCHAR(MAX),
        -- Huong dan cong viec
        YCKT NVARCHAR(MAX),
        -- Yeu cau ky thuat
        CONSTRAINT FK_TaiLieuKyThuat_TaiLieu FOREIGN KEY (DocID) REFERENCES TaiLieu(DocID) ON DELETE CASCADE,
        -- Bao toan ven du lieu: moi (DocID, TrangSo) chi 1 dong metadata.
        CONSTRAINT UQ_TaiLieuKyThuat_Doc_Trang UNIQUE (DocID, TrangSo)
    );
GO
    CREATE TABLE BangKeVatTu (
        ID INT IDENTITY(1, 1) PRIMARY KEY,
        DocID INT NOT NULL,
        TrangSo INT,
        MaHang NVARCHAR(255),
        TenVatTu NVARCHAR(500),
        VatLieu NVARCHAR(255),
        SoLuong INT,
        GhiChu NVARCHAR(MAX),
        CONSTRAINT FK_BangKeVatTu_TaiLieu FOREIGN KEY (DocID) REFERENCES TaiLieu(DocID) ON DELETE CASCADE
    );
GO
    CREATE INDEX IX_BangKeVatTu_DocID ON BangKeVatTu(DocID);
    CREATE INDEX IX_BangKeVatTu_MaHang ON BangKeVatTu(MaHang);
    CREATE INDEX IX_BangKeVatTu_VatLieu ON BangKeVatTu(VatLieu);
GO -- ==========================================
    -- PHAN 3: LUU TRU LICH SU CHAT
    -- ==========================================
    CREATE TABLE LichSuChat (
        ChatID INT IDENTITY(1, 1) PRIMARY KEY,
        SessionID VARCHAR(100) NOT NULL,
        CauHoi_User NVARCHAR(MAX) NOT NULL,
        TraLoi_Bot NVARCHAR(MAX) NOT NULL,
        HinhAnhUpload NVARCHAR(500),
        -- Duong dan anh user upload (neu co)
        RefImages NVARCHAR(MAX),
        -- FIX C5: danh sach duong dan ban ve can cu dang JSON
        DanhGia TINYINT,
        -- 1: Like, -1: Dislike, NULL: Chua danh gia
        ThoiGian DATETIME DEFAULT GETDATE()
    );
GO -- Index composite: vua loc theo Session, vua sap xep theo thoi gian
    CREATE NONCLUSTERED INDEX IX_LichSuChat_Session_Time ON LichSuChat(SessionID, ThoiGian);
GO -- ==========================================
    -- MIGRATION (CHI DUNG KHI DB DA TON TAI VA KHONG MUON XOA DU LIEU CU)
    -- Thay vi chay lai toan bo script (se xoa het bang), chay rieng doan duoi:
    -- ==========================================
    -- IF NOT EXISTS (
    --     SELECT 1 FROM sys.columns
    --     WHERE Name = N'RefImages' AND Object_ID = Object_ID(N'dbo.LichSuChat')
    -- )
    -- BEGIN
    --     ALTER TABLE dbo.LichSuChat ADD RefImages NVARCHAR(MAX) NULL;
    -- END
    -- GO