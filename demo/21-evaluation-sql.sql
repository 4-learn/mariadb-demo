-- Pure SQL qrels-style evaluation for fixed teaching cases.
-- Uses a derived table, so course_editor does not need CREATE TEMPORARY TABLE.
SELECT q.case_id,
       COUNT(q.relevant_chunk_id) AS relevant_count
FROM (
    SELECT 'Q01' AS case_id, 'C001' AS relevant_chunk_id
    UNION ALL SELECT 'Q02','C003'
    UNION ALL SELECT 'Q02','C004'
    UNION ALL SELECT 'Q04','C003'
    UNION ALL SELECT 'Q04','C004'
    UNION ALL SELECT 'Q06','C015'
    UNION ALL SELECT 'Q07','C013'
    UNION ALL SELECT 'Q07','C014'
    UNION ALL SELECT 'Q03',NULL
    UNION ALL SELECT 'Q05',NULL
    UNION ALL SELECT 'Q08',NULL
) AS q
GROUP BY q.case_id
ORDER BY q.case_id;
