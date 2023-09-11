import redis 
import jinja2
import aiohttp_jinja2
from aiohttp import web


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))  

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    return aiohttp_jinja2.render_template('index.html', request, {})

@routes.get("/static/{path}")
async def static_dir(request):
    path = request.match_info['path']
    return web.FileResponse(f"static/{path}")

@routes.post("/")
async def get_results(request):
    data = await request.post()
    name = data["name"]
    enrollment_number = data["enrollment"]
    ip_addr = request.remote
    key = f"student:{enrollment_number}"
    redis_client.hset(key, "enrollment_number", enrollment_number)
    redis_client.hset(key, "name", name)
    redis_client.hset(key, "ip_address", ip_addr)
    return web.HTTPFound(location="/")

@routes.get("/results")
async def results(request):
    all_keys_and_values = {}

    for key in redis_client.scan_iter("*"): 
        key_str = key.decode("utf-8")
        value = redis_client.get(key_str).decode("utf-8")
        all_keys_and_values[key_str] = value

    for key, value in all_keys_and_values.items():
        print(f"Key: {key}, Value: {value}")

    students = [
        ("ok", "A", "B", "C"),
        ("ok", "D", "E", "F"),
        ("error", "G", "H", "Isdf")
    ]
    return aiohttp_jinja2.render_template('results.html', request, {'students':students})

app.router.add_routes(routes)

if __name__ == "__main__":
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    redis_client.flushdb()
    web.run_app(app, host='0.0.0.0', port=8000)