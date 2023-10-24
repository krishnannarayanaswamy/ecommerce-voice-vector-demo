import csv
import json

import openai
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from dotenv import dotenv_values
from cassandra.query import SimpleStatement

# Description: This file will load the clients dataset into Astra DB

# parameters #########
config = dotenv_values('.env')
openai.api_key = config['OPENAI_API_KEY']
SECURE_CONNECT_BUNDLE_PATH = config['SECURE_CONNECT_BUNDLE_PATH']
ASTRA_CLIENT_ID = config['ASTRA_CLIENT_ID']
ASTRA_CLIENT_SECRET = config['ASTRA_CLIENT_SECRET']
ASTRA_KEYSPACE_NAME = config['ASTRA_KEYSPACE_NAME']
model_id = "text-embedding-ada-002"

# Open a connection to the Astra database
cloud_config = {
    'secure_connect_bundle': SECURE_CONNECT_BUNDLE_PATH
}
auth_provider = PlainTextAuthProvider(ASTRA_CLIENT_ID, ASTRA_CLIENT_SECRET)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()

with open('data/Inventory.csv', 'r') as file:
    reader = csv.reader(file)
    headers = next(reader)
    query = SimpleStatement(f"INSERT INTO {ASTRA_KEYSPACE_NAME}.inventory_data (item_code, item_name, full_description, price, stock, embedding_inventory) VALUES (%s, %s, %s, %s, %s, %s)")

    for row in reader:
        # Create a dictionary for the row using headers as keys
        row_dict = dict(zip(headers, row))

        #print(row_dict)

        # Insert client information and embedding into astra
        json_data_row = json.dumps(row_dict)

        #print(json_data_row)

        # Create embedding for client containing all the columns
        embedding_inventory = openai.Embedding.create(input=json_data_row, model=model_id)['data'][0]['embedding']

        # Insert values into Astra database
        session.execute(query, (row_dict['ItemCode'], row_dict['ItemName'], row_dict['FullDescription'], row_dict['Price'], row_dict['InStock'], embedding_inventory))

        print(f"Inserted inventory {row_dict['ItemCode']} into Astra DB")

# Close the connection to the Astra database
session.shutdown()