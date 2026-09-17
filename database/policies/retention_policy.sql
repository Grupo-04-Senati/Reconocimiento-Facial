CREATE POLICY "recognition_logs_service_role"
  ON recognition_logs FOR ALL TO service_role USING (TRUE);

CREATE POLICY "recognition_logs_authenticated_read"
  ON recognition_logs FOR SELECT TO authenticated USING (TRUE);

ALTER TABLE recognition_logs ENABLE ROW LEVEL SECURITY;
