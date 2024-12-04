import os
import smtplib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from flask_cors import CORS
import requests


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
from bs4 import BeautifulSoup




# Define the hardware IP as a variable
HARDWARE_IP = "http://ip of hardware"



# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Add the path to your service account key file
# creds = ServiceAccountCredentials.from_json_keyfile_name(r'E:/Air_Pollution_monitoring/model-marker-440716-t1-44c4e6dcf699.json', scope)
creds = ServiceAccountCredentials.from_json_keyfile_name('C:/credentials.json', scope)


# Authorize and open the spreadsheet
client = gspread.authorize(creds)
spreadsheet = client.open("air-pollution")
sheet = spreadsheet.sheet1


app = Flask(__name__)
CORS(app)


# Load the dataset
data = pd.read_csv('C:air_quality_dataset.csv')

# API Key and URLs
API_KEY = '4s5ofw7b2aarcnfi4ccada05da1d7cc4800e56103badas'
GEO_URL = 'https://api.openweathermap.org/geo/1.0/direct'
AIR_QUALITY_URL = 'http://api.openweathermap.org/data/2.5/air_pollution'

# List of cities for the dropdown
city_list = ['Ahmedabad', 'Aizawl', 'Amaravati', 'Amritsar', 'Bengaluru', 'Bhopal',
             'Brajrajnagar', 'Chandigarh', 'Chennai', 'Coimbatore', 'Delhi', 'Ernakulam',
             'Gurugram', 'Guwahati', 'Hyderabad', 'Jaipur', 'Jorapokhar', 'Kochi',
             'Kolkata', 'Lucknow', 'Mumbai', 'Patna', 'Shillong', 'Talcher',
             'Thiruvananthapuram', 'Visakhapatnam']

#hardware data aqi

def classify_aqi(sensor_value):
    """Classify AQI based on the sensor value."""
    aqi_description = {
        1: {"quality": "Good", "color": "#4CAF50"},
        2: {"quality": "Fair", "color": "#8BC34A"},
        3: {"quality": "Moderate", "color": "#FFEB3B"},
        4: {"quality": "Poor", "color": "#FF9800"},
        5: {"quality": "Very Poor", "color": "#F44336"},
    }

    if sensor_value < 100:
        return aqi_description[1]
    elif 100 <= sensor_value < 200:
        return aqi_description[2]
    elif 200 <= sensor_value < 300:
        return aqi_description[3]
    elif 300 <= sensor_value < 400:
        return aqi_description[4]
    else:
        return aqi_description[5]

# Machine learning model for prediction
def train_predict_model():
    # Load dataset (assuming you have stored it locally)
    data = pd.read_csv('air_quality_dataset.csv')

    # Features are gas values, and the target is AQI
    X = data[['co', 'no2', 'o3','so2', 'pm2_5', 'nh3']]
    y = data['aqi']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model (you can use more complex models based on your dataset)
    model = LinearRegression()
    model.fit(X_train, y_train)

    return model


# Train the model when the app starts
model = train_predict_model()


def data_store(data, city_name, air_quality_index):
    # Remove unnecessary keys
    data.pop('no', None)
    data.pop('pm10', None)

    # Prepare the values to store
    values_list = list(data.values())
    values_list.append(air_quality_index)
    values_list.append(city_name)

    # Append the data to Google Sheets
    sheet.append_row(values_list)

    # Retrieve all data from the sheet (optional)
    all_data = sheet.get_all_records()
    print(all_data)


# Function to send email alerts
def send_email_alert(city_name, aqi_level):
    sender_email = " "  # Your email
    sender_password = " "  # Your email password
    receiver_email = " "  # Receiver's email

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = f"Air Quality Alert for {city_name}"

    email_content = f"""
    <h2>Air Quality Alert!</h2>
    <p>The air quality in <strong>{city_name}</strong> has reached an unhealthy level.</p>
    <p><strong>AQI: {aqi_level} (Poor/Very Poor)</strong></p>
    <p>Please take necessary precautions.</p>
    """
    message.attach(MIMEText(email_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")


# Function to get latitude and longitude from city name
def get_lat_lon(city_name):
    params = {'q': city_name, 'limit': 1, 'appid': API_KEY}
    response = requests.get(GEO_URL, params=params)
    data = response.json()
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return lat, lon
    return None, None


# Function to get air quality data
def get_air_quality(lat, lon, city_name):
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY}
    response = requests.get(AIR_QUALITY_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        aqi = data['list'][0]['main']['aqi']
        components = data['list'][0]['components']
        data_store(components, city_name, aqi)

        # AI Prediction
        prediction_data = np.array([list(components.values())]).reshape(1, -1)
        predicted_aqi = model.predict(prediction_data)[0]

        # Convert predicted AQI to descriptive category
        predicted_aqi_category = get_aqi_description(predicted_aqi)

        # Check AQI level and trigger email if needed
        if aqi in [4, 5]:
            send_email_alert(city_name, aqi)

        aqi_description = {
            1: 'Good',
            2: 'Fair',
            3: 'Moderate',
            4: 'Poor',
            5: 'Very Poor'
        }

        return {
            "aqi": aqi,
            "description": aqi_description.get(aqi, 'Unknown'),
            "components": components,
            "predicted_aqi": predicted_aqi,
            "predicted_aqi_category": predicted_aqi_category
        }
    else:
        return None


# Function to convert AQI to descriptive category
def get_aqi_description(aqi_value):
    if aqi_value <= 50:
        return 'Good'
    elif aqi_value <= 100:
        return 'Fair'
    elif aqi_value <= 150:
        return 'Moderate'
    elif aqi_value <= 200:
        return 'Poor'
    else:
        return 'Very Poor'


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        city_name = request.form['city']
        action = request.form['action']  # Get which button was clicked

        lat, lon = get_lat_lon(city_name)

        if lat and lon:
            air_quality = get_air_quality(lat, lon, city_name)
            if air_quality:
                if action == 'current':
                    # Show current AQI
                    return render_template('index.html',
                                           air_quality_info=f"AQI: {air_quality['aqi']} ({air_quality['description']})",
                                           components=air_quality['components'],
                                           city=city_name)
                elif action == 'predict':
                    # Predict the next day's AQI
                    predicted_aqi = air_quality['predicted_aqi']
                    predicted_aqi_category = air_quality['predicted_aqi_category']
                    return render_template('index.html',
                                           air_quality_info=f"Predicted Next Day AQI: {predicted_aqi} ({predicted_aqi_category})",
                                           components=air_quality['components'],
                                           city=city_name)
            else:
                return render_template('index.html', air_quality_info="Failed to retrieve air quality data.")
        else:
            return render_template('index.html', air_quality_info="City not found.")
    return render_template('index.html')


@app.route('/hardware')
def get_hardware():
    try:
        # Fetch the data from the hardware API
        response = requests.get(HARDWARE_IP)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract values from the HTML
        sensor_value = float(soup.find('p', text=lambda t: t and "Sensor Value" in t).text.split(":")[1].strip())
        voltage = soup.find('p', text=lambda t: t and "Voltage" in t).text.split(":")[1].strip()

        # Classify AQI based on the sensor value
        aqi_info = classify_aqi(sensor_value)

        # Prepare data for rendering
        data = {
            "sensor_value": sensor_value,
            "voltage": voltage,
            "aqi_quality": aqi_info["quality"],
            "aqi_color": aqi_info["color"]
        }

    except requests.exceptions.RequestException as e:
        # Handle errors (e.g., connection issues or invalid responses)
        data = {"error": "Unable to fetch hardware data", "details": str(e)}
    except Exception as e:
        # Handle parsing or other errors
        data = {"error": "Error processing data", "details": str(e)}

    # Render the template and pass the data
    return render_template('hardware.html', data=data)

@app.route('/history')
def get_history():
    data = sheet.get_all_records()
    print(data)
    return render_template('history.html', data=data)



@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        city_name = request.form['city']
        lat, lon = get_lat_lon(city_name)

        if lat and lon:
            air_quality = get_air_quality(lat, lon, city_name)
            if air_quality:
                predicted_aqi = air_quality['predicted_aqi']
                predicted_aqi_category = air_quality['predicted_aqi_category']
                return render_template('prediction.html',
                                       air_quality_info=f"Predicted Next Day AQI: {predicted_aqi} ({predicted_aqi_category})",
                                       components=air_quality['components'],
                                       city=city_name)
            else:
                return render_template('prediction.html', air_quality_info="Failed to retrieve air quality data.")
        else:
            return render_template('prediction.html', air_quality_info="City not found.")
    return render_template('prediction.html')

if __name__ == "__main__":
    app.run(debug=True)



