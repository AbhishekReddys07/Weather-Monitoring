import requests
import time
import sqlite3
from datetime import datetime
from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64
from threading import Thread, Event, Lock

app = Flask(__name__)

# Configurable parameters
API_KEY = '9a9dc888ba8d74cb6a0b1aae52077caa'  # Replace with your actual API key
CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
INTERVAL = 300  # 5 minutes (configurable)
TEMP_UNIT = "metric"  # Can be changed to "imperial" for Fahrenheit
ALERT_THRESHOLD = 28  # Alert temperature threshold

# Global list to store alerts and an Event to stop the thread gracefully
alerts = []
alerts_lock = Lock()  # Lock for alerts access
stop_event = Event()

# SQLite database setup for daily summaries and alerts
def init_db():
    with sqlite3.connect('weather_data.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS weather_data (
                        city TEXT,
                        date TEXT,
                        temp REAL,
                        humidity REAL,
                        wind_speed REAL,
                        dominant_condition TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS daily_weather_summary (
                        city TEXT,
                        date TEXT,
                        avg_temp REAL,
                        max_temp REAL,
                        min_temp REAL,
                        dominant_condition TEXT,
                        humidity REAL,
                        wind_speed REAL
                    )''')
        conn.commit()

# Alert function to add alert messages to the global list
def send_alert(city, temp):
    alert_message = f"ALERT: Temperature in {city} has exceeded {ALERT_THRESHOLD}°C! Current temperature: {temp}°C"
    print(alert_message)  # Log the alert to the console
    with alerts_lock:  # Ensure thread-safe access to alerts
        alerts.append(alert_message)  # Add alert to the global alerts list

# Fetch weather data from the OpenWeatherMap API and send alert if temp exceeds threshold
def fetch_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units={TEMP_UNIT}"
    response = requests.get(url)
    data = response.json()

    if data.get("cod") == 200:
        main_condition = data["weather"][0]["main"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        update_time = datetime.utcfromtimestamp(data["dt"]).strftime('%Y-%m-%d %H:%M:%S')

        # Trigger alert if temperature exceeds the threshold
        if temp >= ALERT_THRESHOLD:
            send_alert(city, temp)

        return {
            "city": city,
            "main_condition": main_condition,
            "temp": temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "update_time": update_time
        }
    else:
        print(f"Error retrieving weather data for {city}: {data.get('message')}")
        return None

# Calculate daily rollups and aggregates
def calculate_daily_summary(city):
    today = datetime.utcnow().date()
    with sqlite3.connect('weather_data.db', check_same_thread=False) as conn:
        c = conn.cursor()
        summary_query = f"SELECT avg(temp), max(temp), min(temp), dominant_condition, avg(humidity), avg(wind_speed) FROM weather_data WHERE city=? AND date=?"
        c.execute(summary_query, (city, str(today)))
        result = c.fetchone()

        if result:
            avg_temp, max_temp, min_temp, dominant_condition, avg_humidity, avg_wind_speed = result
            # Store summary in daily_weather_summary table
            c.execute('''INSERT INTO daily_weather_summary (city, date, avg_temp, max_temp, min_temp, dominant_condition, humidity, wind_speed)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (city, str(today), avg_temp, max_temp, min_temp, dominant_condition, avg_humidity, avg_wind_speed))
            conn.commit()

# Generate visualizations for daily summaries
def generate_visualization(city):
    with sqlite3.connect('weather_data.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(f"SELECT date, avg_temp, max_temp, min_temp FROM daily_weather_summary WHERE city=? ORDER BY date", (city,))
        rows = c.fetchall()

    dates = [row[0] for row in rows]
    avg_temps = [row[1] for row in rows]
    max_temps = [row[2] for row in rows]
    min_temps = [row[3] for row in rows]  # Fixed this line

    plt.figure(figsize=(10, 6))
    plt.plot(dates, avg_temps, label="Average Temp")
    plt.plot(dates, max_temps, label="Max Temp", linestyle='--')
    plt.plot(dates, min_temps, label="Min Temp", linestyle='--')
    plt.title(f"Daily Temperature Summary for {city}")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.legend()

    # Save plot as an image and return base64 string for web rendering
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url

# Save current weather data to database
def save_weather_data(data):
    with sqlite3.connect('weather_data.db', check_same_thread=False) as conn:
        c = conn.cursor()
        date_today = datetime.utcnow().date()
        c.execute('''INSERT INTO weather_data (city, date, temp, humidity, wind_speed, dominant_condition)
                     VALUES (?, ?, ?, ?, ?, ?)''', (data['city'], str(date_today), data['temp'], data['humidity'], data['wind_speed'], data['main_condition']))
        conn.commit()

# Fetch daily summaries from the database
def get_daily_summaries():
    daily_summaries = []
    with sqlite3.connect('weather_data.db', check_same_thread=False) as conn:
        c = conn.cursor()
        for city in CITIES:
            c.execute(f"SELECT date, avg_temp, max_temp, min_temp, dominant_condition FROM daily_weather_summary WHERE city=?", (city,))
            summaries = c.fetchall()
            daily_summaries.extend([(city, *summary) for summary in summaries])
    return daily_summaries

# Fetch current weather data
def get_weather_data():
    weather_data = {}
    for city in CITIES:
        data = fetch_weather(city)
        if data:
            weather_data[city] = data
            save_weather_data(data)
    return weather_data

# Generate weather chart for visualization
def generate_weather_chart():
    plot_urls = {}
    for city in CITIES:
        plot_urls[city] = generate_visualization(city)
    return plot_urls

# Main function to continuously fetch weather data in a separate thread
def run_weather_monitoring():
    while not stop_event.is_set():
        get_weather_data()  # Fetch current weather data and save to database
        for city in CITIES:
            calculate_daily_summary(city)  # Calculate daily summary
        time.sleep(INTERVAL)  # Sleep for the configured interval before next update

@app.route('/')
def index():
    weather_data = get_weather_data()  # Fetch current weather data
    daily_summaries = get_daily_summaries()  # Fetch daily summaries
    plot_urls = generate_weather_chart()  # Generate visualizations
    return render_template('index.html', 
                           weather_data=weather_data, 
                           daily_summaries=daily_summaries, 
                           alerts=alerts, 
                           plot_urls=plot_urls)  # Pass plot_urls to the template

# Start the Flask application
if __name__ == '__main__':
    init_db()  # Initialize the database
    weather_thread = Thread(target=run_weather_monitoring, daemon=True)  # Start weather monitoring in a thread
    weather_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000)  # Start the Flask application
