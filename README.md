# Disaster Prediction System

A real-time disaster prediction and alert system that monitors and predicts potential natural disasters like cyclones and earthquakes.

## Features

- Real-time cyclone risk detection using weather API and ML models
- Earthquake risk assessment using USGS data and predictive models
- Interactive NOAA hazards map integration
- Email and WhatsApp alerts for users in affected areas
- User subscription system for location-based alerts

## Prerequisites

- Python 3.8 or higher
- Redis (for Celery)
- OpenWeatherMap API key
- Gmail account (for email alerts)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/disaster-prediction.git
cd disaster-prediction
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your credentials:
```
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
DJANGO_SECRET_KEY=your_django_secret_key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

7. Start Celery worker (in a separate terminal):
```bash
celery -A myproject worker -l info
```

8. Start Celery beat (in a separate terminal):
```bash
celery -A myproject beat -l info
```

## Usage

1. Visit http://127.0.0.1:8000/
2. Subscribe to alerts by providing your location and contact details
3. Receive real-time alerts when potential disasters are detected in your area

## Testing

Run the risk detection test:
```bash
python test_risk_detection.py
```

## Developed by Spectaculars in MGIT National Level Hackathon

### Authors
1. [G.R.S. Akshay Rushi](https://github.com/PhantomChillz)
2. [K. Akshay Reddy](https://github.com/A-R-K-7)
3. [G. Harshitha](https://github.com/Harshitha9407)
4. [I. Sri Bala Tejesh](https://github.com/SRIBALATEJESH)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
