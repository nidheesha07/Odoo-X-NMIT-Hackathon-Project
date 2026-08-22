from datetime import datetime, date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import db
from salary import compute_salary

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-to-a-random-secret-key"  # used to keep sessions secure
db.init_app(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("You do not have permission to view that page.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def get_user_by_id(user_id):
    return db.get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "employee")

        errors = []
        if not employee_id or not name or not email or not password:
            errors.append("All fields are required.")
        if "@" not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if role not in ("employee", "admin"):
            role = "employee"

        conn = db.get_db()
        if not errors:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ? OR employee_id = ?",
                (email, employee_id),
            ).fetchone()
            if existing:
                errors.append("An account with that email or employee ID already exists.")

        if errors:
            for e in errors:
                flash(e)
            return render_template("signup.html", form=request.form)

        password_hash = generate_password_hash(password)
        cur = conn.execute(
            """INSERT INTO users (employee_id, name, email, password_hash, role)
               VALUES (?, ?, ?, ?, ?)""",
            (employee_id, name, email, password_hash, role),
        )
        conn.commit()
        user_id = cur.lastrowid

        # every new employee gets an empty salary row so later lookups never fail
        conn.execute(
            "INSERT INTO salary (user_id, monthly_wage, pf_rate, professional_tax) VALUES (?, 0, 12, 200)",
            (user_id,),
        )
        conn.commit()

        flash("Account created successfully. Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = db.get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = db.get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None:
            flash("No account found with that email address.")
            return render_template("forgot_password.html")

        return render_template(
            "reset_password.html",
            email=email
        )

    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["POST"])
def reset_password():
    email = request.form.get("email", "").strip().lower()
    new_password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if len(new_password) < 6:
        flash("Password must be at least 6 characters long.")
        return render_template("reset_password.html", email=email)

    if new_password != confirm_password:
        flash("Passwords do not match.")
        return render_template("reset_password.html", email=email)

    conn = db.get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if user is None:
        flash("No account found with that email address.")
        return redirect(url_for("forgot_password"))

    new_password_hash = generate_password_hash(new_password)

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (new_password_hash, email)
    )

    conn.commit()

    flash("Password changed successfully. Please log in.")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    conn = db.get_db()
    user = get_user_by_id(session["user_id"])

    if session["role"] == "admin":
        employee_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        pending_leaves = conn.execute(
            "SELECT COUNT(*) AS c FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()["c"]
        today_attendance = conn.execute(
            "SELECT COUNT(*) AS c FROM attendance WHERE date = ?", (date.today().isoformat(),)
        ).fetchone()["c"]
        return render_template(
            "dashboard.html",
            user=user,
            employee_count=employee_count,
            pending_leaves=pending_leaves,
            today_attendance=today_attendance,
        )

    today = date.today().isoformat()
    today_row = conn.execute(
        "SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user["id"], today)
    ).fetchone()
    my_pending_leaves = conn.execute(
        "SELECT COUNT(*) AS c FROM leave_requests WHERE user_id = ? AND status = 'Pending'",
        (user["id"],),
    ).fetchone()["c"]
    return render_template(
        "dashboard.html", user=user, today_row=today_row, my_pending_leaves=my_pending_leaves
    )


# ---------------------------------------------------------------------------
# Profile: Private Info + Salary Info
# ---------------------------------------------------------------------------

PRIVATE_FIELDS = [
    "dob", "address", "nationality", "personal_email", "gender",
    "marital_status", "date_of_joining", "bank_account", "bank_name",
    "ifsc_code", "pan_no", "uan_no",
]


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = db.get_db()
    user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        values = {field: request.form.get(field, "").strip() for field in PRIVATE_FIELDS}
        mobile = request.form.get("mobile", "").strip()

        conn.execute(
            """UPDATE users SET mobile = ?, dob = ?, address = ?, nationality = ?,
               personal_email = ?, gender = ?, marital_status = ?, date_of_joining = ?,
               bank_account = ?, bank_name = ?, ifsc_code = ?, pan_no = ?, uan_no = ?
               WHERE id = ?""",
            (
                mobile, values["dob"], values["address"], values["nationality"],
                values["personal_email"], values["gender"], values["marital_status"],
                values["date_of_joining"], values["bank_account"], values["bank_name"],
                values["ifsc_code"], values["pan_no"], values["uan_no"], user["id"],
            ),
        )
        conn.commit()
        flash("Profile updated.")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user, tab="private")

RESUME_FIELDS = ["about", "job_love", "hobbies"]


@app.route("/profile/resume", methods=["GET", "POST"])
@login_required
def profile_resume():
    conn = db.get_db()
    user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        values = {field: request.form.get(field, "").strip() for field in RESUME_FIELDS}
        conn.execute(
            "UPDATE users SET about = ?, job_love = ?, hobbies = ? WHERE id = ?",
            (values["about"], values["job_love"], values["hobbies"], user["id"]),
        )
        conn.commit()
        flash("Resume updated.")
        return redirect(url_for("profile_resume"))

    skills = conn.execute(
        "SELECT * FROM skills WHERE user_id = ? ORDER BY id", (user["id"],)
    ).fetchall()
    certifications = conn.execute(
        "SELECT * FROM certifications WHERE user_id = ? ORDER BY id", (user["id"],)
    ).fetchall()
    return render_template(
        "profile.html", user=user, tab="resume", skills=skills, certifications=certifications
    )


@app.route("/profile/resume/skills/add", methods=["POST"])
@login_required
def add_skill():
    skill_name = request.form.get("skill_name", "").strip()
    if skill_name:
        db.get_db().execute(
            "INSERT INTO skills (user_id, skill_name) VALUES (?, ?)",
            (session["user_id"], skill_name),
        )
        db.get_db().commit()
    return redirect(url_for("profile_resume"))


@app.route("/profile/resume/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
def delete_skill(skill_id):
    # only delete if it belongs to the logged-in user
    db.get_db().execute(
        "DELETE FROM skills WHERE id = ? AND user_id = ?", (skill_id, session["user_id"])
    )
    db.get_db().commit()
    return redirect(url_for("profile_resume"))


@app.route("/profile/resume/certifications/add", methods=["POST"])
@login_required
def add_certification():
    certification_name = request.form.get("certification_name", "").strip()
    if certification_name:
        db.get_db().execute(
            "INSERT INTO certifications (user_id, certification_name) VALUES (?, ?)",
            (session["user_id"], certification_name),
        )
        db.get_db().commit()
    return redirect(url_for("profile_resume"))


@app.route("/profile/resume/certifications/<int:cert_id>/delete", methods=["POST"])
@login_required
def delete_certification(cert_id):
    db.get_db().execute(
        "DELETE FROM certifications WHERE id = ? AND user_id = ?", (cert_id, session["user_id"])
    )
    db.get_db().commit()
    return redirect(url_for("profile_resume"))


@app.route("/profile/salary")
@login_required
def profile_salary():
    conn = db.get_db()
    user = get_user_by_id(session["user_id"])
    salary_row = conn.execute("SELECT * FROM salary WHERE user_id = ?", (user["id"],)).fetchone()
    salary = compute_salary(
        salary_row["monthly_wage"], salary_row["pf_rate"], salary_row["professional_tax"]
    )
    return render_template("profile.html", user=user, tab="salary", salary=salary)


# ---------------------------------------------------------------------------
# Admin: employee list + editing another employee's info / salary
# ---------------------------------------------------------------------------

@app.route("/admin/employees")
@admin_required
def admin_employees():
    conn = db.get_db()
    employees = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    return render_template("admin_employees.html", employees=employees)


@app.route("/admin/employee/<int:emp_id>/salary", methods=["GET", "POST"])
@admin_required
def admin_employee_salary(emp_id):
    conn = db.get_db()
    employee = get_user_by_id(emp_id)
    if employee is None:
        flash("Employee not found.")
        return redirect(url_for("admin_employees"))

    if request.method == "POST":
        wage = request.form.get("monthly_wage", "0")
        pf_rate = request.form.get("pf_rate", "12")
        professional_tax = request.form.get("professional_tax", "200")

        errors = []
        try:
            wage = float(wage)
            if wage < 0:
                errors.append("Wage cannot be negative.")
        except ValueError:
            errors.append("Wage must be a number.")
        try:
            pf_rate = float(pf_rate)
        except ValueError:
            errors.append("PF rate must be a number.")
        try:
            professional_tax = float(professional_tax)
        except ValueError:
            errors.append("Professional tax must be a number.")

        if errors:
            for e in errors:
                flash(e)
        else:
            conn.execute(
                "UPDATE salary SET monthly_wage = ?, pf_rate = ?, professional_tax = ? WHERE user_id = ?",
                (wage, pf_rate, professional_tax, emp_id),
            )
            conn.commit()
            flash("Salary updated.")
            return redirect(url_for("admin_employee_salary", emp_id=emp_id))

    salary_row = conn.execute("SELECT * FROM salary WHERE user_id = ?", (emp_id,)).fetchone()
    salary = compute_salary(
        salary_row["monthly_wage"], salary_row["pf_rate"], salary_row["professional_tax"]
    )
    return render_template("admin_salary.html", employee=employee, salary=salary, salary_row=salary_row)


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    conn = db.get_db()
    user_id = session["user_id"]
    today = date.today().isoformat()

    if request.method == "POST":
        action = request.form.get("action")
        now = datetime.now().strftime("%H:%M:%S")
        row = conn.execute(
            "SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today)
        ).fetchone()

        if action == "check_in":
            if row is None:
                conn.execute(
                    "INSERT INTO attendance (user_id, date, check_in, status) VALUES (?, ?, ?, 'Present')",
                    (user_id, today, now),
                )
            else:
                flash("You have already checked in today.")
        elif action == "check_out":
            if row is not None and row["check_out"] == "":
                conn.execute(
                    "UPDATE attendance SET check_out = ? WHERE id = ?", (now, row["id"])
                )
            else:
                flash("You need to check in before you can check out.")
        conn.commit()
        return redirect(url_for("attendance"))

    my_records = conn.execute(
        "SELECT * FROM attendance WHERE user_id = ? ORDER BY date DESC LIMIT 30", (user_id,)
    ).fetchall()
    today_row = conn.execute(
        "SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user_id, today)
    ).fetchone()
    return render_template("attendance.html", records=my_records, today_row=today_row)


@app.route("/admin/attendance")
@admin_required
def admin_attendance():
    conn = db.get_db()
    records = conn.execute(
        """SELECT attendance.*, users.name AS employee_name
           FROM attendance JOIN users ON attendance.user_id = users.id
           ORDER BY attendance.date DESC LIMIT 100"""
    ).fetchall()
    return render_template("admin_attendance.html", records=records)


# ---------------------------------------------------------------------------
# Leave / Time-Off
# ---------------------------------------------------------------------------

@app.route("/leave", methods=["GET", "POST"])
@login_required
def leave():
    conn = db.get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        leave_type = request.form.get("leave_type", "")
        start_date = request.form.get("start_date", "")
        end_date = request.form.get("end_date", "")
        remarks = request.form.get("remarks", "").strip()

        errors = []
        if leave_type not in ("Paid", "Sick", "Unpaid"):
            errors.append("Please choose a valid leave type.")
        if not start_date or not end_date:
            errors.append("Please choose both a start and an end date.")
        elif start_date > end_date:
            errors.append("The start date must be before the end date.")

        if errors:
            for e in errors:
                flash(e)
        else:
            conn.execute(
                """INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, remarks)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, leave_type, start_date, end_date, remarks),
            )
            conn.commit()
            flash("Leave request submitted.")
        return redirect(url_for("leave"))

    my_requests = conn.execute(
        "SELECT * FROM leave_requests WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    return render_template("leave.html", requests=my_requests)


@app.route("/admin/leave", methods=["GET", "POST"])
@admin_required
def admin_leave():
    conn = db.get_db()

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        decision = request.form.get("decision")
        comment = request.form.get("admin_comment", "").strip()
        if decision in ("Approved", "Rejected"):
            conn.execute(
                "UPDATE leave_requests SET status = ?, admin_comment = ? WHERE id = ?",
                (decision, comment, leave_id),
            )
            conn.commit()
            flash(f"Leave request {decision.lower()}.")
        return redirect(url_for("admin_leave"))

    all_requests = conn.execute(
        """SELECT leave_requests.*, users.name AS employee_name
           FROM leave_requests JOIN users ON leave_requests.user_id = users.id
           ORDER BY leave_requests.status = 'Pending' DESC, leave_requests.id DESC"""
    ).fetchall()
    return render_template("admin_leave.html", requests=all_requests)


if __name__ == "__main__":
    app.run(debug=True)