from flask import Flask, render_template, request, redirect, url_for, session, send_file
import uuid, datetime, os, csv, qrcode
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = "gadaa_secure_key"

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- In-Memory Data ----------------
users = {
    "admin@gadaa.com": {"role": "admin", "password": "admin123", "status": "active",
                        "first_name": "System", "last_name": "Admin", "phone_number": "0000000000", "branch": "HQ"},
    "ops@gadaa.com": {"role": "ops", "password": "ops123", "status": "active",
                      "first_name": "Ops", "last_name": "Staff", "phone_number": "1111111111", "branch": "HQ"},
    "merchant@gadaa.com": {"role": "merchant", "password": "merchant123", "status": "active",
                           "first_name": "Merchant", "last_name": "User", "phone_number": "2222222222", "branch": "HQ"}
}

merchants, transactions, audit_logs, qr_reports = [], [], [], []

# ---------------- Role Decorator ----------------
def role_required(role):
    def wrapper(func):
        def decorated_function(*args, **kwargs):
            if "user" not in session or users[session["user"]]["role"] != role:
                return "Access Denied", 403
            return func(*args, **kwargs)
        decorated_function.__name__ = func.__name__
        return decorated_function
    return wrapper

def log_action(action):
    audit_logs.append({
        "user": session.get("user"),
        "action": action,
        "time": datetime.datetime.now()
    })

@app.context_processor
def inject_role():
    role = None
    if "user" in session:
        role = users[session["user"]]["role"]
    return dict(current_role=role)

# ---------------- Home/Login ----------------
@app.route("/")
def home():
    if "user" in session:
        role = users[session["user"]]["role"]
        if role == "admin":
            return redirect(url_for("admin_home"))
        elif role == "ops":
            return redirect(url_for("ops_dashboard"))
        elif role == "merchant":
            return redirect(url_for("merchant_dashboard"))
    return redirect(url_for("login_page"))

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email, password = request.form["email"], request.form["password"]
    if email in users and users[email]["password"] == password and users[email]["status"] == "active":
        session["user"] = email
        log_action(f"Login by {email}")
        return redirect(url_for("home"))
    return render_template("login.html", error="Invalid credentials or inactive user")

@app.route("/logout")
def logout():
    log_action(f"Logout by {session.get('user')}")
    session.pop("user", None)
    return redirect(url_for("login_page"))

# ---------------- Admin Dashboard ----------------
@app.route("/admin_home")
@role_required("admin")
def admin_home():
    return render_template("admin_home.html")

@app.route("/admin_dashboard")
@role_required("admin")
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        users=users,
        merchants=merchants,
        transactions=transactions,
        qr_reports=qr_reports,
        audit_logs=audit_logs
    )

@app.route("/admin_add_user", methods=["GET", "POST"])
@role_required("admin")
def admin_add_user():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        status = request.form.get("status", "active")

        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name", "")
        last_name = request.form["last_name"]
        phone_number = request.form["phone_number"]
        branch = request.form.get("branch", "")

        if email not in users:
            users[email] = {
                "role": role,
                "password": password,
                "status": status,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "branch": branch
            }
            log_action(f"Admin created user {email} ({first_name} {last_name}) with role {role}")
        else:
            return "User already exists", 400

        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_user.html")

@app.route("/admin_edit_user/<email>", methods=["GET", "POST"])
@role_required("admin")
def admin_edit_user(email):
    if email not in users:
        return "User not found", 404
    if request.method == "POST":
        new_status = request.form["status"]
        users[email]["status"] = new_status
        log_action(f"Admin changed status of {email} to {new_status}")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_edit_user.html", email=email, user=users[email])

@app.route("/admin_reports", methods=["GET", "POST"])
@role_required("admin")
def admin_reports():
    filtered_merchants = merchants
    filtered_transactions = transactions
    filtered_qr = qr_reports

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        if start_date and end_date:
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

            filtered_merchants = [m for m in merchants if m.get("id_issue_date") and start <= datetime.datetime.strptime(m["id_issue_date"], "%Y-%m-%d").date() <= end]
            filtered_transactions = [t for t in transactions if t.get("date") and start <= t["date"] <= end]
            filtered_qr = [q for q in qr_reports if q.get("generated_at") and start <= q["generated_at"].date() <= end]

    return render_template("admin_reports.html",
                           merchants=filtered_merchants,
                           transactions=filtered_transactions,
                           qr_reports=filtered_qr)

@app.route("/admin_audit")
@role_required("admin")
def admin_audit():
    return render_template("audit_logs.html", audit_logs=audit_logs)

@app.route("/services")
@role_required("admin")
def services():
    return render_template("services.html")

# ---------------- Ops Dashboard ----------------
@app.route("/ops_dashboard", methods=["GET", "POST"])
@role_required("ops")
def ops_dashboard():
    if request.method == "POST":
        tx_id = str(uuid.uuid4())[:8]
        transactions.append({
            "id": tx_id,
            "merchant_id": request.form.get("merchant_id"),
            "amount": float(request.form["amount"]),
            "description": request.form["description"],
            "date": datetime.date.today()
        })
        log_action(f"Transaction added {tx_id}")
        return redirect(url_for("ops_dashboard"))
    return render_template("ops_dashboard.html", transactions=transactions, merchants=merchants)

@app.route("/export_transactions")
@role_required("ops")
def export_transactions():
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], "transactions.csv")
    with open(filepath, "w", newline="", encoding="utf-8", errors="ignore") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Merchant ID", "Amount", "Description", "Date"])
        for t in transactions:
            writer.writerow([t["id"], t.get("merchant_id",""), t["amount"], t["description"], t["date"]])
    log_action("Transactions exported")
    return f"Transactions exported to {filepath}"

# ---------------- Merchant Dashboard ----------------
@app.route("/merchant_dashboard")
@role_required("merchant")
def merchant_dashboard():
    merchant_id = None
    for m in merchants:
        if m["email"] == session["user"]:
            merchant_id = m["id"]
    merchant_tx = [t for t in transactions if t.get("merchant_id") == merchant_id]
    return render_template("merchant_dashboard.html", merchants=merchants, transactions=merchant_tx)

@app.route("/merchant_register", methods=["GET", "POST"])
@role_required("merchant")
def merchant_register():
    if request.method == "POST":
        # Generate numerical merchant ID
        merchant_id = str(len(merchants) + 10001)

        # Mandatory fields check
        required_fields = [
            "first_name", "last_name", "national_id",
            "id_issue_date", "id_expiry_date", "full_address",
            "phone_number", "business_type", "business_name",
            "account_number", "tin_number"
        ]
        for field in required_fields:
            if not request.form.get(field):
                return f"Error: {field.replace('_',' ').title()} is required", 400


        new_merchant = {
            "id": merchant_id,
            "first_name": request.form["first_name"],
            "middle_name": request.form.get("middle_name", ""),
            "last_name": request.form["last_name"],
            "id_number": request.form["national_id"],
            "id_issue_date": request.form["id_issue_date"],
            "id_expiry_date": request.form["id_expiry_date"],
            "full_address": request.form["full_address"],
            "phone_number": request.form["phone_number"],
            "business_type": request.form["business_type"],
            "business_name": request.form["business_name"],
            "account_number": request.form["account_number"],
            "tin_number": request.form["tin_number"],
            "email": session["user"],
            "status": "Active",
            "documents": []
        }

        # Handle license upload
        if "license" in request.files:
            file = request.files["license"]
            if file.filename:
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(filepath)
                new_merchant["documents"].append(file.filename)

        merchants.append(new_merchant)
        log_action(f"Merchant registered {merchant_id}")
        return redirect(url_for("merchant_list"))

    return render_template("merchant_register.html")

@app.route("/merchant_list")
@role_required("merchant")
def merchant_list():
    return render_template("merchant_list.html", merchants=merchants)

@app.route("/merchant_reports")
@role_required("merchant")
def merchant_reports():
    merchant_id = None
    for m in merchants:
        if m["email"] == session["user"]:
            merchant_id = m["id"]
    merchant_tx = [t for t in transactions if t.get("merchant_id") == merchant_id]
    merchant_qr = [q for q in qr_reports if q.get("merchant_id") == merchant_id]
    return render_template("merchant_reports.html", merchants=merchants, transactions=merchant_tx, qr_reports=merchant_qr)

# ---------------- Generate QR ----------------
@app.route("/generate_qr", methods=["GET", "POST"])
@role_required("merchant")
def generate_qr():
    if request.method == "POST":
        merchant = next((m for m in merchants if m["email"] == session["user"]), None)
        if not merchant:
            return "Merchant not found", 404

        merchant_id = request.form.get("merchant_id", merchant["id"])

        # Fixed EMV QR payload string
        emv_string = "00020101021126340005GADAA0107ETSETAA02101234567890520454115303230540410005502015802ET5906motuma6011Addis abeba61041000623002100933390962040412350504234564140002hi0104leul630494FC"

        # Generate QR
        qr_img = qrcode.make(emv_string).convert("RGBA")

        # Extend canvas upward for logo + downward for merchant details
        new_height = qr_img.size[1] + 180
        canvas = Image.new("RGBA", (qr_img.size[0], new_height), "WHITE")

        # Add Gadaa logo at top center
        logo_path = os.path.join("static", "gadaa_logo.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = int(qr_img.size[0] * 0.20)
            logo = logo.resize((logo_size, logo_size))
            logo_pos = ((canvas.size[0] - logo.size[0]) // 2, 10)
            canvas.paste(logo, logo_pos, mask=logo)

        # Paste QR below logo
        qr_pos_y = logo.size[1] + 20
        canvas.paste(qr_img, (0, qr_pos_y))

        # Draw merchant details at bottom-right
        draw = ImageDraw.Draw(canvas)
        font_path = os.path.join("static", "arial.ttf")
        try:
            font = ImageFont.truetype(font_path, 16)
        except:
            font = ImageFont.load_default()

        details = f"{merchant['business_name']} | ID: {merchant_id}\nAcct: {merchant['account_number']} | Bank: Gadaa Bank"
        bbox = draw.multiline_textbbox((0, 0), details, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.multiline_text((canvas.size[0] - text_w - 10, qr_pos_y + qr_img.size[1] + 10),
                            details, fill="black", font=font)

        filename = f"qr_{uuid.uuid4().hex}.png"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        canvas.save(filepath)

        # Log QR generation in reports
        qr_reports.append({
            "id": str(uuid.uuid4())[:8],
            "merchant_id": merchant_id,
            "code_value": emv_string,
            "generated_at": datetime.datetime.now(),
            "file": filename
        })

        log_action(f"QR generated for merchant {merchant_id}")
        return render_template("generate_qr.html", qr_file=filename)

    return render_template("generate_qr.html")

# ---------------- File Download ----------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename))

# ---------------- Support Page ----------------
@app.route("/support")
def support():
    return render_template("support.html")

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
