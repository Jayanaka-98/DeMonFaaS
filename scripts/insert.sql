-- Generating 100,000 unique names using 'Name_' prefix followed by row number
WITH RECURSIVE number_gen AS (
    SELECT 1 AS num
    UNION ALL
    SELECT num + 1
    FROM number_gen
    WHERE num < 100000
)
INSERT INTO read_heavy (read_name)
SELECT CONCAT('Name_', num) AS read_name
FROM number_gen;
