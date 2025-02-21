import streamlit as st
from itinerary_generator import ItineraryGenerator
from weather_agent import WeatherAgent
from news_agent import NewsAgent
from memory_agent import MemoryAgent
from ollama import Client  
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
from datetime import datetime, date, time
from opencage.geocoder import OpenCageGeocode
import os
import requests
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')
load_dotenv()
API_BASE_URL = "http://localhost:8000"


#initialise base tools
generator = ItineraryGenerator()
weather_agent = WeatherAgent()
news_agent = NewsAgent()
memory_agent = MemoryAgent()

llm_client = Client(host="http://localhost:11434")

st.set_page_config(page_title="JourneyGPT", layout="wide")
st.title("JourneyGPT")
st.subheader("Your Personal Toor Planner and Journey Companion")

if "trip_submitted" not in st.session_state:
    st.session_state.trip_submitted = False
if "query_processed" not in st.session_state:
    st.session_state.query_processed = False

st.header("Help Us Know You")
user_id = st.text_input("Please enter your User Name or User ID:")



if user_id:
    # Retrieve user preferences and memories
    user_preferences = requests.get(f"http://localhost:8000/user/preferences/{user_id}").json()
    user_memories = requests.get(f"http://localhost:8000/user/memories/{user_id}").json()

    if user_memories:
        st.write(f"Welcome back, {user_id}!")
        st.subheader("Your Details:")
        for memory in user_memories:
            st.write(f"- {memory}")
    else:
        st.write("Hello, new user! Please fill up the registration form!")






    # Input form
    
    st.header("Trip Details")
    with st.form("trip_form"):
        # Autofill values from memory or session state
        city = st.text_input("City you want to visit:", value=st.session_state.city if "city" in st.session_state else  "")
        trip_date = st.date_input("Date of your trip:", value=st.session_state.date if "date" in st.session_state else date.today())
        start_time = st.time_input("Start time:", value=st.session_state.start_time if "start_time" in st.session_state else time(9, 0))
        end_time = st.time_input("End time:", value=st.session_state.end_time if "end_time" in st.session_state else time(19, 0))
        interests = st.multiselect(
            "Select your interests:",
            ["Historical Sites", "Beaches", "Shopping", "Food Experiences", "Nature", "Art Galleries"],
            default=st.session_state.interests if "interests" in st.session_state else (user_preferences if user_preferences else [])
        )
        budget = st.number_input("Budget for the day (in Euros):", min_value=0, value=100)
        start_location = st.text_input("Starting location (e.g., hotel or landmark):", "")

        submit_button = st.form_submit_button("Submit Form")

    if submit_button:
        st.session_state.trip_submitted = True
        st.session_state.city = city
        st.session_state.date = trip_date
        st.session_state.start_time = start_time
        st.session_state.end_time = end_time
        st.session_state.interests = interests

        # Save details to memory using FastAPI
        requests.post("http://localhost:8000/user/memories/", json={"user_id": user_id, "memory": f"Planned trip to {city} on {trip_date.strftime('%Y-%m-%d')}"})
        for interest in interests:
            requests.post("http://localhost:8000/user/preferences/", json={"user_id": user_id, "preference": interest})



#Query Chatbot

if st.session_state.trip_submitted:
    st.header("How may I help you")
    user_query = st.text_input("Ask a question :", key="user_query")

    if user_query:
        prompt = f"""
            
            You are an intelligent assistant designed to route user queries to specific functions or respond directly if no function matches. Analyze the query and do the following:

            1. If the query matches one of the functions, respond **only with the corresponding number**:
            - 0: generate_itinerary (Plan a day trip in a specified city based on time range and interests.)
            - 1: get_weather (Fetch the weather forecast for a specified city and date.)
            - 2: get_local_events (Retrieve local events in a specified city for a given date.)

            2. If the query is unrelated to these functions, respond directly to the user query with a concise and relevant answer. Do not mention the function or numbers in this case.

            ### Examples:
            #### Queries that match functions:
            - Query: "Plan a trip to Paris for sightseeing from 9 AM to 7 PM."
            Response: 0
            - Query: "What will the weather be in New York on 2025-01-20?"
            Response: 1
            - Query: "Are there any events in Tokyo tomorrow?"
            Response: 2
            - Query: "Create a day itinerary for Rome focused on food and art from 10 AM to 6 PM."
            Response: 0
            - Query: "Can you tell me the weather in London on March 15, 2025?"
            Response: 1
            - Query: "Find me local events happening in Los Angeles on January 22."
            Response: 2

            

            #### Queries unrelated to functions:
            - Query: "What is the tallest building in the world?"
            Response: The tallest building in the world is the Burj Khalifa in Dubai.
            - Query: "Who won the FIFA World Cup in 2018?"
            Response: France won the FIFA World Cup in 2018.
            - Query: "What is the capital of Japan?"
            Response: The capital of Japan is Tokyo.
            - Query: "How many continents are there in the world?"
            Response: There are seven continents in the world: Africa, Antarctica, Asia, Australia, Europe, North America, and South America.
            - Query: "Explain quantum mechanics briefly."
            Response: Quantum mechanics is the branch of physics that studies phenomena at very small scales, such as atoms and subatomic particles. It describes the behavior of matter and energy using principles like wave-particle duality and uncertainty.

            Now respond:
            Query: {user_query}
            Response:
            """


        try:
            response = llm_client.chat(model="llama3.2:latest", messages=[{"role": "user", "content": prompt}])
            llm_content = response["message"]["content"].strip()

            # Check if response is a valid number or a fallback answer
            try:
                llm_output = int(llm_content)

                if llm_output == 0:
                    # Generate itinerary
                    with st.spinner("Generating your itinerary..."):
                        itinerary = generator.generate_itinerary(
                            st.session_state.city,
                            st.session_state.interests,
                            st.session_state.start_time.strftime("%I:%M %p"),
                            st.session_state.end_time.strftime("%I:%M %p")
                        )
                        st.success("Itinerary generated!")
                        st.text_area("Your Itinerary:", itinerary, height=200, key="itinerary_output")

                elif llm_output == 1:
                    # Fetch weather
                    with st.spinner("Fetching weather information..."):
                        weather_info = weather_agent.get_weather(st.session_state.city, st.session_state.date.strftime("%Y-%m-%d"))
                        st.subheader("Weather Forecast")
                        st.write(weather_info, key="weather_output")

                elif llm_output == 2:
                    # Fetch local events
                    with st.spinner("Fetching local events..."):
                        local_events = news_agent.get_local_events(st.session_state.city, st.session_state.date.strftime("%Y-%m-%d"))
                        st.subheader("Local Events")
                        if local_events:
                            for event in local_events:
                                st.write(f"**Event**: {event['title']} at {event['location']} from {event['time']}")
                        else:
                            st.write("No events found for this date.")
               


            except ValueError:
                st.info("Model responded with a direct answer:")
                st.write(llm_content)
        
        except Exception as e:
            st.error(f"An error occurred while processing your query: {e}")
       
       
       
       
       
       
       #Function to show map 
if "city" in st.session_state and st.session_state.city:
    st.header("City Map")

    def get_city_coordinates(city_name):
        geocoder = OpenCageGeocode(OPENCAGE_API_KEY)
        result = geocoder.geocode(city_name)
        if result and len(result):
            return result[0]['geometry']['lat'], result[0]['geometry']['lng']
        return None, None

    lat, lon = get_city_coordinates(st.session_state.city)
    if lat and lon:
        city_map = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup=f"{st.session_state.city}").add_to(city_map)
    else:
        city_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Default location: India
        st.warning("Unable to fetch the location for the specified city. Displaying default view.")
    st_folium(city_map, width=700, height=500)
