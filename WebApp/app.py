import os 
import redis 
import jinja2
import datetime 
import xlsxwriter
import aiohttp_jinja2
from aiohttp import web
from pytz import timezone


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("/root/WebApp/templates"))  

routes = web.RouteTableDef()


def get_students():
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
async def index(request):
    return aiohttp_jinja2.render_template('index.html', request, {})


@routes.get("/static/{path}")
async def static_dir(request):
    path = request.match_info['path']
    return web.FileResponse(f"/root/WebApp/static/{path}")


@routes.post("/")
async def get_results(request):
    data = await request.post()
    name = data["name"]
    enrollment_number = data["enrollment"]
    headers = request.headers
    ip_addr = headers.get('X-Forwarded-For')
    print(ip_addr, name, enrollment_number)
    key = f"student:{enrollment_number}"
    redis_client.hset(key, "enrollment_number", enrollment_number)
    redis_client.hset(key, "name", name)
    redis_client.hset(key, "ip_address", ip_addr)
    return web.HTTPFound(location="/")


@routes.get("/results")
async def results(request):
    auth_header = request.headers.get('auth')
    if not auth_header:
        return web.HTTPFound('/login')
    students = get_students()  
    sorted_list = sorted(students, key=lambda x: x['ip_address'])
    return aiohttp_jinja2.render_template('results.html', request, {'students':sorted_list, 'total':len(sorted_list)})


@routes.get("/export")
async def export(request):
    students = get_students()
    students = sorted(students, key=lambda x: x['enrollment_number'])
    now = datetime.datetime.now(tz=timezone("Asia/Kolkata"))
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
    try: os.system("rm *.xlsx")
    except: pass
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    redis_client.flushdb()
    web.run_app(app, host='0.0.0.0', port=5000)
