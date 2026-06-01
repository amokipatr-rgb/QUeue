-- Changes the unique constraint on services from global service_code
-- to per-office (office_id, service_code) so PS can exist in every office

ALTER TABLE services DROP INDEX service_code;
ALTER TABLE services ADD UNIQUE KEY unique_service_per_office (office_id, service_code);
