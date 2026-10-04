import logging; logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
print("--- A: Cluster(['127.0.0.1']) with no policy")
c = Cluster(["127.0.0.1"]); s = c.connect(); print("protocol_version:", c.protocol_version); c.shutdown()
print("--- B: explicit local_dc='datacenter1'")
prof = ExecutionProfile(load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc="datacenter1")))
c = Cluster(["127.0.0.1"], execution_profiles={EXEC_PROFILE_DEFAULT: prof}); s = c.connect(); print("protocol_version:", c.protocol_version); c.shutdown()
