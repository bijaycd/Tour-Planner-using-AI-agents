from ollama import Client
from datetime import datetime, timedelta
import logging


class ItineraryGenerator:
    def __init__(self):
        self.client = Client(host="http://localhost:11434")
        logging.info("ItineraryGenerator initialized with Llama2 model.")

    def generate_itinerary(self, city, interests, start_time, end_time):
        prompt = (
            f"Plan a one-day trip in {city} starting from {start_time} to {end_time}. "
            f"The user is interested in: {', '.join(interests)}. "
            "Provide an itinerary with hourly activities, covering each interest, check transportation availability, and balancing exploration, meals, and relaxation."
        )
        logging.info(f"Prompt sent to Llama2: {prompt}")

        try:
            response = self.client.chat(model="llama3.2:latest", messages=[{"role": "user", "content": prompt}])
            logging.info(f"Full Llama2 Response: {response}")  

            if hasattr(response, "message") and hasattr(response.message, "content"):
                generated_text = response.message.content
                logging.info("Successfully extracted 'content' from Llama2 response.")

                itinerary = self.parse_hour_by_hour(generated_text, start_time, end_time)
                return itinerary

            logging.error("Llama2 response does not contain 'message' or 'content'.")
            return "Error: Llama2 response is missing 'message' or 'content'."

        except Exception as e:
            logging.error(f"Failed to generate itinerary: {e}")
            return f"Error: {str(e)}"

    def parse_hour_by_hour(self, generated_text, start_time, end_time):
        """Custom parser to create an hour-by-hour itinerary from generated text."""
        logging.info("Parsing itinerary text into hour-by-hour format.")

        generated_lines = generated_text.strip().split("\n")
        itinerary = []
        try:
            current_time = datetime.strptime(start_time, "%I:%M %p")
            end_time_dt = datetime.strptime(end_time, "%I:%M %p")

            for line in generated_lines:
                line = line.strip()
                if line and "**" not in line:  
                    time_str = current_time.strftime("%I:%M %p")
                    itinerary.append(f"{time_str}: {line}")

                    current_time += timedelta(hours=1)
                    if current_time >= end_time_dt:
                        break  

            parsed_itinerary = "\n".join(itinerary)
            logging.info(f"Parsed Itinerary: {parsed_itinerary}")
            return parsed_itinerary

        except Exception as e:
            logging.error(f"Error parsing itinerary: {e}")
            return "Error: Unable to parse the generated itinerary."

