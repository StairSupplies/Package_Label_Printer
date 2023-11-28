import requests
import pathlib
import configparser
import os
import pandas as pd
import traceback
import base64

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
import aiohttp

import os
from os import environ as env
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.cwd() / 'venv' / '.env')

USE_STAGING = os.environ.get("DEV")
GQL_API_KEY = os.environ.get("API-KEY")

GQL_URL = env["GRAPHQL_URL"]
GQL_API_KEY = env["GRAPHQL_API_KEY"]
DB_HOST = env['DB_URL'],
DB_DATABASE = env['DB_DATABASE'],
DB_USER = env['DB_USER'],
DB_PASSWORD = env['DB_PASSWORD']

#Use Terminals graphQL query to get order status by type
#kinda broken, when an order is completed, the query returns null... 
#but it is faster than the checkForPackedSmallParts2 query, so try this first,
# if it returns null, then call checkForPackedSmallParts2
def get_package_items(package_id):

    result = query_GQL("get_package_items", {"package_id": int(package_id)})
    print(result)
    #Check the parent Package and get items list
    try:
        package_items_df = pd.json_normalize(result['package']['contents'])
        package_items_df = package_items_df.fillna("none")
    except:
        pass

    # #Check for Child Packages and get items list
    # try:
    #     data = request['data']["package"]["contents"]
    #     childItemsDF = pd.json_normalize(data, record_path=['packableItems'])
    #     childItemsDF = childItemsDF.fillna("none")
    # except:
    #     pass
    
    filtered_items_df = pd.DataFrame(columns=package_items_df.columns)
    if not package_items_df.empty:
        print("Items Found")
        filtered_items_df = package_items_df
    
    order_id = str(result["package"]["order"]["id"])
    order_number = str(result["package"]["order"]["order_number"])

    return package_items_df, order_number, order_id

def get_handrail_info(oli_piece_id):
    result = query_GQL("get_handrail_info", {"oli_piece_id": int(oli_piece_id)})
     #try to check for a oli_piece_id
    try:
        handrail_df = pd.json_normalize(result['oliPiece'])
        handrail_df = handrail_df.fillna("none")
    except Exception as error:
        #try to check for a production item id (remove later)
        try:
            result = query_GQL("get_handrail_info_old", {"pid": int(oli_piece_id)})
            handrail_df = pd.json_normalize(result['oliPiece'])
            handrail_df = handrail_df.fillna("none")
        except Exception as error:
            traceback.print_exc()
            return False
    
    return handrail_df

def get_terminal_file_url(package_id, filename):

    result = query_GQL("get_terminal_file", {"package_id": int(package_id)})
    
    files = result['package']['order']["files"]
    print(files)
    url = ""
    for file in files:
        print(file["name"])
        if filename in file["name"]:
            url = file["viewable_permalink"]
    
    if url == "":
        return ""
    else:
        return url
        
# def upload_file_to_terminal(pdf_type, part, pdf_path, order_id):
#     uploadpath = pdf_path
#     # filename = uploadpath.split('/')[-1]
    
#     pack_filename = f'{pdf_type}_{part}_Combined.pdf'
#     with open(uploadpath, "rb",buffering=0) as file_data:
#         file_data.name = pack_filename
#         file_data = base64.b64encode(file_data).decode()
#         # This is an example of uploading a file to an Order using and order id
#         params = {"file_object": file_data,
#                   "id_type":"ORDER",
#                   "id":order_id}
        
#         # This is an example of uploading a file to a Line Item using a Line Item id
#         #params = {"fileobject": f,"idtype":"LINE_ITEM","id":11878375}
#         result = mutation_GQL("upload_file_to_terminal", params)
#         #result = client.execute(query, variable_values=params, upload_files=True)
#     print(result)
#     return result['uploadFiles'][0]['url']


def upload_file_to_terminal(pdf_type, part, pdf_path, order_id):

    # pack_filename = f'{pdf_type}_{part}_Combined.pdf'
    # with open(pdf_path, "rb") as file_data:
    #     file_content = file_data.read()  # Read the content of the file
    #     file_content = base64.b64encode(file_content).decode()  # Encode the content, not the file object
    #     params = {"file_object": file_content,
    #               "id_type":"ORDER",
    #               "id":order_id}
    #     result = mutation_GQL("upload_file_to_terminal", params)
    # print(result)
    # return result['uploadFiles'][0]['url']

    uploadpath = pdf_path
    # filename = uploadpath.split('/')[-1]
    
    pack_filename = f'{pdf_type}_{part}_Combined.pdf'
    with open(uploadpath, "rb",buffering=0) as f:
        f.name = pack_filename
        
        # This is an example of uploading a file to an Order using and order id
        params = {"file_object": f,
                  "id_type": "ORDER",
                  "id": order_id}
        
        # This is an example of uploading a file to a Line Item using a Line Item id
        #params = {"fileobject": f,"idtype":"LINE_ITEM","id":11878375}
        
        result = mutation_GQL("upload_file_to_terminal", params)

    return result['uploadFiles'][0]['url']


def dbconfig():
    transport = RequestsHTTPTransport(url=GQL_URL, headers={'x-api-key': GQL_API_KEY}, timeout=60)
    timeout = aiohttp.ClientTimeout(total=60, connect=60)

    # Create a GraphQL client using the transport
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

def query_GQL(filename=str, params=dict):
    query = gql((Path.cwd() / 'app' / 'gql' / f"{filename}.graphql").read_text())
    client = dbconfig()
    result = client.execute(query, variable_values=params, timeout=60)
    return result

def mutation_GQL(filename=str, params=dict):
    query = gql((Path.cwd() / 'app' / "gql" / f"{filename}.graphql").read_text())
    print(query)
    client = dbconfig()
    result = client.execute(query, variable_values=params)
    return result
