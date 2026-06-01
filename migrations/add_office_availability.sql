-- Run once on production. Adds operational "unavailable" state + admin/kiosk-visible notice.

ALTER TABLE offices
  ADD COLUMN availability_status VARCHAR(20) NOT NULL DEFAULT 'available' COMMENT 'available | unavailable' AFTER is_active,
  ADD COLUMN unavailability_notice TEXT NULL COMMENT 'Reason shown to admins (QA) and optionally kiosk' AFTER availability_status;
