from flask import Flask, render_template, request, redirect, url_for
from models import db, Merchant

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///merchant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "<h1>Merchant Portal is running!</h1>"

@app.route("/add_merchant", methods=["GET", "POST"])
def add_merchant():
    if request.method == "POST":
        new_merchant = Merchant(
            name=request.form["name"],
            account_number=request.form["account_number"],
            city=request.form["city"],
            country_code=request.form["country_code"],
            category_code=request.form["category_code"],
            channel=request.form["channel"]
        )
        db.session.add(new_merchant)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_merchant.html")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
