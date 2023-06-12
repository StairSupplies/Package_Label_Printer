from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(url='https://terminal.stairsupplies.com/graphql',
                             headers={'x-api-key': 'Q5dhUlEkJXG5T4ABebLwmHXbjXht5Y'})
client = Client(transport=transport)


# Create the GQL query object to upload the things, the GQL Variables are "fileobject" and "id" and "idtype"
# fileobject is the file object you pull up in python, ID type is whether it is a Product, Order or Line Item you want to add a file to.
# Fileable_group will be deprecated.
query = gql('''
        mutation gql($fileobject: Upload!,$idtype:RelationType!,$id: ID!) { 
        uploadFiles(input:{
        files: [$fileobject]
        fileable_id: $id
        fileable_type: $idtype
        fileable_group: CUSTOMER
        }
        ) {
            id 
            name  
            url
        }
        }
    '''
)

def upload_file_to_Terminal(pdf_type, part, pdf_path, order_id):
    uploadpath = pdf_path
    # filename = uploadpath.split('/')[-1]
    
    pack_filename = f'{pdf_type}_{part}_Combined.pdf'
    with open(uploadpath, "rb",buffering=0) as f:
        f.name = pack_filename
        
        # This is an example of uploading a file to an Order using and order id
        params = {"fileobject": f,
                  "idtype":"ORDER",
                  "id":order_id}
        
        # This is an example of uploading a file to a Line Item using a Line Item id
        #params = {"fileobject": f,"idtype":"LINE_ITEM","id":11878375}
        
        result = client.execute(
            query, variable_values=params, upload_files=True,
        )

    return result['uploadFiles'][0]['url']


