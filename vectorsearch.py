# Import libraries
import streamlit as st
import pandas as pd
import openai
import os
import json
from langdetect import detect_langs

from cassandra.cluster import Session
from cassandra.query import PreparedStatement, SimpleStatement
from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider

# Page setup
st.set_page_config(page_title="PTC Product Recommendations powered by DataStax Astra", layout="wide")
st.title("PTC Product Recommendations powered by DataStax Astra Vector Search")

open_api_key= os.environ.get('openai_api_key')
openai.api_key = open_api_key

def detect_brand(customer_query):
    message_objects = []
    message_objects.append({"role":"system",
                            "content":"Extract product brand name, category, keywords, price range from a user query and respond the detected pair in a json formatted string like this .. {\"brand\": \"brand\", \"category\":\"\", \"keywords\":\"\", \"price\": { \"amount\": 1.0, \"operator\":\"\"}} operator can be \">\" , \"<\". Respond only json object, no need any description or code. if brand is not found, leave it empty"})

    message_objects.append({"role":"user",
                            "content": customer_query})

    completion = openai.ChatCompletion.create(
    model="gpt-4",
    messages=message_objects
    )

    brand_category = completion.choices[0].message['content']

    filter_keyword=json.loads(brand_category)
    brand = str(filter_keyword['brand'].upper())
    category = str(filter_keyword['category'].upper())
    print("System detected brand with GPT 4: " + brand)
    print("System detected category with GPT 4: " + category)
    return brand, category

def translate_lang(query):
    message_objects = []
    message_objects.append({"role":"user",
                        "content": "Translate Khmer to English:'" +  query + "'"})
    completion = openai.ChatCompletion.create(
    model="gpt-4", 
    messages=message_objects
    )
    text_in_en = completion.choices[0].message.content
    print("System translated text with GPT 4:" + text_in_en)
   
    return text_in_en

def get_session(scb: str, secrets: str) -> Session:
    """
    Connect to Astra DB using secure connect bundle and credentials.

    Parameters
    ----------
    scb : str
        Path to secure connect bundle.
    secrets : str
        Path to credentials.
    """

    cloud_config = {
        'secure_connect_bundle': scb
    }

    with open(secrets) as f:
        secrets = json.load(f)

    CLIENT_ID = secrets["clientId"]
    CLIENT_SECRET = secrets["secret"]

    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    return cluster.connect()


session = get_session(scb='./config/secure-connect-multilingual.zip',
                          secrets='./config/krishnan.narayanaswamy@datastax.com-token.json')

#df = pd.read_csv(url, dtype=str).fillna("")

# Use a text_input to get the keywords to filter the dataframe
text_search = st.text_input("Search products", value="")

if text_search:
    #langs = detect_langs(text_search)
    #language = langs[0].lang
    #print(language)
    
    customer_text = []
    #if language == "en":
    #    customer_query_en = text_search
    #else:
    customer_query_en = translate_lang(text_search)
    customer_text = []
    customer_text.append(customer_query_en)
    model_id = "text-embedding-ada-002"
    embeddings = openai.Embedding.create(input=customer_text, model=model_id)['data'][0]['embedding']

    brand, category = detect_brand(customer_query_en)

    if brand != "": 
        query = SimpleStatement(
        f"""
        SELECT *
        FROM ecommerce.inventory_data
        WHERE item_name : ' + {brand} + '
        ORDER BY embedding_inventory ANN OF {embeddings} LIMIT 5;
        """
        )
    else:
        query = SimpleStatement(
        f"""
        SELECT *
        FROM ecommerce.inventory_data
        ORDER BY embedding_inventory ANN OF {embeddings} LIMIT 5;
        """
        )

    results = session.execute(query)
    top_5_products = results._current_rows
    response = []
    for r in top_5_products:
        response.append({
            'id': r.item_code,
            'name': r.item_name,
            'description': r.full_description,
            'price': r.price
        })
    print(response)
    df = pd.DataFrame(response)
    st.write(df)