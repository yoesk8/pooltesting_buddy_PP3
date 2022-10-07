import os
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_readings")
def get_readings():
    # query database for home page named readings
    readings = mongo.db.readings.find()
    return render_template("readings.html", readings=readings)


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database to prevent duplicates
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "name": request.form.get("name"),
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the newly created user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("get_readings", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # check if password matches
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for("get_readings"))
            else:
                # invalid password
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Username and/or password doesn't exist")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_reading", methods=["GET", "POST"])
def add_reading():
    # Send user input reading to the reading table as a dictionary
    if request.method == "POST":
        outside_parameters = "on" if request.form.get(
            "outside_parameters") else "off"
        reading = {
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "pool_type": request.form.get("pool_type"),
            "free_chlorine": request.form.get("free_chlorine"),
            "total_chlorine": request.form.get("total_chlorine"),
            "combined_chlorine": request.form.get("combined_chlorine"),
            "ph": request.form.get("ph"),
            "water_temperature": request.form.get("water_temperature"),
            "outside_parameters": outside_parameters,
            "created_by": session["user"]

        }
        mongo.db.readings.insert_one(reading)
        flash("Reading succesfully added")
        return redirect(url_for("get_readings"))
    types = mongo.db.pool_type.find().sort("type", 1)
    return render_template("add_reading.html", types=types)


@app.route("/edit_reading/<reading_id>", methods=["GET", "POST"])
def edit_reading(reading_id):
    if request.method == "POST":
        outside_parameters = "on" if request.form.get(
            "outside_parameters") else "off"
        submit = {"$set": {
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "pool_type": request.form.get("pool_type"),
            "free_chlorine": request.form.get("free_chlorine"),
            "total_chlorine": request.form.get("total_chlorine"),
            "combined_chlorine": request.form.get("combined_chlorine"),
            "ph": request.form.get("ph"),
            "water_temperature": request.form.get("water_temperature"),
            "outside_parameters": outside_parameters,
            "created_by": session["user"]

        }}
        mongo.db.readings.update_one({"_id": ObjectId(reading_id)}, submit)
        flash("Reading succesfully updated")

    reading = mongo.db.readings.find_one({"_id": ObjectId(reading_id)})
    types = mongo.db.pool_type.find().sort("type", 1)
    return render_template("edit_reading.html", reading=reading, types=types)


@app.route("/delete_reading/<reading_id>")
def delete_reading(reading_id):
    # Delete selected reading from reading table in database
    mongo.db.readings.delete_one({"_id": ObjectId(reading_id)})
    flash("Reading succesfully deleted")
    return redirect(url_for("get_readings"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")), debug=False)
