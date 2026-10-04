# second container c41-auth started with the yaml diff below mounted at /etc/cassandra/cassandra.yaml
#   authenticator: PasswordAuthenticator / authorizer: CassandraAuthorizer / materialized_views_enabled: true
#   env: CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch CASSANDRA_DC=HCM
set -x
docker exec c41-auth cqlsh -e "SELECT 1 FROM system.local"
docker exec c41-auth cqlsh -u cassandra -p cassandra -e "LIST ROLES; LIST ALL PERMISSIONS OF app_reader; SELECT keyspace_name, view_name FROM system_schema.views WHERE keyspace_name='ride_booking';"
docker exec c41-auth cqlsh -u app_reader -p 'Reader@123' -e "INSERT INTO ride_booking.rides (ride_id, status) VALUES (uuid(), 'REQUESTED')"
docker exec c41-auth nodetool status
docker exec c41-dconly nodetool status
docker exec c41-dconly grep -E "^dc|^endpoint_snitch" /etc/cassandra/cassandra-rackdc.properties /etc/cassandra/cassandra.yaml
