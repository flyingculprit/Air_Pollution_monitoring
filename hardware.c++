#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// Replace these with your Wi-Fi credentials
const char* ssid = "CYRUSBYTE";
const char* password = "12344321";

ESP8266WebServer server(80); // Create a web server on port 80

const int analogPin = A0; // Analog pin connected to MQ135
float sensorValue = 0;    // Variable to store sensor value
float voltage = 0;        // Variable to store voltage
unsigned long lastPrintTime = 0; // Variable to track time

void setup() {
  Serial.begin(115200); // Start serial communication
  WiFi.begin(ssid, password); // Connect to Wi-Fi

  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("Connected to Wi-Fi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP()); // Print the device's IP address

  // Define the route for the root URL
  server.on("/", []() {
    // Create an HTML response
    String html = "<html><body>";
    html += "<h1>MQ135 Sensor Data</h1>";
    html += "<p>Sensor Value: " + String(sensorValue) + "</p>";
    html += "<p>Voltage: " + String(voltage, 2) + "V</p>";
    html += "</body></html>";

    // Send the response
    server.send(200, "text/html", html);
  });

  server.begin(); // Start the server
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient(); // Handle incoming client requests

  // Print data to Serial Monitor every 3 seconds
  if (millis() - lastPrintTime >= 3000) { // Check if 3 seconds have passed
    lastPrintTime = millis();

    // Read sensor value and calculate voltage
    sensorValue = analogRead(analogPin);
    voltage = (sensorValue / 1023.0) * 3.3;

    // Print data to Serial Monitor
    Serial.println("=== MQ135 Sensor Data ===");
    Serial.print("Sensor Value: ");
    Serial.println(sensorValue);
    Serial.print("Voltage: ");
    Serial.print(voltage, 2); // Print voltage with 2 decimal places
    Serial.println(" V");
    Serial.println("=========================");
  }
}