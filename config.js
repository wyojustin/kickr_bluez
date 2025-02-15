// config.js
// Immediately invoked function expression (IIFE) to encapsulate the config values
var Config = (function() {
  return {
    mqtt_hostname: localStorage.getItem('mqtt_hostname') || 'mqtt.eclipseprojects.io',
    mqtt_port: Number(localStorage.getItem('mqtt_port')) || 80,
    APP_ID: localStorage.getItem('APP_ID') || 'UniqueAppID_for_training_sessions'
  };
})();
