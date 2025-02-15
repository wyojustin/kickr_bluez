"use strict";

/***********************
 * Global Ride Data Collection
 ***********************/
var rideData = [];
setInterval(function() {
  var now = new Date();
  var dataPoint = {
    time: now.toISOString(),
    power: Dashboard ? Dashboard.currentPower : 100,
    cadence: Dashboard ? Dashboard.currentCadence : 90
  };
  rideData.push(dataPoint);
}, 1000);

/***********************
 * GPX Generation and Download
 ***********************/
function generateGPX() {
  var gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="RiderDashboard" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Trainer Ride</name>
    <type>Virtual Ride</type>
    <trkseg>`;
  rideData.forEach(function(point) {
    gpx += `
      <trkpt lat="0.0" lon="0.0">
        <time>${point.time}</time>
        <extensions>
          <power>${point.power}</power>
          <cadence>${point.cadence}</cadence>
        </extensions>
      </trkpt>`;
  });
  gpx += `
    </trkseg>
  </trk>
</gpx>`;
  return gpx;
}

document.getElementById("downloadRideButton").addEventListener("click", function() {
  var gpxContent = generateGPX();
  var blob = new Blob([gpxContent], { type: "application/gpx+xml" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = "ride.gpx";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

/***********************
 * Rider Dashboard Code
 ***********************/
const Dashboard = {
  canvas: document.getElementById("dashboard"),
  ctx: document.getElementById("dashboard").getContext("2d"),
  currentPower: 120,
  targetPower: 150,
  maxPower: 200,
  currentCadence: 90,
  targetCadence: 100,
  maxCadence: 160,
  trainerFtp: 100,
  resize: function() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  },
  percentToAngle: function(percent, maxPercent) {
    const angleDegrees = -240 + percent * 1.5;
    return angleDegrees * Math.PI / 180;
  },
  valueToAngle: function(value, maxValue) {
    const angleDegrees = 240 - (value / maxValue) * 300;
    return angleDegrees * Math.PI / 180;
  },
  getZoneColor: function(percent) {
    if (percent < 60) return "grey";
    else if (percent <= 75) return "blue";
    else if (percent <= 89) return "green";
    else if (percent <= 104) return "yellow";
    else if (percent <= 118) return "orange";
    else return "red";
  },
  getMutedColor: function(color) {
    const muted = {
      "grey": "rgba(128,128,128,0.3)",
      "blue": "rgba(0,0,255,0.3)",
      "green": "rgba(0,128,0,0.3)",
      "yellow": "rgba(255,255,0,0.3)",
      "orange": "rgba(255,165,0,0.3)",
      "red": "rgba(255,0,0,0.3)"
    };
    return muted[color] || color;
  },
  getCadenceZoneColor: function(cadence) {
    if (cadence < 60) return "grey";
    else if (cadence < 70) return "blue";
    else if (cadence < 80) return "green";
    else if (cadence < 90) return "yellow";
    else if (cadence < 110) return "orange";
    else return "red";
  },
  drawDial: function(ctx, center, value, target, label, maxValue, radius, extraLabel, zoneColor, useWedges, dialType) {
    if (useWedges) {
      const maxPercent = 150;
      const zones = [
        { from: 0, to: 60, color: this.getMutedColor("grey") },
        { from: 60, to: 75, color: this.getMutedColor("blue") },
        { from: 75, to: 89, color: this.getMutedColor("green") },
        { from: 89, to: 104, color: this.getMutedColor("yellow") },
        { from: 104, to: 118, color: this.getMutedColor("orange") },
        { from: 118, to: maxPercent, color: this.getMutedColor("red") }
      ];
      zones.forEach(zone => {
        let startAngle = this.percentToAngle(zone.from, maxPercent);
        let endAngle = this.percentToAngle(zone.to, maxPercent);
        if (startAngle > endAngle) { startAngle -= 2 * Math.PI; }
        ctx.beginPath();
        ctx.moveTo(center.x, center.y);
        ctx.arc(center.x, center.y, radius, startAngle, endAngle, false);
        ctx.closePath();
        ctx.fillStyle = zone.color;
        ctx.fill();
      });
    } else {
      ctx.beginPath();
      ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = "rgb(0,0,150)";
      ctx.fill();
    }
  
    // Draw chrome rim.
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
    let rimGradient = ctx.createRadialGradient(center.x, center.y, radius * 0.9, center.x, center.y, radius);
    rimGradient.addColorStop(0, "#ccc");
    rimGradient.addColorStop(0.5, "#fff");
    rimGradient.addColorStop(1, "#aaa");
    ctx.lineWidth = 8;
    ctx.strokeStyle = rimGradient;
    ctx.stroke();
  
    // Draw tick marks only on the cadence dial.
    if (!useWedges) {
      const tickStep = maxValue / 10;
      for (let tickVal = 0; tickVal <= maxValue; tickVal += tickStep) {
        const angle = this.valueToAngle(tickVal, maxValue);
        const tickX = center.x + radius * 0.9 * Math.cos(angle);
        const tickY = center.y - radius * 0.9 * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(tickX, tickY, 2, 0, 2 * Math.PI);
        ctx.fillStyle = "rgb(255,255,255)";
        ctx.fill();
      }
    }
  
    // Compute needle angles.
    let currentAngle, targetAngle;
    if (useWedges) {
      let measuredPercent = (value / this.trainerFtp) * 100;
      let tPercent = target;
      currentAngle = this.valueToAngle(measuredPercent, 200);
      targetAngle = this.valueToAngle(tPercent, 200);
    } else {
      currentAngle = this.valueToAngle(value, maxValue);
      targetAngle = this.valueToAngle(target, maxValue);
    }
  
    // Draw measured needle.
    if (zoneColor) {
      const tipX = center.x + 0.95 * radius * Math.cos(currentAngle);
      const tipY = center.y - 0.95 * radius * Math.sin(currentAngle);
      const baseCenterX = center.x - 0.25 * radius * Math.cos(currentAngle);
      const baseCenterY = center.y + 0.25 * radius * Math.sin(currentAngle);
      const halfWidth = 0.05 * radius;
      const baseLeftX = baseCenterX + halfWidth * Math.cos(currentAngle + Math.PI/2);
      const baseLeftY = baseCenterY - halfWidth * Math.sin(currentAngle + Math.PI/2);
      const baseRightX = baseCenterX + halfWidth * Math.cos(currentAngle - Math.PI/2);
      const baseRightY = baseCenterY - halfWidth * Math.sin(currentAngle - Math.PI/2);
      ctx.beginPath();
      ctx.moveTo(baseLeftX, baseLeftY);
      ctx.lineTo(tipX, tipY);
      ctx.lineTo(baseRightX, baseRightY);
      ctx.closePath();
      ctx.fillStyle = zoneColor;
      ctx.fill();
    } else {
      const currentX = center.x + 0.8 * radius * Math.cos(currentAngle);
      const currentY = center.y - 0.8 * radius * Math.sin(currentAngle);
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(currentX, currentY);
      ctx.strokeStyle = "rgb(0,255,0)";
      ctx.lineWidth = 4;
      ctx.stroke();
    }
  
    // Determine target needle color.
    let targetNeedleColor = "rgb(255,255,255)";
    if (dialType === "watts") {
      const computedTargetWatts = Math.round(this.trainerFtp * target / 100);
      if (target !== 0 && Math.abs(value - computedTargetWatts) / computedTargetWatts <= 0.05) {
        targetNeedleColor = "rgb(0,255,0)";
      }
    } else if (dialType === "cadence") {
      if (target !== 0 && Math.abs(value - target) / target <= 0.05) {
        targetNeedleColor = "rgb(0,255,0)";
      }
    }
    // Draw target needle.
    const targetX = center.x + 0.8 * radius * Math.cos(targetAngle);
    const targetY = center.y - 0.8 * radius * Math.sin(targetAngle);
    ctx.beginPath();
    ctx.moveTo(center.x, center.y);
    ctx.lineTo(targetX, targetY);
    ctx.strokeStyle = targetNeedleColor;
    ctx.lineWidth = 2;
    ctx.stroke();
  
    // Draw dial labels.
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const fontSize = Math.floor(radius * 0.15);
    ctx.font = `${fontSize}px Arial`;
    if (dialType === "watts") {
      const measuredPercent = Math.round((value / this.trainerFtp) * 100);
      const measuredText = value.toString() + " W (" + measuredPercent.toString() + "%)";
      const computedTargetWatts = Math.round(this.trainerFtp * target / 100);
      const targetText = computedTargetWatts.toString() + " W (" + target.toString() + "%)";
      const measuredColor = this.getZoneColor(measuredPercent);
      const targetColor = this.getZoneColor(target);
      ctx.fillStyle = measuredColor;
      ctx.fillText(measuredText, center.x, center.y + radius * 0.45);
      ctx.fillStyle = targetColor;
      ctx.fillText(targetText, center.x, center.y + radius * 0.65);
    } else if (dialType === "cadence") {
      ctx.fillStyle = "rgb(255,255,255)";
      ctx.fillText(value.toString() + "/" + target.toString(), center.x, center.y + radius * 0.45);
      ctx.fillText("RPM", center.x, center.y + radius * 0.65);
    }
  
    // Draw a shiny 3D hubcap in the center.
    const hubcapRadius = 0.1 * radius;
    const hubcapGradient = ctx.createRadialGradient(center.x, center.y, hubcapRadius * 0.1, center.x, center.y, hubcapRadius);
    hubcapGradient.addColorStop(0, "#fff");
    hubcapGradient.addColorStop(0.5, "#ddd");
    hubcapGradient.addColorStop(0.8, "#888");
    hubcapGradient.addColorStop(1, "#444");
    ctx.beginPath();
    ctx.arc(center.x, center.y, hubcapRadius, 0, 2 * Math.PI);
    ctx.fillStyle = hubcapGradient;
    ctx.fill();
  
    // Draw a green LED over the hubcap if the target needle is bright green.
    if (targetNeedleColor === "rgb(0,255,0)") {
      const ledRadius = hubcapRadius * 0.5;
      const ledGradient = ctx.createRadialGradient(center.x, center.y, ledRadius * 0.1, center.x, center.y, ledRadius);
      ledGradient.addColorStop(0, "#0f0");
      ledGradient.addColorStop(1, "rgba(0,255,0,0)");
      ctx.beginPath();
      ctx.arc(center.x, center.y, ledRadius, 0, 2 * Math.PI);
      ctx.fillStyle = ledGradient;
      ctx.fill();
    }
  },
  
  animate: function() {
    const width = this.canvas.width;
    const height = this.canvas.height;
    this.ctx.clearRect(0, 0, width, height);
  
    const dialRadius = Math.min(width, height / 2) * 0.4;
    const topDialCenter = { x: width / 2, y: height / 4 };
    const bottomDialCenter = { x: width / 2, y: (height * 3) / 4 };
  
    const measuredPercent = Math.round((this.currentPower / this.trainerFtp) * 100);
    const targetPercent = Math.round((this.targetPower / this.trainerFtp) * 100);
    const powerLabel = measuredPercent + "%/" + targetPercent + "%";
    const extraLabel = this.trainerFtp + "W";
    const wattZoneColor = this.getZoneColor(measuredPercent);
  
    const cadenceZoneColor = this.getCadenceZoneColor(this.currentCadence);
  
    // Draw watts dial.
    this.drawDial(this.ctx, topDialCenter, this.currentPower, this.targetPower, powerLabel, this.maxPower, dialRadius, extraLabel, wattZoneColor, true, "watts");
    // Draw cadence dial.
    this.drawDial(this.ctx, bottomDialCenter, this.currentCadence, this.targetCadence, "RPM", this.maxCadence, dialRadius, null, cadenceZoneColor, false, "cadence");
  
    requestAnimationFrame(() => { this.animate(); });
  }
};
  
// Initialize Dashboard.
Dashboard.resize();
Dashboard.animate();
  
/***********************
 * MQTT Integration for Rider Dashboard
 ***********************/
const clientId = "web_client_" + Math.floor(Math.random() * 100);
let pairedTrainerId = null;
// Create MQTT client using values from Config.
const mqttClient = new Paho.MQTT.Client(Config.mqtt_hostname, Number(Config.mqtt_port), "/mqtt", clientId);
  
mqttClient.onConnectionLost = function(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.error("Connection lost: " + responseObject.errorMessage);
  } else {
    console.log("Connection lost.");
  }
};
  
mqttClient.onMessageArrived = function(message) {
  if (!message.payloadString || message.payloadString.trim() === "") {
    console.log("Empty MQTT payload, skipping parsing.");
    return;
  }
  console.log("MQTT message arrived on topic " + message.destinationName + ": " + message.payloadString);
  try {
    const data = JSON.parse(message.payloadString);
    const topic = message.destinationName;
    if (topic.endsWith("device_list")) {
      if (data.device_list && Array.isArray(data.device_list)) {
        const selectElem = document.getElementById("trainerSelect");
        // Rebuild dropdown with default option and devices.
        selectElem.innerHTML = '<option value="">Select Trainer</option>';
        data.device_list.forEach(device => {
          const option = document.createElement("option");
          option.value = device;
          option.textContent = device;
          selectElem.appendChild(option);
        });
        // If a saved trainer exists, ensure it appears in the dropdown.
        var savedTrainer = getCookie("pairedTrainer");
        if (savedTrainer) {
          let exists = false;
          for (let i = 0; i < selectElem.options.length; i++) {
            if (selectElem.options[i].value === savedTrainer) {
              exists = true;
              break;
            }
          }
          if (!exists) {
            let newOption = document.createElement("option");
            newOption.value = savedTrainer;
            newOption.textContent = savedTrainer;
            selectElem.appendChild(newOption);
          }
          selectElem.value = savedTrainer;
        }
      }
    } else if (topic.endsWith("set_target_power")) {
      if (data.target_power !== undefined) {
        if (!data.uuid_trainer || data.uuid_trainer === pairedTrainerId) {
          Dashboard.targetPower = data.target_power;
        }
      }
    } else if (topic.endsWith("set_measured_power")) {
      if (data.measured_power !== undefined) {
        if (data.uuid_trainer) {
          var selectElem = document.getElementById("trainerSelect");
          var exists = false;
          for (var i = 0; i < selectElem.options.length; i++) {
            if (selectElem.options[i].value === data.uuid_trainer) {
              exists = true;
              break;
            }
          }
          if (!exists) {
            var option = document.createElement("option");
            option.value = data.uuid_trainer;
            option.textContent = data.uuid_trainer;
            selectElem.appendChild(option);
          }
        }
        if (!data.uuid_trainer || data.uuid_trainer === pairedTrainerId) {
          Dashboard.currentPower = data.measured_power;
        }
      }
    } else if (topic.endsWith("set_ftp")) {
      if (data.ftp !== undefined) {
        if (!data.uuid_trainer || data.uuid_trainer === pairedTrainerId) {
          Dashboard.trainerFtp = data.ftp;
          document.getElementById("ftpSlider").value = data.ftp;
          document.getElementById("ftpText").value = data.ftp;
        }
      }
    } else if (topic.endsWith("set_target_cadence")) {
      if (data.target_cadence !== undefined) {
        if (!data.uuid_trainer || data.uuid_trainer === pairedTrainerId) {
          Dashboard.targetCadence = data.target_cadence;
        }
      }
    } else if (topic.endsWith("set_measured_cadence")) {
      if (data.measured_cadence !== undefined) {
        if (!data.uuid_trainer || data.uuid_trainer === pairedTrainerId) {
          Dashboard.currentCadence = data.measured_cadence;
        }
      }
    }
  } catch (err) {
    console.error("Error parsing MQTT JSON:", err);
  }
};
  
// Connect to the MQTT broker.
mqttClient.connect({
  onSuccess: function() {
    console.log("Connected to MQTT broker at " + Config.mqtt_hostname + ":" + Config.mqtt_port);
    mqttClient.subscribe(Config.APP_ID + "/#");
    const listDevicesMsg = new Paho.MQTT.Message("");
    listDevicesMsg.destinationName = Config.APP_ID + "/list_devices";
    mqttClient.send(listDevicesMsg);
    
    // AUTOMATIC PAIRING: Now that we're connected, check for a saved trainer and FTP.
    var savedTrainer = getCookie("pairedTrainer");
    var savedFtp = getCookie("trainerFtp");
    if (savedTrainer) {
      pairedTrainerId = savedTrainer;
      // Ensure the trainer appears in the dropdown.
      const trainerSelect = document.getElementById("trainerSelect");
      let exists = false;
      for (let i = 0; i < trainerSelect.options.length; i++) {
        if (trainerSelect.options[i].value === savedTrainer) {
          exists = true;
          break;
        }
      }
      if (!exists) {
        let newOption = document.createElement("option");
        newOption.value = savedTrainer;
        newOption.textContent = savedTrainer;
        trainerSelect.appendChild(newOption);
      }
      trainerSelect.value = savedTrainer;
      
      // If a saved FTP value exists, update the slider and text.
      if (savedFtp) {
        document.getElementById("ftpSlider").value = savedFtp;
        document.getElementById("ftpText").value = savedFtp;
        Dashboard.trainerFtp = parseInt(savedFtp, 10);
      }
      
      const pairPayload = {
        uuid_trainer: savedTrainer,
        uuid_rider: clientId
      };
      const pairMessage = new Paho.MQTT.Message(JSON.stringify(pairPayload));
      pairMessage.destinationName = Config.APP_ID + "/pair_trainer_rider";
      mqttClient.send(pairMessage);
      console.log("Automatically paired with trainer from cookie:", savedTrainer);
      document.getElementById("ftpSlider").disabled = false;
      document.getElementById("ftpText").disabled = false;
    }
  },
  onFailure: function(message) {
    console.error("MQTT Connection failed: " + message.errorMessage);
  }
});
  
/***********************
 * FTP Slider and Text Handling
 ***********************/
const ftpSlider = document.getElementById("ftpSlider");
const ftpText = document.getElementById("ftpText");
  
function sendFTPUpdate(ftpVal) {
  const msgPayload = {
    uuid_trainer: pairedTrainerId,
    ftp: ftpVal,
    time: new Date().toISOString()
  };
  const msg = new Paho.MQTT.Message(JSON.stringify(msgPayload));
  msg.destinationName = Config.APP_ID + "/set_ftp";
  mqttClient.send(msg);
}
  
ftpSlider.addEventListener("input", function() {
  const ftpVal = parseInt(this.value, 10);
  ftpText.value = ftpVal;
  sendFTPUpdate(ftpVal);
  if (pairedTrainerId) {
    setCookie("trainerFtp", ftpVal, 30);
  }
});
  
ftpText.addEventListener("change", function() {
  let ftpVal = parseInt(this.value, 10);
  if (isNaN(ftpVal)) { ftpVal = 100; }
  ftpVal = Math.max(50, Math.min(ftpVal, 400));
  this.value = ftpVal;
  ftpSlider.value = ftpVal;
  sendFTPUpdate(ftpVal);
  if (pairedTrainerId) {
    setCookie("trainerFtp", ftpVal, 30);
  }
});
  
/***********************
 * Pairing Handling with Cookie Support (Manual)
 ***********************/
const trainerSelect = document.getElementById("trainerSelect");
trainerSelect.addEventListener("change", function() {
  const selectedTrainer = trainerSelect.value;
  if (selectedTrainer) {
    pairedTrainerId = selectedTrainer;
    // Store both the selected trainer and current FTP value in cookies.
    setCookie("pairedTrainer", selectedTrainer, 30);
    setCookie("trainerFtp", ftpSlider.value, 30);
    const pairPayload = {
      uuid_trainer: selectedTrainer,
      uuid_rider: clientId
    };
    const pairMessage = new Paho.MQTT.Message(JSON.stringify(pairPayload));
    pairMessage.destinationName = Config.APP_ID + "/pair_trainer_rider";
    if (mqttClient.isConnected()) {
      mqttClient.send(pairMessage);
      console.log("Pairing with trainer:", selectedTrainer);
    } else {
      console.warn("MQTT client not connected; pairing message not sent.");
    }
    ftpSlider.disabled = false;
    ftpText.disabled = false;
  } else {
    pairedTrainerId = null;
    setCookie("pairedTrainer", "", -1);
    setCookie("trainerFtp", "", -1);
    ftpSlider.disabled = true;
    ftpText.disabled = true;
  }
});
  
/***********************
 * UI Handling: Side Panel Toggle
 ***********************/
document.getElementById("togglePanelButton").addEventListener("click", function(e) {
  e.stopPropagation();
  document.getElementById("sidePanel").classList.toggle("open");
});
  
document.getElementById("dashboard").addEventListener("click", function() {
  document.getElementById("sidePanel").classList.remove("open");
});
  
window.addEventListener("resize", () => { Dashboard.resize(); });
