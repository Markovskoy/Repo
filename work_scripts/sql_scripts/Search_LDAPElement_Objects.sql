-- Джобы
SELECT 
    'SQL_AGENT_JOB' AS Object_Type,
    j.name AS Object_Name, 
    NULL AS Schema_Name, 
    js.command AS Object_Definition
FROM 
    msdb.dbo.sysjobs AS j
JOIN 
    msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.command LIKE '%*****%'
UNION ALL
-- Триггеры
SELECT 
    'TRIGGER' AS Object_Type,
    o.name AS Object_Name, 
    s.name AS Schema_Name, 
    m.definition AS Object_Definition
FROM 
    sys.sql_modules AS m
JOIN 
    sys.objects AS o ON m.object_id = o.object_id
JOIN 
    sys.schemas AS s ON o.schema_id = s.schema_id
WHERE 
    m.definition LIKE '%*****%'
    AND o.type = 'TR'
UNION ALL
-- Представления
SELECT 
    'VIEW' AS Object_Type,
    o.name AS Object_Name, 
    s.name AS Schema_Name, 
    m.definition AS Object_Definition
FROM 
    sys.sql_modules AS m
JOIN 
    sys.objects AS o ON m.object_id = o.object_id
JOIN 
    sys.schemas AS s ON o.schema_id = s.schema_id
WHERE 
    m.definition LIKE '%*****%'
    AND o.type = 'V'
UNION ALL
-- Процедуры и функции
SELECT 
    o.type_desc AS Object_Type,
    o.name AS Object_Name, 
    s.name AS Schema_Name, 
    m.definition AS Object_Definition
FROM 
    sys.sql_modules AS m
JOIN 
    sys.objects AS o ON m.object_id = o.object_id
JOIN 
    sys.schemas AS s ON o.schema_id = s.schema_id
WHERE 
    m.definition LIKE '%*****%'
    AND o.type IN ('P', 'FN', 'TF') 
ORDER BY 
    Object_Type, Schema_Name, Object_Name;