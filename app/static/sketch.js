let airport;
let aircraft;
let radar;

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
    length: -(height / 2) + 40,  // length of radar arm
  };
  for (let i = 0; i < radar.blip.width; ++i) {
    for (let j = 0; j < radar.blip.height; ++j) {
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
  ellipse(width / 2, height / 2, width - 80, height - 80);

  // Airport information box
  fill(airport.valid ? radar.color : radar.colorInvalid);
  noStroke();
  textSize(50);
  text(airport.icao, 25, 80);
  textSize(20);
  text(radar.distance + "NM", 25, 110);
  if (airport.valid) {
    text(airport.wind.padStart(12), width - 170, 40);
    text(airport.temperature.padStart(8), width - 120, 70);
    textSize(20);
    text(airport.name, 25, 30);
  }
  textSize(20);
  fill("yellow");
  text(airport._nextIcao, 25, height - 25);

  // Show aircraft
  const blips = [];
  for (const a of aircraft.current) {
    if (a.angle <= radar.angle && a.distance <= radar.distance) {
      drawBlip(a.angle, a.distance);
      blips.push(a.callsign + " " + a.angle + " " + a.distance);
    }
  }
  for (const a of aircraft.last) {
    if (a.angle >= radar.angle && a.distance <= radar.distance) {
      drawBlip(a.angle, a.distance);
      blips.push(a.callsign + " " + a.angle + " " + a.distance);
    }
  }
  if (blips.toString() !== radar._blips.toString()) {
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

function keyPressed() {
  if (keyCode === ENTER) {
    loadAirport(airport._nextIcao);
    airport._nextIcao = "";
  } else if (keyCode === BACKSPACE) {
    airport._nextIcao = airport._nextIcao.slice(0, -1);
  } else if (("A" <= key && key <= "Z") || ("0" <= key && "9" <= key)) {
    airport._nextIcao += key;
  }
}

function mouseWheel(event) {
  const zoomOut = event.delta > 0;
  const zoomDelta = (radar.distance >= 4500) ? 25
                  : (radar.distance >= 1500) ? 20
                  : (radar.distance >= 500) ? 10
                  : (radar.distance >= 10) ? 5
                  : 1;

  if (zoomOut) {
    // 11000NM is slightly more than half the circumference of earth.
    radar.distance = Math.min(11000, radar.distance + zoomDelta);
  } else {
    radar.distance = Math.max(2, radar.distance - zoomDelta);
  }
}

function loadAirport(icao) {
  fetch("/airport/" + icao)
  .then((response) => response.json())
  .then(function (json) {
    if (json.status === "Success") {
      airport.icao = json.icao;
      airport.name = json.name;
      airport.latitude = json.coordinates.latitude;
      airport.longitude = json.coordinates.longitude;
      airport.temperature = json.weather.temperature;
      airport.wind = json.weather.wind;
      airport.valid = true;
    } else {
      airport.icao = icao;
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
