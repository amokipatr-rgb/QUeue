-- Adds index for fast unrated token lookup by student_id
-- Used by /api/student/token to block new tokens when a previous
-- completed token has no feedback_submitted_at

CREATE INDEX idx_tokens_student_unrated
ON university_tokens(student_id, status, feedback_submitted_at);
