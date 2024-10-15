from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Your API key (Replace with your actual key)
API_KEY = 'e7ab12968358ecf387dc7f0c96c98660'


# Function to get latitude and longitude for a city
def get_city_coordinates(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
    try:
        response = requests.get(geo_url)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return lat, lon
            else:
                return None, None
        else:
            return None, None
    except Exception as e:
        return None, None


# Function to get air quality data for specific latitude and longitude
def get_air_quality(lat, lon):
    try:
        air_quality_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY
        }
        response = requests.get(air_quality_url, params=params)
        if response.status_code == 200:
            data = response.json()

            # Extracting the air quality index (AQI)
            aqi = data['list'][0]['main']['aqi']
            aqi_description = {
                1: 'Good',
                2: 'Fair',
                3: 'Moderate',
                4: 'Poor',
                5: 'Very Poor'
            }

            # Extracting air quality components
            components = data['list'][0]['components']
            return {
                "aqi": f"Air Quality Index (AQI): {aqi} ({aqi_description.get(aqi, 'Unknown')})",
                "components": components
            }
        else:
            return None
    except Exception as e:
        return None


# Main route
@app.route("/", methods=["GET", "POST"])
def index():
    air_quality_info = None
    components = None
    city =None
    if request.method == "POST":
        city = request.form.get("city")
        lat, lon = get_city_coordinates(city)
        if lat and lon:
            air_quality_data = get_air_quality(lat, lon)
            if air_quality_data:
                air_quality_info = air_quality_data["aqi"]
                components = air_quality_data["components"]
            else:
                air_quality_info = "Failed to retrieve air quality data."
        else:
            air_quality_info = f"Could not find coordinates for {city}. Please check the city name."

    return render_template("index.html", air_quality_info=air_quality_info, components=components,city=city)


if __name__ == "__main__":
    app.run(debug=True)
