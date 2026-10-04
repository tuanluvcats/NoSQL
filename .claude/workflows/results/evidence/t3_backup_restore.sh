# Run on host: bash t3_backup_restore.sh  (container nosql-cassandra, keyspace probe from t3_probe.cql)
C="docker exec nosql-cassandra"
# thu muc du lieu cua bang = <ten bang>-<id bang khong co dau ->; lay id tu system_schema de tranh thu muc cu cua bang da DROP
tdir(){ id=$($C cqlsh -e "SELECT id FROM system_schema.tables WHERE keyspace_name='probe' AND table_name='$1'" | sed -n '4p' | tr -d ' -'); echo "/var/lib/cassandra/data/probe/$1-$id"; }
set -x
$C cqlsh -e "SELECT COUNT(*) FROM probe.rides_by_driver;"
$C nodetool snapshot -t bk_drivers -kt probe.rides_by_driver
$C nodetool listsnapshots
$C cqlsh -e "TRUNCATE probe.rides_by_driver; SELECT COUNT(*) FROM probe.rides_by_driver;"
D=$(tdir rides_by_driver)
$C sh -c "ls $D/snapshots/ && ls $D/snapshots/bk_drivers"
$C nodetool import -cd probe rides_by_driver $D/snapshots/bk_drivers
$C cqlsh -e "SELECT driver_id, ride_id, vehicle_plate FROM probe.rides_by_driver;"
$C cqlsh -e "COPY probe.customers TO '/tmp/c.csv' WITH HEADER=true; TRUNCATE probe.customers; COPY probe.customers FROM '/tmp/c.csv' WITH HEADER=true; SELECT customer_id, TTL(full_name) FROM probe.customers;"
$C sh -c 'ls /opt/cassandra/bin; echo PATH=$PATH'
