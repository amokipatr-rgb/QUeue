ALTER TABLE university_tokens
  ADD COLUMN parent_name  VARCHAR(100) DEFAULT NULL AFTER student_phone,
  ADD COLUMN parent_phone VARCHAR(20)  DEFAULT NULL AFTER parent_name,
  ADD COLUMN is_priority  TINYINT(1)   DEFAULT 0  AFTER parent_phone;

ALTER TABLE university_tokens
  ADD INDEX idx_priority (is_priority, office_id, status);
