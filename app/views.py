from flask import jsonify, render_template

from . import app, utils


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/airport/<icao>")
def airport(icao):
    """Given an airport's ICAO code,
    returns its coordinates.
    """

    coordinates = utils.get_airport_coordinates(icao)
    if coordinates is None:
        return jsonify(status="Not found"), 404

    weather = utils.get_airport_weather(icao)

    return jsonify(status="Success", coordinates=coordinates, weather=weather)


@app.route("/aircraft/<latitude>/<longitude>/<int:distance>")
def aircraft(latitude, longitude, distance):
    """Given an airport's coordinates,
    returns the callsign, distance, and angle of
    the nearest aircraft.
    """

    try:
        airport_lat = float(latitude)
        airport_lon = float(longitude)
    except ValueError as e:
        return jsonify(status="Invalid latitude and/or longitude values"), 400

    if distance <= 0:
        return jsonify(status="The distance must be positive"), 400

    airport_coords = (airport_lat, airport_lon)
    nearby_aircraft = utils.get_nearby_aircraft(airport_coords, distance)

    return jsonify(aircraft=nearby_aircraft)
