
# SkyBee Routes

**AI-Powered Flight Route Optimization System**

SkyBee Routes is a Django web application that finds optimal flight paths between airports using advanced pathfinding algorithms and provides real-time flight suggestions powered by AI.

## Features

- **Dual Algorithm Route Finding**: Compare A* and Dijkstra's optimal pathfinding with Reinforcement Learning predictions.
- **Interactive Map Visualization**: View flight paths on interactive maps with Folium integration.
- **Real-time Flight Data**: Get current flight deals via Amadeus API integration.
- **AI-Powered Suggestions**: Receive intelligent flight recommendations using Google Gemini AI.
- **Dark/Light Theme**: Modern responsive UI with theme switching.
- **Comparison**: Compares the speed of A* and Dijkstra's Algorithm

## Tech Stack

- **Backend**: Django 5.2.6, NetworkX 3.3, Pandas 2.2.2
- **Frontend**: Tailwind CSS, Folium maps, Vanilla JavaScript
- **APIs**: Amadeus Flight API, Google Gemini AI
- **Algorithms**: A* pathfinding, Dijkstra's Algorithm, Q-learning Reinforcement Learning
- **Deployment**: Docker, Render

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shivamkhator/SkyBee_Routes.git
   cd SkyBee_Routes
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export AMADEUS_API_KEY="your_amadeus_api_key"
   export AMADEUS_API_SECRET="your_amadeus_api_secret"
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

4. **Run the application**
   ```bash
   cd skybee_routes
   python manage.py runserver
   ```

## Usage

1. Navigate to the web interface
2. Select departure and destination airports from the dropdown menus
3. Click "Find Route" to generate optimal paths
4. View results including:
   - A* algorithm optimal path with distance
   - Dijkstra's optimal path with distance
   - Speed comparsion with A* and Dijkstra
   - Interactive map visualization
   - AI-generated flight suggestions using Gemini

## Model Architecture

The system uses a layered architecture with:
- **Web Layer**: Django views and templates
- **Processing Layer**: NetworkX graph algorithms
- **Data Layer**: CSV-based airport and route data
- **External Services**: Amadeus API and Google Gemini AI


## Project Structure

```
SkyBee_Routes/
├── skybee_routes/                    # Django project root
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Python dependencies
│   ├── db.sqlite3                    # SQLite database (generated)
│   │
│   ├── skybee_routes/               # Main Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py              # Django settings and configuration
│   │   ├── urls.py                  # Root URL configuration
│   │   ├── wsgi.py                  # WSGI application entry point
│   │   └── asgi.py                  # ASGI application entry point
│   │
│   └── routes/                      # Main Django app
│       ├── __init__.py
│       ├── admin.py                 # Django admin configuration
│       ├── apps.py                  # App configuration
│       ├── models.py                # Database models (empty)
│       ├── tests.py                 # Unit tests (empty)
│       ├── urls.py                  # App URL patterns
│       ├── views.py                 # Main view controller
│       ├── utils.py                 # Core algorithms and data processing
│       │
│       ├── data/                    # Static data files
│       │   ├── Airports.csv         # Airport coordinates and metadata
│       │   └── Routes.csv           # Flight route connections
│       │
│       └── templates/               # Django templates
│           └── routes/
│               └── index.html       # Main web interface template
│
├── README.md                        # Project documentation
└── .env                            # Environment variables (not in repo)
```

## API Keys Required

- **Amadeus API**: For real-time flight data
- **Google Gemini API**: For AI-powered flight suggestions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Notes**

The application loads airport and route data from CSV files during initialization and builds a NetworkX graph for efficient pathfinding operations. The RL algorithm implementation includes a training loop that may cause slower response times for web requests hence we are using A* and Dijkstra's Algorithm in the live website.

## Contact

- GitHub: [@Shivamkhator](https://github.com/Shivamkhator)
- Project Link: [https://github.com/Shivamkhator/SkyBee_Routes](https://github.com/Shivamkhator/SkyBee_Routes)
```
