import os
import redis
import jinja2
import secrets
import xlsxwriter
import aiohttp_jinja2
from aiohttp import web
from pytz import timezone
from datetime import datetime
from typing import Dict, Any, List

login_credentials: Dict[str, str] = {
    "root": "root",
    "admin": "admin"
}
active_sessions: Dict[str, Dict[str, Any]] = {}

app = web.Application()
routes = web.RouteTableDef()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('/root/WebApp/templates'))


def verify_user(username: str, password: str) -> bool:
    is_verified = False
    if username in login_credentials:
        is_verified = password == login_credentials[username]
    return is_verified


def get_students() -> List[Dict[str, str]]:
    students = []
    for key in redis_client.scan_iter("student:*"):
        student = redis_client.hgetall(key)
        decoded_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in student.items()}
        students.append(decoded_data)

    ip_count = {}
    for data_dict in students:
        ip_address = data_dict.get('ip_address')
        if ip_address in ip_count:
            ip_count[ip_address] += 1
        else:
            ip_count[ip_address] = 1

    for data_dict in students:
        ip_address = data_dict.get('ip_address')
        if ip_count[ip_address] > 1:
            data_dict['class'] = "error"
        else:
            data_dict['class'] = "ok"
    return students


@routes.get("/")
async def index(request: web.Request) -> web.Response:
    return aiohttp_jinja2.render_template('index.html', request, {})


@routes.get("/login")
async def login(request: web.Request) -> web.Response:
    return aiohttp_jinja2.render_template('login.html', request, {'error_message': 'Login to access private data!'})


@routes.get("/static/{path}")
async def static_dir(request: web.Request) -> web.Response:
    path = request.match_info['path']
    return web.FileResponse(f"/root/WebApp/static/{path}")


@routes.post("/")
async def get_results(request: web.Request) -> web.Response:
    data = await request.post()
    name = data["name"]
    enrollment_number = data["enrollment"]
    headers = request.headers
    ip_addr = headers.get('X-Forwarded-For')
    key = f"student:{enrollment_number}"
    redis_client.hset(key, "enrollment_number", enrollment_number)
    redis_client.hset(key, "name", name)
    redis_client.hset(key, "ip_address", ip_addr)
    return web.HTTPFound(location="/")


@routes.post("/login")
async def login(request: web.Request) -> web.Response:
    data = await request.post()
    username = data.get('username')
    password = data.get('password')

    if verify_user(username, password):
        session_token = secrets.token_hex(16)
        active_sessions[session_token] = {
            "username": username,
            "login_time": datetime.utcnow(),
        }
        response = web.HTTPFound('/results')
        response.set_cookie('session', session_token)
        return response
    else:
        return aiohttp_jinja2.render_template('login.html', request, {'error_message': 'Invalid credentials'})


@routes.get("/results")
async def results(request: web.Request) -> web.Response:
    session = request.cookies.get('session')
    if not session or session not in active_sessions:
        return web.HTTPFound('/login')
    session_data = active_sessions[session]

    login_time = session_data.get("login_time")
    current_time = datetime.utcnow()

    if (current_time - login_time).total_seconds() > 5:
        del active_sessions[session]
        return aiohttp_jinja2.render_template('login.html', request, {'error_message': 'Session has expired. Please log in again.'})

    students = get_students()
    sorted_list = sorted(students, key=lambda x: x['ip_address'])
    return aiohttp_jinja2.render_template('results.html', request, {'students': sorted_list, 'total': len(sorted_list)})


@routes.get("/export")
async def export(request: web.Request) -> web.Response:
    session = request.cookies.get('session')
    if not session or session not in active_sessions:
        return web.HTTPFound('/login')
    session_data = active_sessions[session]

    login_time = session_data.get("login_time")
    current_time = datetime.utcnow()

    if (current_time - login_time).total_seconds() > 5:
        del active_sessions[session]
        return aiohttp_jinja2.render_template('login.html', request, {'error_message': 'Session has expired. Please log in again.'})

    students = get_students()
    students = sorted(students, key=lambda x: x['enrollment_number'])
    now = datetime.now(tz=timezone("Asia/Kolkata"))
    file_name = f"export_dt{now.day}.{now.month}_{now.hour}.{now.minute}.xlsx"
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()
    red_format = workbook.add_format({'bg_color': '#febcb4'})
    worksheet.write_row(0, 0, ['Enrollment Number', 'Name', 'IP Address'])
    for row_num, row_data in enumerate(students, 1):
        if row_data['class'] == 'error':
            row_data.pop('class')
            worksheet.write_row(row_num, 0, row_data.values(), red_format)
        else:
            row_data.pop('class')
            worksheet.write_row(row_num, 0, row_data.values())
    workbook.close()
    response = web.FileResponse(path=file_name)
    response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


app.router.add_routes(routes)

if __name__ == "__main__":
    os.system("rm *.xlsx >/dev/null 2>&1")
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    redis_client.flushdb()
    web.run_app(app, host='0.0.0.0', port=5000)