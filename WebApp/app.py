from flask import Flask, redirect, url_for, render_template, request, send_from_directory

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/static/<path:path>", methods=["GET"])
def static_dir(path):
    return send_from_directory("static", path)

@app.route("/", methods=["POST"])
def get_results():
    name = request.form["name"]
    enrollment_number = request.form["enrollment"]
    ip_addr = request.remote_addr
    print(name, enrollment_number, ip_addr)
    return redirect(url_for("index"))

@app.route("/results", methods=["GET"])
def results():
    students = [
        ("ok", "A", "B", "C"),
        ("ok", "D", "E", "F"),
        ("error", "G", "H", "I")
    ]
    return render_template("results.html", students=students)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

