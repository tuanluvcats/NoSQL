from cassandra.cluster import Cluster
from cassandra.io.asyncioreactor import AsyncioConnection
c = Cluster(["127.0.0.1"], connection_class=AsyncioConnection)
s = c.connect()
print("asyncio reactor ok:", s.execute("SELECT release_version FROM system.local").one())
c.shutdown()
