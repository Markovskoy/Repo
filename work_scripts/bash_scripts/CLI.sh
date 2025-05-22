#!/bin/bash

. /home/oraupd/.bash_profile
bdauth=
bduser=
DBSID=""
ZBX_M="rc_cli_state"
ZBX_SENDER=$(`which zabbix_sender`)
ZBX_CONFIG="/etc/zabbix/zabbix_agentd.conf"
ZBX_HOST=$(hostname)


tmpfile=/tmp/$(uuidgen).tmp
F_TIME=$(($(date +%s)+30*60))

do_chek(){
$ORACLE_HOME/sqlplus -silent $bduser/$bdauth@$DBSID<<EOF

set echo off
set feedback off
set linesize 250
set pagesize 0
set trimspool on
set space 0
set truncate off

spool $tmpfile
------------------------
select nvl(status,'NO_DATA')  from (select sysdate from dual)
left join dba_scheduler_job_run_details on job_name='COMMLOG_INFORMATIKA_JOB' and trunc(log_date) = trunc(sysdate);
------------------------
spool off
EOF

RESULT=$(cat $tmpfile)
}
RESULT="NO_DATA"

while (true)
do
    do_chek
    [ "$RESULT" != "NO_DATA" ] && break
    [ "$(date +%s)" -gt "$F_TIME" ] && break
    sleep 10m
done
$ZBX_SENDER -s "$ZBX_HOST" -c "$ZBX_CONFIG" -k $ZBX_M -o "$RESULT"
rm -f $tmpfile
exit 0