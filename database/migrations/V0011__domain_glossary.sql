-- V0011__domain_glossary.sql
-- P0-3: Tu dien dong nghia / viet tat theo domain (Domain Glossary).
-- Idempotent: bao boi IF NOT EXISTS -> an toan chay lai nhieu lan.
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.DomainGlossary') AND type = 'U')
BEGIN
    CREATE TABLE dbo.DomainGlossary (
        GlossaryID INT IDENTITY(1,1) PRIMARY KEY,
        Domain     NVARCHAR(50)  NOT NULL,
        Term       NVARCHAR(255) NOT NULL,
        Synonyms   NVARCHAR(MAX) NULL,
        Expansion  NVARCHAR(1000) NULL,
        IsActive   BIT NOT NULL CONSTRAINT DF_DomainGlossary_IsActive DEFAULT 1,
        CreatedAt  DATETIME NOT NULL CONSTRAINT DF_DomainGlossary_CreatedAt DEFAULT GETDATE(),
        UpdatedAt  DATETIME NULL
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_DomainGlossary_Domain' AND object_id = OBJECT_ID(N'dbo.DomainGlossary'))
    CREATE INDEX IX_DomainGlossary_Domain ON dbo.DomainGlossary (Domain, IsActive);
GO
