from langchain.tools import BaseTool

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

from dotenv import dotenv_values
import openai

import streamlit as st

### parameters #########
config = dotenv_values('.env')
openai.api_key = config['OPENAI_API_KEY']


SECURE_CONNECT_BUNDLE_PATH = config['SECURE_CONNECT_BUNDLE_PATH']
ASTRA_CLIENT_ID = config['ASTRA_CLIENT_ID']
ASTRA_CLIENT_SECRET = config['ASTRA_CLIENT_SECRET']
ASTRA_KEYSPACE_NAME = config['ASTRA_KEYSPACE_NAME']

# Open a connection to the Astra database
cloud_config = {
    'secure_connect_bundle': SECURE_CONNECT_BUNDLE_PATH
}
auth_provider = PlainTextAuthProvider(ASTRA_CLIENT_ID, ASTRA_CLIENT_SECRET)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
astra_client = cluster.connect()


class InventorySimilarityTool(BaseTool):
    name = "Inventory Similarity Tool"
    description = "This tool is used to search for ecommerce product inventory with information like item code, item name, description, price and stock availability, " \
                  "Note this does not contains user names or emails." \
                  "Example query: Suggest me best laptops that are less than $1000"

    def _run(self, user_question):
        model_id = "text-embedding-ada-002"
        embedding = openai.Embedding.create(input=user_question, model=model_id)['data'][0]['embedding']
        query = f"SELECT item_code, item_name, full_description, price, stock " \
                f"FROM {ASTRA_KEYSPACE_NAME}.inventory_data " \
                f"ORDER BY embedding_inventory ANN OF {embedding} LIMIT 5 "
        rows = astra_client.execute(query)

        inventory_list = []
        for row in rows:
            inventory_list.append({f"inventory item code is {row.item_code}, current stock is {row.stock}, inventory item code is {row.item_name}, description is {row.full_description}, price is {row.price}"})
        return inventory_list

    def _arun(self, query: str):
        raise NotImplementedError("This tool does not support async")
