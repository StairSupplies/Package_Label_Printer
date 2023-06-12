import requests
import pathlib
import configparser
import os
import pandas as pd
import traceback

def dbconfig():
    moddir = os.path.abspath(os.path.dirname(__file__))

    configPath = pathlib.Path(moddir) / '.gql_config.txt'
    
    config = configparser.ConfigParser()
    config.read(configPath)
    
    url = config.get('CONNECTION', 'URL')
    
    api_token = config.get('CONNECTION', 'TOKEN')
    headers = {'x-api-key': api_token}
    return url, headers


#Use Terminals graphQL query to get order status by type
#kinda broken, when an order is completed, the query returns null... 
#but it is faster than the checkForPackedSmallParts2 query, so try this first,
# if it returns null, then call checkForPackedSmallParts2
def getParts(packageID):
    query = f"""
    query getItemsInPackage{{
        package(id: {packageID}){{
            order{{
                id
                order_number
            }}
            id
            packedItemsQuantity
            stringerVoeIds
            packableItems{{
                id
                lineItem{{
                    id
                    od1Files(type: PDF){{
                        FileName
                        FileTitle
                        url
                    }}
                    handrail_style
                    handrail_numbers_list
                }}
                id
                getProduct{{
                    id
                    name
                    stringer_length
                    website_image_override_url
                }}
                lineItemFinishes
                packableItemsPivots{{
                    quantity
                }}
                }}
            
            contents{{
                packableItems{{
                
                lineItem{{
                    id
                    od1Files(type: PDF){{
                        FileName
                        FileTitle
                        url
                    }}
                }}
                id
                getProduct{{
                    id
                    name
                    stringer_length
                    website_image_override_url
                }}
                lineItemFinishes
                packableItemsPivots{{
                    quantity
                }}
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
     
        childLevelPackageItems = request['data']['package']['contents']
             
        #Check the parent Package and get items list
        try:
            parentItemsDF = pd.json_normalize(request['data']["package"]["packableItems"])
            parentItemsDF = parentItemsDF.fillna("none")
        except:
            pass

        #Check for Child Packages and get items list
        try:
            data = request['data']["package"]["contents"]
            childItemsDF = pd.json_normalize(data, record_path=['packableItems'])
            childItemsDF = childItemsDF.fillna("none")
        except:
            pass
        
        finalItemsDF = pd.DataFrame(columns=parentItemsDF.columns)
        if not parentItemsDF.empty:
            print("Parent Items Found")
            finalItemsDF = finalItemsDF.append(parentItemsDF)
        
        if not childItemsDF.empty:
            finalItemsDF = finalItemsDF.append(childItemsDF)
        
        orderID = str(request['data']["package"]["order"]["id"])
        orderNumber = str(request['data']["package"]["order"]["order_number"])

    return finalItemsDF, orderNumber, orderID

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