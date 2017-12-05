import json
import math
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# TODO: move URL variables up here as well
EARTH_RADIUS_NM = 3440 


def angle_between(dst_coord, src_coord):
    """Given a pair of coordinates on Earth,
    returns the angle from src to dst (in degrees).
    """

    lat_diff = dst_coord[0] - src_coord[0]
    lon_diff = dst_coord[1] - src_coord[1]

    angle = math.atan2(lon_diff, lat_diff)
    angle = math.degrees(angle)  # rad to deg
    angle = angle % 360  # handle negative

    return angle


def distance_between(coord1, coord2):
    """Given a pair of lat/lon coordinates on Earth (in degrees),
    return the distance between them (in nautical miles).

    It uses the haversine formula to estimate the distance.
    """

    lat1, lon1, lat2, lon2 = map(math.radians, (*coord1, *coord2))

    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1

    lat_sin2 = math.sin(lat_diff / 2) ** 2
    lon_sin2 = math.sin(lon_diff / 2) ** 2

    return 2 * EARTH_RADIUS_NM * math.asin(math.sqrt(
        lat_sin2 + math.cos(lat1) * math.cos(lat2) * lon_sin2
    ))


def get_airport_coordinates(icao):
    """Given an airport's ICAO code, returns its coordinates."""

    url = "https://openflights.org/php/apsearch.php"
    post_data = {"icao": icao}
    request = Request(url, urlencode(post_data).encode())
    with urlopen(request) as response:
        data = json.loads(response.read().decode())
    airports = data["airports"]

    if not airports:
        return None

    return {
        "latitude": float(airports[0]["y"]),
        "longitude": float(airports[0]["x"]),
    }


def get_airport_weather(icao):
    """Given an airport's ICAO code,
    returns some weather information about the location.
    """

    url = "https://aw.stephenorjames.com/api/retrieve/report/%s" % icao
    with urlopen(url) as response:
        data = json.loads(response.read().decode())

    return {
        "temperature": data["temperature"]["raw"],
        "wind": data["wind"]["raw"],
    }


def get_nearby_aircraft(airport_coords, max_distance):
    url = "https://opensky-network.org/api/states/all"
    with urlopen(url) as response:
        response_json = json.loads(response.read().decode())

    nearby_aircraft = []
    for state in response_json["states"]:
        if state[5] is None or state[6] is None:
            continue

        aircraft_lat = state[6]
        aircraft_lon = state[5]
        aircraft_coords = (aircraft_lat, aircraft_lon)
        aircraft_distance = distance_between(aircraft_coords, airport_coords)
        if aircraft_distance > max_distance:
            continue

        aircraft_angle = angle_between(aircraft_coords, airport_coords)

        nearby_aircraft.append({
            "callsign": state[1].strip(),
            "angle": round(aircraft_angle),
            "distance": round(aircraft_distance),
        })

    nearby_aircraft.sort(key=lambda a: a["distance"])

    return nearby_aircraft
