# Bo sung cho C12: incremental backup -> import, nodetool refresh, sstableloader, clearsnapshot.
# Chay tren host, ngay sau khi chay t3_probe.cql tren keyspace probe moi: bash t3_backup_restore2.sh
C="docker exec nosql-cassandra"
# thu muc du lieu cua bang = <ten bang>-<id bang khong co dau ->; lay id tu system_schema de tranh thu muc cu cua bang da DROP
tdir(){ id=$($C cqlsh -e "SELECT id FROM system_schema.tables WHERE keyspace_name='probe' AND table_name='$1'" | sed -n '4p' | tr -d ' -'); echo "/var/lib/cassandra/data/probe/$1-$id"; }
set -x
# don thu muc tam cua lan chay truoc
$C sh -c "rm -rf /tmp/incr /tmp/loader"
# --- 1. Incremental backup: bat bang nodetool (khong can sua yaml), ghi them, flush -> hard link trong backups/
$C nodetool statusbackup
$C nodetool enablebackup
$C nodetool statusbackup
$C cqlsh -e "INSERT INTO probe.rides_by_customer (customer_id, booked_at, ride_id, status, fare) VALUES ('CUST003', '2026-09-05 07:30:00+0000', 77777777-7777-7777-7777-777777777777, 'COMPLETED', 45000);"
$C nodetool flush probe rides_by_customer
T=$(tdir rides_by_customer)
$C sh -c "ls $T/backups/"
$C sh -c "mkdir -p /tmp/incr && cp $T/backups/* /tmp/incr/ && chown -R cassandra /tmp/incr"
$C cqlsh -e "TRUNCATE probe.rides_by_customer;"
$C nodetool import probe rides_by_customer /tmp/incr
$C cqlsh -e "SELECT customer_id, booked_at, fare FROM probe.rides_by_customer;"
$C nodetool disablebackup
# --- 2. nodetool refresh (deprecated tu 4.0): chep SSTable cua snapshot vao thu muc du lieu cua bang roi refresh
$C nodetool snapshot -t bk_refresh -kt probe.rides_by_driver
D=$(tdir rides_by_driver)
$C cqlsh -e "TRUNCATE probe.rides_by_driver; SELECT COUNT(*) FROM probe.rides_by_driver;"
$C sh -c "cp $D/snapshots/bk_refresh/nb-* $D/ && chown cassandra $D/nb-*"
$C nodetool refresh -- probe rides_by_driver
$C cqlsh -e "SELECT COUNT(*) FROM probe.rides_by_driver;"
# --- 3. sstableloader: thu muc nguon phai co dang .../<keyspace>/<table>/
$C nodetool snapshot -t bk_loader -kt probe.customers
K=$(tdir customers)
$C sh -c "mkdir -p /tmp/loader/probe/customers && cp $K/snapshots/bk_loader/nb-* /tmp/loader/probe/customers/"
$C cqlsh -e "TRUNCATE probe.customers; SELECT COUNT(*) FROM probe.customers;"
IP=$($C hostname -i | awk '{print $1}')
$C sstableloader -d $IP /tmp/loader/probe/customers
$C cqlsh -e "SELECT customer_id, full_name, phones FROM probe.customers;"
# --- 4. Don dep snapshot
$C nodetool listsnapshots
$C nodetool clearsnapshot -t bk_loader -- probe
$C nodetool clearsnapshot --all -- probe
$C nodetool listsnapshots
