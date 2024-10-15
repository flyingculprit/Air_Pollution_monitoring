import os
import smtplib
from flask import Flask, render_template, request, jsonify
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


# Add the path to your service account key file
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

# Authorize and open the spreadsheet
client = gspread.authorize(creds)

spreadsheet = client.open("Air-Quality")
sheet = spreadsheet.sheet1


app = Flask(__name__)

# API Key and URLs
API_KEY = 'API key'
GEO_URL = 'https://api.openweathermap.org/geo/1.0/direct'
AIR_QUALITY_URL = 'http://api.openweathermap.org/data/2.5/air_pollution'

def data_store(data,city_name,air_quality_index):




    # Remove the keys 'no' and 'pm10'
    data.pop('no', None)  # Removes 'no' key
    data.pop('pm10', None)  # Removes 'pm10' key

    # Extract the remaining values as a list
    values_list = []
    print(city_name)
    values_list = list(data.values())
    values_list.append(air_quality_index)
    values_list.append(city_name)


    print(values_list)

    sheet.append_row(values_list)

    # Retrieve all data from the sheet
    all_data = sheet.get_all_records()
    print(all_data)

    # # Retrieve specific row/column
    # row_data = sheet.row_values(2)
    # print(f"Row 2 data: {row_data}")
    #
    # col_data = sheet.col_values(2)
    # print(f"Column 2 data: {col_data}")



# Function to send email alerts
def send_email_alert(city_name, aqi_level, recipient_email):
    sender_email = "gmail"  # Your email
    sender_password = "mail pass" # Your email password

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = f"Air Quality Alert for {city_name}"

    # Create the email content
    email_content = f"""
    <h2>Air Quality Alert!</h2>
    <p>The air quality in <strong>{city_name}</strong> has reached an unhealthy level.</p>
    <p><strong>AQI: {aqi_level} (Poor/Very Poor)</strong></p>
    <p>Please take necessary precautions.</p>
    """

    message.attach(MIMEText(email_content, 'html'))

    # Setup the SMTP server
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # For Gmail
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
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
def get_air_quality(lat, lon,city_name):
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY}
    response = requests.get(AIR_QUALITY_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        aqi = data['list'][0]['main']['aqi']
        components = data['list'][0]['components']
        data_store(components,city_name,aqi)
        # Check AQI level and trigger email if needed
        if aqi in [4, 5]:
            recipient_email="thamizh5253@gmail.com"
            send_email_alert(city_name, aqi, recipient_email)

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
            "components": components
        }
    else:
        return None


# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        city_name = request.form['city']
        # recipient_email = request.form['email']  # Email field for receiving alerts
        lat, lon = get_lat_lon(city_name)

        if lat and lon:
            air_quality = get_air_quality(lat, lon,city_name)
            if air_quality:
                return render_template('index.html',
                                       air_quality_info=f"AQI: {air_quality['aqi']} ({air_quality['description']})",
                                       components=air_quality['components'] ,city=city_name)
            else:
                return render_template('index.html', air_quality_info="Failed to retrieve air quality data.")
        else:
            return render_template('index.html', air_quality_info="City not found.")
    return render_template('index.html')


@app.route('/history')
def get_history():

    # Fetch all rows from the spreadsheet
    data = sheet.get_all_records()
    # Render the history page and pass the spreadsheet data to it
    return render_template('history.html', data=data)


if __name__ == "__main__":
    app.run(debug=True)
