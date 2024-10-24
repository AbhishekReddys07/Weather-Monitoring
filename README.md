# Weather-Monitoring

## Overview
The Weather Monitoring System is a web application that continuously retrieves weather data for major metros in India using the OpenWeatherMap API. The application processes this data to provide summarized insights, including daily weather summaries, alert thresholds, and visualizations.

Note: Please ensure that your device is connected to the internet. The main python is fetch_weather.py
## Features

- Real-time weather data retrieval for specified cities.
- Daily weather summaries stored in a SQLite database.
- Configurable alert thresholds for specific weather conditions.
- Visualizations of weather data using Matplotlib.

## Technologies Used

- **Python**: The primary programming language for developing the application.
- **Flask**: A micro web framework for Python used to build the web application.
- **SQLite**: A lightweight database for storing weather data locally.
- **Requests**: A Python library for making HTTP requests to the OpenWeatherMap API.
- **Matplotlib**: A plotting library for creating visualizations of weather data.
- **Docker**: For containerizing the application and its dependencies.

## Setup Instructions

### Prerequisites

- **Docker**: Ensure you have Docker installed on your machine. You can download it from [docker.com](https://www.docker.com/get-started).
- **Docker Compose**: Included with Docker installations.

### Installation

1. **Clone the Repository**: Clone this repository to your local machine using:
    ```bash
    [git clone https://github.com/yourusername/weather-monitoring-system.git]
    (https://github.com/AbhishekReddys07/Weather-Monitoring)
    ```


2. **Navigate to the Project Directory**:
    ```bash
    cd weather-monitoring-system
    ```

3. **Create a `.env` File**:
    - Create a `.env` file in the root directory of your project. This file will store your environment variables. 
    - Add your OpenWeatherMap API key to this file:
      ```bash
      echo "API_KEY=your_api_key_here" > .env
      ```
      (Replace `your_api_key_here` with your actual API key from OpenWeatherMap.)

4. **Modify the Cities List**:
    - Open the `app.py` file and update the `CITIES` list to include the cities you want to monitor:
      ```python
      CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
      ```

5. **Build and Run the Application with Docker**:
    - Start the application using Docker Compose:
      ```bash
      docker-compose up --build
      ```

### Accessing the Application

- Once the application is running, open your web browser and navigate to `http://127.0.0.1:5000/` to access the Weather Monitoring System.

## Dependencies

- **Flask**: Web framework for building the application.
- **Requests**: Library for making HTTP requests.
- **Matplotlib**: Library for data visualization.
- **SQLite**: Database for storing weather data.

These dependencies will be managed through the Dockerfile and included in the container build process.

## Key Functions

- **`fetch_weather_data(city)`**: 
  - Fetches weather data from the OpenWeatherMap API for a specified city.
  
- **`process_weather_data(data)`**: 
  - Processes the raw weather data fetched from the API.

- **`store_weather_data(city, weather_info)`**: 
  - Stores the processed weather information in the SQLite database.
  
- **`get_daily_summary(city)`**: 
  - Retrieves and displays the daily summary of weather data for a specific city from the database.

## Design Choices

- **Model-View-Controller (MVC)**: 
  - The project follows the MVC pattern for separating concerns. The Model handles data interactions, the View renders the HTML, and the Controller manages application logic.

- **Singleton Pattern**: 
  - Used for the database connection to ensure a single instance throughout the application.

- **Facade Pattern**: 
  - Simplifies interactions with the OpenWeatherMap API, providing a clear interface for data retrieval and processing.

- **Containerization with Docker**: 
  - The application is containerized to ensure consistent environments across different setups, simplifying deployment and scalability.

## Docker Configuration

### Dockerfile

Here's a sample `Dockerfile` for the application:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
