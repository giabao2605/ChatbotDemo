-- ============================================================================
-- V0002: Vo hieu hoa cac "phong ban" cong doan / thu muc cu (To_Han, To_Dap,
--        Bang_Ke, CHUNG, Gia_Cong_Ngoai, Ky_Thuat, Ke_Toan, Nhan_Su, Tu_Hoc...)
-- de chi con 14 phong ban chuan hien trong cac dropdown (Tien trinh ingest,
-- Kho tai lieu, ...). Du lieu tai lieu cu (TaiLieu.ThuMuc) van doc binh thuong.
--
-- An toan & idempotent: chi set IsActive = 0 cho phong ban KHONG thuoc 14 ma
-- chuan. Khong xoa du lieu, co the bat lai bang IsActive = 1 trong trang
-- Nguoi dung > Phong ban & Khu.
--
-- Chay sau seed/03_departments.sql:
--   sqlcmd -S WS-IT-04\SQLEXPRESS -d Mech_Chatbot_DB -E -I -i V0002__deactivate_legacy_stage_departments.sql
-- ============================================================================
USE Mech_Chatbot_DB;
GO

UPDATE dbo.Departments
SET IsActive = 0
WHERE DeptCode NOT IN (
    N'Technical', N'Production', N'Maintenance', N'Molding',
    N'Accountant', N'Purchasing', N'Warehouse', N'Sales',
    N'HR', N'Planning', N'QualityControl', N'ISO', N'HSE_5S', N'IT'
);
GO

-- Dam bao 14 phong ban chuan dang active (phong khi bi tat truoc do).
UPDATE dbo.Departments
SET IsActive = 1
WHERE DeptCode IN (
    N'Technical', N'Production', N'Maintenance', N'Molding',
    N'Accountant', N'Purchasing', N'Warehouse', N'Sales',
    N'HR', N'Planning', N'QualityControl', N'ISO', N'HSE_5S', N'IT'
);
GO

PRINT 'V0002: Da vo hieu hoa phong ban cong doan cu, giu lai 14 phong ban chuan.';
GO
