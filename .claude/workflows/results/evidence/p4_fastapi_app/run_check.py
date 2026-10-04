import threading, time, urllib.request, sys, platform
import uvicorn, fastapi, jinja2
print("python", sys.version.split()[0], platform.system(), "| fastapi", fastapi.__version__, "| uvicorn", uvicorn.__version__, "| jinja2", jinja2.__version__)
server = uvicorn.Server(uvicorn.Config("main:app", host="127.0.0.1", port=8765, log_level="warning"))
t = threading.Thread(target=server.run, daemon=True); t.start()
for _ in range(60):
    if server.started: break
    time.sleep(0.5)
html = urllib.request.urlopen("http://127.0.0.1:8765/customers/CUST001/rides", timeout=20).read().decode()
print(html)
server.should_exit = True; t.join(10)
