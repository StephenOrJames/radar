var airport;
var aircraft;
var radar;


function setup() {
  createCanvas(815, 815);
  frameRate(60);

  airport = {
    icao: "KBUF",
    _nextIcao: "",
    valid: false,
  };
  loadAirport(airport.icao);

  // No aircraft initially
  aircraft = {
    next: [],
    current: [],
    last : [],
  };

  radar = {
    angle: 0,
    blip: createImage(8, 8),
    _blips: [],
    color: color(81, 255, 13),
    colorInvalid: color("red"),  // used to indicate invalid airports
    distance: 100,  // max aircraft distance (nautical miles)
    length: -(height / 2) + 20,  // length of radar arm
  };
  for (var i = 0; i < radar.blip.width; ++i) {
    for (var j = 0; j < radar.blip.height; ++j) {
      radar.blip.set(i, j, radar.color);
    }
  }
  radar.blip.updatePixels();

  background(0);
  noFill();
  stroke(radar.color);
  rectMode(RADIUS);
  textFont("Courier New");
}

function draw() {
  background(0, 40);

  // Outer radar "box"
  noFill();
  rect(width / 2, height / 2, (width / 2) - 10, (height / 2) - 10);
  
  // Outer radar circle
  fill(81, 255, 13, 4);
  ellipse(width / 2, height / 2, width - 40, height - 40);

  // Airport information box
  fill(airport.valid ? radar.color : radar.colorInvalid);
  noStroke();
  textSize(50);
  text(airport.icao, 25, 60);
  textSize(20);
  text(radar.distance + "nm", 25, 90);
  if (airport.valid) {
    text(airport.wind.padStart(12), width - 170, 40);
    text(airport.temperature.padStart(8), width - 120, 70);
  }

  // Show aircraft
  var blips = [];
  for (var a of aircraft.current) {
    if (a.angle <= radar.angle) {
      drawBlip(a.angle, a.distance);
      blips.push(a.callsign + " " + a.angle + " " + a.distance);
    }
  }
  for (var a of aircraft.last) {
    if (a.angle >= radar.angle) {
      drawBlip(a.angle, a.distance);
      blips.push(a.callsign + " " + a.angle + " " + a.distance);
    }
  }
  if (blips.toString() !== radar._blips.toString()) {
    print(blips);
    radar._blips = blips;
  }

  // Show rotating radar line
  stroke(radar.color);
  push();
  translate(width / 2, height / 2);
  rotate(radians(radar.angle));
  line(0, 0, 0, radar.length);
  pop();

  // Radar arm
  radar.angle = (radar.angle + 1) % 360;

  // Get updated aircraft positions
  if (radar.angle === 0) {
    aircraft.last = aircraft.current;
    aircraft.current = aircraft.next;
    aircraft.next = [];
    loadAircraft();
  }
}

function keyTyped() {
  if (keyCode === ENTER) {
    loadAirport(airport._nextIcao.toUpperCase());
    airport._nextIcao = "";
  } else {
    airport._nextIcao += key;
  }
}

function mouseWheel(event) {
  var delta = event.delta;

  if (delta > 0) {
    radar.distance += 5;
  }
  if (delta < 0) {
    radar.distance = Math.max(5, radar.distance - 5);
  }
}

function loadAirport(icao) {
  fetch("/airport/" + icao)
  .then((response) => response.json())
  .then(function (json) {
    airport.icao = icao;
    if (json.status === "Success") {
      airport.latitude = json.coordinates.latitude;
      airport.longitude = json.coordinates.longitude;
      airport.temperature = json.weather.temperature;
      airport.wind = json.weather.wind;
      airport.valid = true;
    } else {
      airport.valid = false;
    }
  });
}

function loadAircraft() {
  if (!airport.valid) {
    return;
  }

  fetch("/aircraft/" + airport.latitude + "/" + airport.longitude + "/" + radar.distance)
  .then((response) => response.json())
  .then(function (json) {
    aircraft.next = json.aircraft;
  });
}

function drawBlip(angle, distance) {
  angle = radians(angle + 180);
  distance = map(distance, 0, radar.distance, 0, -radar.length - radar.blip.height);

  push();
  translate(width / 2, height / 2);
  rotate(angle);
  image(radar.blip, 0, distance);
  pop();
}
