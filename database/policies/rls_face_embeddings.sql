ALTER TABLE face_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "embeddings_no_public_access"
  ON face_embeddings FOR ALL TO anon USING (FALSE);

CREATE POLICY "embeddings_service_role"
  ON face_embeddings FOR ALL TO service_role USING (TRUE);
