-- V0010__access_requests.sql
-- P0-2: Bang yeu cau cap quyen (Access Request Workflow).
-- Idempotent: bao boi IF NOT EXISTS -> an toan chay lai nhieu lan.
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.AccessRequests') AND type = 'U')
BEGIN
    CREATE TABLE dbo.AccessRequests (
        RequestID        INT IDENTITY(1,1) PRIMARY KEY,
        UserID           INT NOT NULL,
        Username         NVARCHAR(255) NULL,
        RequestType      NVARCHAR(20) NOT NULL,   -- 'security' | 'department'
        RequestedLevel   NVARCHAR(20) NULL,        -- public | internal | confidential
        RequestedDept    NVARCHAR(255) NULL,       -- = Departments.DeptCode
        QuestionText     NVARCHAR(MAX) NULL,       -- cau hoi ngu canh khi bi chan
        Reason           NVARCHAR(MAX) NULL,
        Status           NVARCHAR(20) NOT NULL CONSTRAINT DF_AccessRequests_Status DEFAULT 'pending',  -- pending|approved|rejected
        ReviewerID       INT NULL,
        ReviewerUsername NVARCHAR(255) NULL,
        ReviewNote       NVARCHAR(MAX) NULL,
        ReviewedAt       DATETIME NULL,
        CreatedAt        DATETIME NOT NULL CONSTRAINT DF_AccessRequests_CreatedAt DEFAULT GETDATE()
    );
END
GO
-- Index tra cuu nhanh
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AccessRequests_Status' AND object_id = OBJECT_ID(N'dbo.AccessRequests'))
    CREATE INDEX IX_AccessRequests_Status ON dbo.AccessRequests (Status, CreatedAt DESC);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_AccessRequests_User' AND object_id = OBJECT_ID(N'dbo.AccessRequests'))
    CREATE INDEX IX_AccessRequests_User ON dbo.AccessRequests (UserID, Status);
GO
