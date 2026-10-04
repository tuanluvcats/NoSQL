from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from cassandra.cluster import Cluster

app = FastAPI()
templates = Jinja2Templates(directory="templates")
cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("probe")
q_rides = session.prepare("SELECT booked_at, status, fare FROM rides_by_customer WHERE customer_id = ?")

@app.get("/customers/{cid}/rides")
def rides(request: Request, cid: str):
    rows = list(session.execute(q_rides, [cid]))
    return templates.TemplateResponse(request, "rides.html", {"cid": cid, "rows": rows,
                                      "reactor": cluster.connection_class.__name__})
