-- Add missing indexes for admin performance
-- Run after deploying this migration to production

CREATE INDEX idx_logs_officer ON queue_logs(officer_id);
CREATE INDEX idx_tokens_assigned_officer ON university_tokens(assigned_officer_id);
CREATE INDEX idx_tokens_feedback_submitted ON university_tokens(feedback_submitted_at);
CREATE INDEX idx_tokens_called ON university_tokens(called_at);
CREATE INDEX idx_tokens_serving_started ON university_tokens(serving_started_at);
CREATE INDEX idx_tokens_completed ON university_tokens(completed_at);
CREATE INDEX idx_tokens_skipped ON university_tokens(skipped_at);
CREATE INDEX idx_offices_availability ON offices(availability_status);
