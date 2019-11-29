import math
import re

import requests


EARTH_RADIUS_NM = 3440 

AIRCRAFT_STATES_URL = "https://opensky-network.org/api/states/all"
AIRPORT_SEARCH_URL = "https://openflights.org/php/apsearch.php"
ATC_FEEDS_URL = "https://m.liveatc.net/feeds/?icao={icao}"
WEATHER_REPORT_URL = "https://aw.stephenorjames.com/api/retrieve/report/{icao}"

USER_AGENT_HEADER = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"


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


def get_airport_by_code(code):
    """Return the airport's name, IATA code ICAO code, and coordinates."""

    code_type = "iata" if len(code) == 3 else "icao"
    response = requests.post(AIRPORT_SEARCH_URL, data={code_type: code})
    airports = response.json().get("airports")
    if airports is None:
        return None

    airport = airports[0]
    return {
        "name": airport["name"],
        "iata": airport["iata"],
        "icao": airport["icao"],
        "coordinates": {
            "latitude": float(airport["y"]),
            "longitude": float(airport["x"]),
        },
    }


def get_airport_weather(icao):
    """Given an airport's ICAO code,
    returns some weather information about the location.
    """

    response = requests.get(WEATHER_REPORT_URL.format(icao=icao))
    data = response.json()

    return {
        "temperature": data["temperature"]["raw"],
        "wind": data["wind"]["raw"],
    }


def get_nearby_aircraft(airport_coords, max_distance):
    # 1 degree is approx. 60nm, so overestimate for completeness.
    degrees_delta = max_distance / 58
    bounding_box = {
        "lamin": airport_coords[0] - degrees_delta,
        "lamax": airport_coords[0] + degrees_delta,
        "lomin": airport_coords[1] - degrees_delta,
        "lomax": airport_coords[1] + degrees_delta,
    }

    # API does not support wrapping across the 180th meridian.
    # We'd need to do that manually.
    use_bounding_box = (
        bounding_box["lomin"] > -180 and bounding_box["lomax"] < 180
    )

    response = requests.get(
        AIRCRAFT_STATES_URL,
        params=bounding_box if use_bounding_box else {},
    )
    aircraft = response.json()
    if aircraft["states"] is None:
        return []

    nearby_aircraft = []
    for state in aircraft["states"]:
        aircraft_lat = state[6]
        aircraft_lon = state[5]

        if aircraft_lat is None or aircraft_lon is None:
            continue

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


def get_airport_atc(icao):
    response = requests.get(
        ATC_FEEDS_URL.format(icao=icao),
        headers={"User-Agent": USER_AGENT_HEADER},
    )
    feeds = re.findall(
        '<a href="(http://d.liveatc.net/.+)">(.+)</a>',
        response.text,
    )
    return [
        {'url': feed[0], 'title': feed[1]}
        for feed in feeds
    ]
