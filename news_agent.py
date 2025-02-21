import requests
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta  
load_dotenv()

logging.basicConfig(level=logging.INFO)

class NewsAgent:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            logging.warning("NEWS_API_KEY is missing. Using mock data.")

    def get_local_events(self, city, date):
        logging.info(f"Fetching local events for city: {city} on date: {date}")

        if not self.api_key:
            logging.info("Using mock data due to missing API key.")
            return [
                {"title": "Food Festival", "location": "City Center", "time": "1:00 PM - 4:00 PM"},
                {"title": "Historical Walk", "location": "Old Town", "time": "11:00 AM - 1:00 PM"}
            ]

        from_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        to_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f"{city} events",
            "from": from_date,
            "to": to_date,
            "sortBy": "relevance",
            "apiKey": self.api_key
        }

        try:
            logging.info(f"Sending request to NewsAPI with params: {params}")
            response = requests.get(url, params=params)
            logging.info(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logging.info(f"Response data: {data}")

                articles = data.get("articles", [])
                logging.info(f"Number of articles retrieved: {len(articles)}")

                if len(articles) == 0:
                    logging.warning("No articles found for the given query. Returning a default message.")
                    return [{"title": "No events found for this city and date", "location": "N/A", "time": "N/A"}]

                events = [
                    {"title": article["title"], "location": "Various Locations", "time": article["publishedAt"]}
                    for article in articles
                ]
                logging.info(f"Processed events: {events}")
                return events
            else:
                logging.error(f"Error fetching events: {response.text}")
                return [{"title": "Error fetching events", "location": "", "time": ""}]
        except Exception as e:
            logging.error(f"Exception occurred while fetching events: {e}")
            return [{"title": "Error fetching events", "location": "", "time": ""}]
