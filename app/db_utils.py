import requests
import pathlib
import configparser
import os
import pandas as pd
import traceback


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

    url, headers = dbconfig()
    result = query_GQL("get_package_items", {"package_id": int(package_id)})
    
    
    
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

def getPieceInfo(pieceID):
    query = f'''
    query get_handrail_from_pid {{
    productionItemByScan(scan: "{pieceID}") {{
        id,
        piece_number,
        order{{
        order_number
        }},
        lineItem{{
        id,
        name,
        handrail_style
        }},
        finishOption{{
        name
        }},
        material{{
        name
        }},
        product{{
        handrail_length
        website_image_override_url
        }}
    }}
    }}
    '''

    url, headers = dbconfig()
    request = requests.post(url=url, json={'query': query}, headers=headers)
    
    print(str(request.status_code))
    
    if request.status_code == 200:
        # Return only the dictionary contents at the orderlineitems level of the query results.
        request = request.json()
        print(request)
        #get the data from query
        try:
            resultsDF = pd.json_normalize(request['data']['productionItemByScan'])
            resultsDF = resultsDF.fillna("none")
        except Exception as error:
            print(error)

        print(resultsDF)
    
    return resultsDF

def get_terminal_file_url(package, filename):
    query=f"""query getTerminalFile{{
            package(id: {package}){{
                order{{
                    id
                    order_number
                    files{{
                        name
                        download_permalink
                        viewable_permalink
                    }}
                }}
            }}
    }}
    """
    url, headers = dbconfig()
    request = requests.post(url=url, json={'query': query}, headers=headers)
    
    
    if request.status_code == 200:
        # Return only the dictionary contents at the orderlineitems level of the query results.
        request = request.json()
        
        #get the data from query
        
        #parentLevelPackageItems = request['data']['package']['packableItems']
     
        files = request['data']['package']['order']["files"]
        print(files)
        url = ""
        for file in files:
            print(file["name"])
            if filename in file["name"]:
                url = file["viewable_permalink"]
        
        if url == "":
            raise Exception
        else:
            return url
        
def upload_file_to_terminal(pdf_type, part, pdf_path, order_id):
    uploadpath = pdf_path
    # filename = uploadpath.split('/')[-1]
    
    pack_filename = f'{pdf_type}_{part}_Combined.pdf'
    with open(uploadpath, "rb",buffering=0) as file_data:
        file_data.name = pack_filename
        
        # This is an example of uploading a file to an Order using and order id
        params = {"file_object": file_data,
                  "id_type":"ORDER",
                  "id":order_id}
        
        # This is an example of uploading a file to a Line Item using a Line Item id
        #params = {"fileobject": f,"idtype":"LINE_ITEM","id":11878375}
        result = mutation_GQL("upload_file_to_terminal", params)
        result = client.execute(query, variable_values=params, upload_files=True)

    return result['uploadFiles'][0]['url']


def dbconfig():
    transport = RequestsHTTPTransport(url=GQL_URL, headers={'x-api-key': GQL_API_KEY}, timeout=60)
    timeout = aiohttp.ClientTimeout(total=60, connect=60)

    # Create a GraphQL client using the transport
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

def query_GQL(scope = str, filename=str, params=dict):
    query = gql((Path.cwd() / 'gql' / scope / f"{filename}.graphql").read_text())
    client = dbconfig()
    result = client.execute(query, variable_values=params, timeout=60)
    return result

def mutation_GQL(scope = str, filename=str, params=dict):
    query = gql((Path.cwd() / "gql" / scope / f"{filename}.graphql").read_text())
    client = dbconfig()
    result = client.execute(query, variable_values=params)
    return result