-- Add login_location column to officer_sessions for geo-location tracking
ALTER TABLE officer_sessions
ADD COLUMN login_location VARCHAR(255) DEFAULT NULL AFTER login_ip;
