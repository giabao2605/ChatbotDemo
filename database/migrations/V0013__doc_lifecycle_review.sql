-- V0013__doc_lifecycle_review.sql
-- P1-7: bo sung cot log lan review gan nhat cho TaiLieu (idempotent ALTER).
-- Cac cot EffectiveDate/ExpiryDate/ReviewDate/EffectiveStatus da co san trong baseline.
IF COL_LENGTH('dbo.TaiLieu','LastReviewedAt') IS NULL ALTER TABLE dbo.TaiLieu ADD LastReviewedAt DATETIME NULL;
GO
IF COL_LENGTH('dbo.TaiLieu','LastReviewedBy') IS NULL ALTER TABLE dbo.TaiLieu ADD LastReviewedBy NVARCHAR(255) NULL;
GO
