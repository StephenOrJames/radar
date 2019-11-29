from flask import jsonify, render_template

from . import app, utils


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/airport/<code>")
def airport(code):
    """Return information about the airport with the specified ICAO code."""

    data = utils.get_airport_by_code(code)
    if data is None:
        return jsonify(status="Airport not found"), 404
    data["weather"] = utils.get_airport_weather(data["icao"])
    data["atc"] = utils.get_airport_atc(data["icao"])
    return jsonify(**data)


@app.route(
    "/aircraft"
    "/<float(signed=True):latitude>"
    "/<float(signed=True):longitude>"
    "/<int:distance>"
)
def aircraft(latitude, longitude, distance):
    """Return aircraft within the specified range of the specified coordinates."""

    if distance <= 0:
        return jsonify(status="The distance must be positive"), 400

    airport_coords = (latitude, longitude)
    nearby_aircraft = utils.get_nearby_aircraft(airport_coords, distance)
    return jsonify(aircraft=nearby_aircraft)
