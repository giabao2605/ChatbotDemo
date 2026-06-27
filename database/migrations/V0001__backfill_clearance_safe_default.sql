-- =============================================================================
-- V0001: Backfill clearance safe-default + siet muc mat tai lieu (GD5 muc 5)
-- Idempotent: chay lai nhieu lan deu an toan.
-- Chay SAU database/schema/01_baseline.sql va cac seed.
--   sqlcmd -S WS-IT-04\SQLEXPRESS -d Mech_Chatbot_DB -E -I -i database/migrations/V0001__backfill_clearance_safe_default.sql
-- =============================================================================
USE Mech_Chatbot_DB;
GO
SET NOCOUNT ON;
GO
IF EXISTS (SELECT 1 FROM dbo._SchemaVersions WHERE Version = 'V0001')
BEGIN
    PRINT 'V0001 da chay truoc do -- bo qua.';
    RETURN;
END
GO

-- 1) SAFE-DEFAULT clearance: moi user PHAI co ban ghi clearance.
--    Thieu -> 'internal' (muc an toan toi thieu, KHONG BAO GIO mac dinh 'confidential').
--    Dong bo voi fallback trong auth/service.py.
INSERT INTO dbo.UserSecurityClearance (UserID, MaxLevel)
SELECT u.UserID, 'internal'
  FROM dbo.Users u
 WHERE NOT EXISTS (SELECT 1 FROM dbo.UserSecurityClearance c WHERE c.UserID = u.UserID);
GO

-- 2) Chuan hoa clearance sai/rong -> 'internal' (safe-default).
UPDATE dbo.UserSecurityClearance
   SET MaxLevel = 'internal'
 WHERE MaxLevel IS NULL
    OR LTRIM(RTRIM(MaxLevel)) = ''
    OR MaxLevel NOT IN ('public', 'internal', 'confidential');
GO

-- 3) SAFE-DEFAULT muc mat tai lieu: tai lieu THIEU/SAI SecurityLevel -> 'confidential'
--    (coi nhu mat; chi user clearance confidential moi doc duoc). Truoc day backfill cu
--    gan NULL -> 'internal' gay ho hong; nay siet lai theo nguyen tac an toan, dong bo
--    voi _security_filter (Qdrant) va search_bom_by_code (SQL).
UPDATE dbo.TaiLieu
   SET SecurityLevel = 'confidential'
 WHERE SecurityLevel IS NULL
    OR LTRIM(RTRIM(SecurityLevel)) = ''
    OR SecurityLevel NOT IN ('public', 'internal', 'confidential');
GO

-- 4) (TUY CHON) Nang clearance cho user can xem tai lieu mat.
--    >>> Sua danh sach Username cho dung thuc te TRUOC khi bo comment <<<
/*
UPDATE c SET MaxLevel = 'confidential'
  FROM dbo.UserSecurityClearance c
  JOIN dbo.Users u ON u.UserID = c.UserID
 WHERE u.Username IN ('ketoan_truong', 'hr_manager');
GO
*/

INSERT INTO dbo._SchemaVersions (Version, Description)
VALUES ('V0001', 'GD5 muc 5: backfill clearance safe-default + tai lieu thieu muc mat coi nhu confidential');
GO

PRINT 'V0001 hoan tat: clearance backfill + siet muc mat safe-default.';
GO
