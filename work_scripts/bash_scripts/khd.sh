#!/bin/bash

. /home/oraupd/.bash_profile

bdauth=""
bduser=""
DBSID=""

ZBX_SENDER=$(which zabbix_sender)
ZBX_CONFIG="/etc/zabbix/zabbix_agentd.conf"
ZBX_HOST=$(hostname)

tmpfile=/tmp/$(uuidgen).tmp

$ORACLE_HOME/sqlplus -silent "$bduser/$bdauth@$DBSID" <<EOF
set echo off
set feedback off
set pagesize 0
set linesize 200
set trimspool on
set space 0
set truncate off
set colsep '|'

spool $tmpfile
------------------------
select 'report_form_ora' as key, 
       case 
         when count(rrl.report_log_id) = 0 then 'PROBLEM' 
         else 'OK' 
       end as value
from wms.rpt_report_log rrl
where rrl.report_alias='level_service_etl'
  and rrl.report_result is not null
  and (rrl.report_result like 'http://%' or rrl.report_result like 'https://%')
  and to_char(rrl.report_start_time,'ddmmyyyy AM') = to_char(sysdate,'ddmmyyyy AM')
union all
select 'khd__ls' as key,
       case 
         when count(1) = 0 then 'OK' 
         else 'PROBLEM' 
       end as value
from ETL.RPT_LEVELSERVICE_ETL_TBL;
------------------------
spool off
EOF

while IFS='|' read -r key value; do
  key=$(echo "$key" | xargs)
  value=$(echo "$value" | xargs)
  $ZBX_SENDER -s "$ZBX_HOST" -c "$ZBX_CONFIG" -k "$key" -o "$value"
done < "$tmpfile"

rm -f "$tmpfile"
exit 0
