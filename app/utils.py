import qrcode
import requests
import fitz
import socket
import pandas as pd
import json

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
import aiohttp

import os
from os import environ as env
from pathlib import Path
from dotenv import load_dotenv
 
LETTER_DICT = {319903 : 'B', 
        319905 : 'B',
        319904 : 'B',
        319906 : 'B',
        319907 : 'C',
        319909 : 'C',
        319908 : 'C',
        319910 : 'C',
        268728 : 'F3',
        268725 : 'F3',
        281610 : 'F3',
        554585: 'F3',
        463500: 'F3',
        268727 : 'F5',
        280307 : 'F5',
        463502: 'F5',
        268726 : 'F7',
        280305 : 'F7',
        279825 : 'H',
        281789 : 'H',
        280228 : 'H',
        281790 : 'H',
        463496 : 'H',
        463498 : 'H',
        525318: 'H',
        525336: 'H',
        525324: 'H',
        289022 : 'I',
        289023 : 'I',
        289024 : 'I',
        289025 : 'I',
        289026 : 'I',
        289027 : 'I',
        323516 : 'I',
        323630 : 'I',
        323631 : 'I',
        323632 : 'I',
        323633 : 'I',
        323634 : 'I',
        268832 : 'P',
        268833 : 'P',
        268834 : 'P',
        268835 : 'P',
        280243 : 'P',
        280245 : 'P',
        280313 : 'P',
        280314 : 'P',
        378950 : 'P',
        278220 : 'W',
        278221 : 'W',
        280301 : 'W',
        280303 : 'W',
        533560: 'W',
        272083 : 'WF',
        272084 : 'WF',
        322206 : 'WF',
        322257 : 'WF',
        464472: 'WF',
        278227 : 'X',
        278228 : 'X',
        280287 : 'X',
        280289 : 'X',
        512022 : 'XT',
   }

USE_STAGING = os.environ.get("DEV")
GQL_API_KEY = os.environ.get("API-KEY")

GQL_URL = env["GRAPHQL_URL"]
GQL_API_KEY = env["GRAPHQL_API_KEY"]
DB_HOST = env['DB_URL'],
DB_DATABASE = env['DB_DATABASE'],
DB_USER = env['DB_USER'],
DB_PASSWORD = env['DB_PASSWORD']


def make_qr_code(string):
        qr = qrcode.make(string, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.save(os.getcwd() + "/app/static/label_pdf/merged_qr_code.png")
        qr_path = os.getcwd() + r"/app/static/label_pdf/merged_qr_code.png"
        return qr_path

def download_file(url, filename):
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        
        output_dir = os.getcwd()+"\\app\\static\\download_temp_files\\"
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        # Save the PDF file
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    
    else:
        print("Failed to download the PDF file.")
    return file_path

def highlight_text_in_pdf(input_path, output_path, search_text):
    # Open the PDF file
    doc = fitz.open(input_path)

    # Iterate over each page of the PDF
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text_instances = page.search_for(search_text)

        # Highlight each instance of the search text
        for inst in text_instances:
            highlight = page.add_highlight_annot(inst)

            # Set the color of the highlight
            #highlight.update(fill=(255, 255, 0))

    # Save the modified PDF to a new file
    doc.save(output_path)
    doc.close()
    return output_path

def get_local_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(('8.8.8.8', 80))
        server_ip = sock.getsockname()[0]
        print(server_ip)
    return server_ip
    
def remove_temp_files():
    directory = 'app\static\label_pdf'
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path) # uncomment to delete subdirectories
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    directory = 'app\static\download_temp_files'
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path) # uncomment to delete subdirectories
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def get_printer_settings(hostname):
    printer_settings_df = pd.read_csv("app\printer_settings.csv")
    row = printer_settings_df[printer_settings_df["hostname"] == hostname].reset_index()
    print(row)
    if len(row) > 0:
        settings_dict = {
            "printer_1": {"name": row.at[0,"printer_1_name"],
                            "type": row.at[0,"printer_1_type"]},
            "printer_2":  {"name": row.at[0,"printer_2_name"],
                        "type": row.at[0,"printer_2_type"]},
            "printer_3": {"name": row.at[0,"printer_3_name"],
                        "type": row.at[0,"printer_3_type"]}
        }
        print(json.dumps(settings_dict))
    else:
        settings_dict = {}
    return settings_dict

def create_settings_entry(hostname):
    printer_settings_df = pd.read_csv("app\printer_settings.csv")
    
    new_row = {"hostname": hostname, "printer_1_name":"printer_1","printer_1_type":"none","printer_2_name":"printer_2","printer_2_type":"none","printer_3_name":"printer_3","printer_3_type":"none"}
    printer_settings_df = printer_settings_df.append(new_row, ignore_index=True)
    printer_settings_df.to_csv("app\printer_settings.csv", index=False)
    print()
    return True

def update_printer_settings(update_json, hostname):
    printer_settings_df = pd.read_csv("app\printer_settings.csv")
    row = printer_settings_df[printer_settings_df["hostname"] == hostname].reset_index()
    
    printer_settings_df.loc[printer_settings_df['hostname'] == hostname, ['printer_1_name', 'printer_1_type', 'printer_2_name', 'printer_2_type', 'printer_3_name', 'printer_3_type']] = [update_json["printer_1"]["name"],
                                                                                                                                                                                          update_json["printer_1"]["type"],
                                                                                                                                                                                          update_json["printer_2"]["name"],
                                                                                                                                                                                          update_json["printer_2"]["type"],
                                                                                                                                                                                          update_json["printer_3"]["name"],
                                                                                                                                                                                          update_json["printer_3"]["type"],
                                                                                                                                                                                            ]
    printer_settings_df.to_csv("app\printer_settings.csv", index=False)

def send_request_printall(url, override, quantity):
    print(f"Sending {quantity} to Printall server {override}")
    
    payload = {
            "print_type": "url",
            "urls": [url],
            "override": override,
            "print_quantity": quantity
        };

    print(payload)
    endpoint = "https://printall.local.stairsupplies.com"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload)
    
    response = requests.post(url=endpoint, headers=headers, data=data)
    print("Response Status: " + str(response.status_code))

    return response.status_code


