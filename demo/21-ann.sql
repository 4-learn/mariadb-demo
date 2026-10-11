-- Run ONCE as course_editor after lesson 19. DDL has an implicit commit.
ALTER TABLE chunk_vectors
    ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;
-- Execute search --explain --mode exact and --mode ann with a real query vector.
-- FORCE INDEX is a request, not proof: retain the actual EXPLAIN key/Extra.
