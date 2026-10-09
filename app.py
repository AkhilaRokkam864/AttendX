from flask import (
    Flask, render_template, request,
    redirect, url_for, Response
)
import json
import os
import csv
import io
from datetime import date

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "students.json")


# ------------------------------------------
# DATA MANAGEMENT
# ------------------------------------------

def load_students():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(students, file, indent=4, ensure_ascii=False)


def valid_date(day_text):
    try:
        return date.fromisoformat(day_text) <= date.today()
    except (ValueError, TypeError):
        return False


def prepare_dashboard_data(selected_date=None):
    students = load_students()
    today = date.today().isoformat()

    if not selected_date or not valid_date(selected_date):
        selected_date = today

    present = 0
    absent = 0
    student_summaries = []

    total_present = 0
    total_absent = 0

    for student in students:
        attendance = student.get("attendance", {})

        status = attendance.get(selected_date, "Not marked")

        if status == "Present":
            present += 1
        elif status == "Absent":
            absent += 1

        history_present = sum(
            1 for day, value in attendance.items()
            if valid_date(day) and value == "Present"
        )

        history_absent = sum(
            1 for day, value in attendance.items()
            if valid_date(day) and value == "Absent"
        )

        total_present += history_present
        total_absent += history_absent

        history_total = history_present + history_absent

        student_summaries.append({
            **student,
            "today_status": status,
            "history_present": history_present,
            "history_absent": history_absent,
            "history_percentage": (
                round(history_present / history_total * 100)
                if history_total else 0
            )
        })

    total = len(students)
    marked = present + absent
    unmarked = total - marked
    total_marked = total_present + total_absent

    recorded_dates = sorted({
        day
        for student in students
        for day, status in student.get("attendance", {}).items()
        if status in ("Present", "Absent") and valid_date(day)
    }, reverse=True)

    return {
        "students": student_summaries,
        "total": total,
        "present": present,
        "absent": absent,
        "unmarked": unmarked,
        "marked": marked,
        "daily_percentage": round(present / marked * 100) if marked else 0,
        "total_present": total_present,
        "total_absent": total_absent,
        "overall_percentage": (
            round(total_present / total_marked * 100)
            if total_marked else 0
        ),
        "total_sessions": total_marked,
        "today": today,
        "selected_date": selected_date,
        "recorded_dates": recorded_dates
    }


# ------------------------------------------
# DASHBOARD
# ------------------------------------------

@app.route("/")
def dashboard():
    data = prepare_dashboard_data(request.args.get("date"))
    return render_template("index.html", **data)


# ------------------------------------------
# STUDENTS PAGE
# ------------------------------------------

@app.route("/students")
def students_page():
    data = prepare_dashboard_data()
    return render_template("students.html", **data)


@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    roll = request.form.get("roll", "").strip()
    selected_date = request.form.get(
        "selected_date", date.today().isoformat()
    )

    students = load_students()

    duplicate_roll = any(
        student.get("roll", "").casefold() == roll.casefold()
        for student in students
    )

    if name and roll and not duplicate_roll:
        students.append({
            "name": name,
            "roll": roll,
            "attendance": {}
        })
        save_students(students)

    destination = request.form.get("return_to", "dashboard")

    if destination == "students":
        return redirect(url_for("students_page"))

    return redirect(url_for("dashboard", date=selected_date))


@app.route("/delete/<roll>", methods=["POST"])
def delete_student(roll):
    students = [
        student for student in load_students()
        if student.get("roll") != roll
    ]

    save_students(students)

    destination = request.form.get("return_to", "dashboard")

    if destination == "students":
        return redirect(url_for("students_page"))

    return redirect(url_for(
        "dashboard",
        date=request.form.get("selected_date", date.today().isoformat())
    ))


# ------------------------------------------
# ATTENDANCE PAGE
# ------------------------------------------

@app.route("/attendance")
def attendance_page():
    data = prepare_dashboard_data(request.args.get("date"))
    return render_template("attendance.html", **data)


@app.route("/attendance/<roll>", methods=["POST"])
def mark_attendance(roll):
    selected_date = request.form.get(
        "date", date.today().isoformat()
    )
    status = request.form.get("status")

    if not valid_date(selected_date):
        return redirect(url_for("attendance_page"))

    if status not in ("Present", "Absent"):
        return redirect(url_for(
            "attendance_page", date=selected_date
        ))

    students = load_students()

    for student in students:
        if student.get("roll") == roll:
            student.setdefault("attendance", {})[selected_date] = status
            break

    save_students(students)

    destination = request.form.get("return_to", "attendance_page")

    if destination == "dashboard":
        return redirect(url_for("dashboard", date=selected_date))

    return redirect(url_for(
        "attendance_page", date=selected_date
    ))


# ------------------------------------------
# REPORTS PAGE
# ------------------------------------------

@app.route("/reports")
def reports_page():
    data = prepare_dashboard_data()
    return render_template("reports.html", **data)


@app.route("/export.csv")
def export_csv():
    students = load_students()

    recorded_dates = sorted({
        day
        for student in students
        for day, status in student.get("attendance", {}).items()
        if status in ("Present", "Absent") and valid_date(day)
    })

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Roll Number",
        "Student Name",
        *recorded_dates,
        "Present Days",
        "Absent Days",
        "Attendance Percentage"
    ])

    for student in students:
        attendance = student.get("attendance", {})

        present_count = sum(
            1 for day in recorded_dates
            if attendance.get(day) == "Present"
        )

        absent_count = sum(
            1 for day in recorded_dates
            if attendance.get(day) == "Absent"
        )

        total_marked = present_count + absent_count

        percentage = (
            round(present_count / total_marked * 100)
            if total_marked else 0
        )

        writer.writerow([
            student.get("roll", ""),
            student.get("name", ""),
            *[attendance.get(day, "") for day in recorded_dates],
            present_count,
            absent_count,
            f"{percentage}%"
        ])

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=attendx_attendance_report.csv"
    )

    return response


# ------------------------------------------
# MY ACCOUNT PAGE
# ------------------------------------------

@app.route("/account")
def account_page():
    data = prepare_dashboard_data()
    return render_template("account.html", **data)


# ------------------------------------------
# SETTINGS PAGE
# ------------------------------------------

@app.route("/settings")
def settings_page():
    data = prepare_dashboard_data()
    return render_template("settings.html", **data)


# ------------------------------------------
# RUN APPLICATION
# ------------------------------------------

if __name__ == "__main__":
    app.run(debug=False)