ALTER TABLE university_tokens
  ADD COLUMN rating TINYINT DEFAULT NULL COMMENT '1-5 star rating' AFTER call_attempts,
  ADD COLUMN feedback_text TEXT DEFAULT NULL COMMENT 'Optional written feedback' AFTER rating,
  ADD COLUMN feedback_submitted_at TIMESTAMP NULL DEFAULT NULL COMMENT 'When feedback was given' AFTER feedback_text;
