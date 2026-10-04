import sys, platform
print("python", sys.version.split()[0], platform.system())
try:
    import cassandra
    print("driver", cassandra.__version__)
    from cassandra.cluster import Cluster
    print("connection_class:", Cluster.connection_class)
except Exception as e:
    print("IMPORT FAILED:", type(e).__name__, e)
    try:
        import cassandra.io.libevreactor
    except Exception as e2:
        print("  libev cause:", type(e2).__name__, str(e2)[:120])
    try:
        import cassandra.io.libevwrapper
    except Exception as e3:
        print("  libevwrapper cause:", type(e3).__name__, str(e3)[:160])
    sys.exit(0)
if len(sys.argv) > 1 and sys.argv[1] == "connect":
    c = Cluster(["127.0.0.1"], port=9042)
    s = c.connect()
    print("server:", s.execute("SELECT release_version, data_center FROM system.local").one())
    print("rows:", list(s.execute("SELECT customer_id, COUNT(*) AS n FROM probe.rides_by_customer GROUP BY customer_id")))
    r = s.execute("UPDATE probe.rides SET status='COMPLETED' WHERE ride_id=55555555-5555-5555-5555-555555555555 IF status='ONGOING'")
    print("LWT applied:", r.was_applied)
    c.shutdown()
