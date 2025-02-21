import logging
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import time
load_dotenv()
logging.basicConfig(level=logging.INFO)

class MemoryAgent:
    def __init__(self):
        uri = os.getenv('NEO4J_URI')
        user = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')

        logging.info(f"Connecting to Neo4j with URI: {uri} and User: {user}")

        if not uri or not user or not password:
            logging.error("Missing required Neo4j environment variables.")
            raise ValueError("Missing required environment variables for Neo4j connection.")

        try:
            self.driver = GraphDatabase.driver(
                uri, auth=(user, password), max_connection_lifetime=1000, connection_timeout=30
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
                logging.info("Connected to Neo4j successfully.")
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise e

    def close(self):
        if self.driver:
            self.driver.close()
            logging.info("Closed Neo4j connection.")

    def add_memory(self, user_id, memory):
        logging.info(f"Adding memory for user_id: {user_id}")
        with self.driver.session() as session:
            try:
                session.write_transaction(self._create_and_return_memory, user_id, memory)
                logging.info("Memory added successfully.")
            except Exception as e:
                logging.error(f"Error adding memory for user_id {user_id}: {e}")

    @staticmethod
    def _create_and_return_memory(tx, user_id, memory):
        query = """
            MERGE (u:User {id: $user_id})
            CREATE (u)-[:HAS_MEMORY]->(m:Memory {content: $memory, timestamp: datetime()})
            RETURN m
        """
        tx.run(query, user_id=user_id, memory=memory)

    def retrieve_memories(self, user_id):
        logging.info(f"Retrieving memories for user_id: {user_id}")
        with self.driver.session() as session:
            try:
                result = session.read_transaction(self._get_memories, user_id)
                memories = [record["memory_content"] for record in result]
                logging.info(f"Memories retrieved: {memories}")
                return memories
            except Exception as e:
                logging.error(f"Error retrieving memories: {e}")
                return []

    @staticmethod
    def _get_memories(tx, user_id):
        query = """
            MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m:Memory)
            RETURN m.content AS memory_content ORDER BY m.timestamp DESC
        """
        return list(tx.run(query, user_id=user_id))


    def add_user_preference(self, user_id, preference):
        logging.info(f"Adding preference for user_id: {user_id}")
        with self.driver.session() as session:
            try:
                session.write_transaction(self._create_and_return_preference, user_id, preference)
                logging.info("Preference added successfully.")
            except Exception as e:
                logging.error(f"Error adding preference: {e}")

    @staticmethod
    def _create_and_return_preference(tx, user_id, preference):
        query = """
            MERGE (u:User {id: $user_id})
            MERGE (p:Preference {name: $preference})
            MERGE (u)-[:HAS_PREFERENCE]->(p)
        """
        tx.run(query, user_id=user_id, preference=preference)

    def get_user_preferences(self, user_id):
        logging.info(f"Retrieving preferences for user_id: {user_id}")
        with self.driver.session() as session:
            try:
                preferences = session.read_transaction(self._get_preferences, user_id)
                preference_list = [record["preference_name"] for record in preferences]
                logging.info(f"Preferences retrieved: {preference_list}")
                return preference_list
            except Exception as e:
                logging.error(f"Error retrieving preferences: {e}")
                return []

    @staticmethod
    def _get_preferences(tx, user_id):
        query = """
            MATCH (u:User {id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
            RETURN p.name AS preference_name
        """
        return list(tx.run(query, user_id=user_id))

