BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'daily_salary_update',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN hr_utils.give_raise(1, 100); END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=10;',
        enabled         => TRUE
    );
END;