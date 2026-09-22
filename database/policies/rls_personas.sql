ALTER TABLE personas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "personas_select_authenticated"
  ON personas FOR SELECT TO authenticated USING (TRUE);

CREATE POLICY "personas_insert_admin"
  ON personas FOR INSERT TO authenticated
  WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "personas_update_admin"
  ON personas FOR UPDATE TO authenticated
  USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "personas_delete_admin"
  ON personas FOR DELETE TO authenticated
  USING (auth.jwt() ->> 'role' = 'admin');
