-- V0012__rag_trace_summary.sql
-- P1-4: Bang tong hop tracing moi luot hoi RAG (Observability).
-- Idempotent: bao boi IF NOT EXISTS -> an toan chay lai nhieu lan.
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.RagTraceSummary') AND type = 'U')
BEGIN
    CREATE TABLE dbo.RagTraceSummary (
        TraceID        NVARCHAR(80) NOT NULL PRIMARY KEY,
        CreatedAt      DATETIME NOT NULL CONSTRAINT DF_RagTraceSummary_CreatedAt DEFAULT GETDATE(),
        Department     NVARCHAR(255) NULL,
        Roles          NVARCHAR(255) NULL,
        Model          NVARCHAR(100) NULL,
        Question       NVARCHAR(500) NULL,
        TokensIn       INT NULL,
        TokensOut      INT NULL,
        Cost           FLOAT NULL,
        FinalLatencyMs INT NULL,
        ContextMs      INT NULL,
        IntentMs       INT NULL,
        HydeMs         INT NULL,
        GlossaryMs     INT NULL,
        RetrievalMs    INT NULL,
        RerankMs       INT NULL,
        GateMs         INT NULL,
        LlmMs          INT NULL,
        Refusal        BIT NULL,
        RefusalReason  NVARCHAR(100) NULL,
        DocsCount      INT NULL,
        RetrievalMode  NVARCHAR(50) NULL
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_RagTraceSummary_CreatedAt' AND object_id = OBJECT_ID(N'dbo.RagTraceSummary'))
    CREATE INDEX IX_RagTraceSummary_CreatedAt ON dbo.RagTraceSummary (CreatedAt);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_RagTraceSummary_Dept' AND object_id = OBJECT_ID(N'dbo.RagTraceSummary'))
    CREATE INDEX IX_RagTraceSummary_Dept ON dbo.RagTraceSummary (Department, CreatedAt);
GO
