from flask import render_template, request
from flask_socketio import SocketIO, emit 
from app import app
import json
import regex as re
import traceback
import time

from app.db_utils import *
from app.pdf import *


socketio = SocketIO(app, cors_allowed_origins="*", access_control_allow_origins="*")

#create directories if missing
PDF_DOWNLOADS_PATH = os.getcwd() + "\\app\\static\\download_temp_files"
PDF_LABELS_PATH = os.getcwd() + "\\app\\static\\label_pdf"
PDF_LABEL_QR_PATH = os.getcwd() + "\\app\\static\\qr_codes"
PDF_MERGED_PATH = os.getcwd() + "\\app\\static\\merged_pdf"
os.makedirs(PDF_DOWNLOADS_PATH, exist_ok=True)
os.makedirs(PDF_LABELS_PATH, exist_ok=True)
os.makedirs(PDF_LABEL_QR_PATH, exist_ok=True)
os.makedirs(PDF_MERGED_PATH, exist_ok=True)
remove_temp_files()
SERVER_IP = get_local_host_ip()

SERVER_URL = f"http://{SERVER_IP}:5050/static/download_temp_files/"
print(SERVER_URL)

#Render page for Scan Input
# @app.route('/custom', methods=['POST', 'GET'])
# def custom_default():
#     hostname = request.remote_addr
#     print(hostname)
#     #look for existing settings for this ip
#     json_data = get_printer_settings(hostname)

#     #if no entry for this printer, create one
#     if json_data == {}:
#         create_settings_entry(hostname)
#         json_data = get_printer_settings(hostname)

#     title = "Custom Package Labels"
#     return render_template("index.html", title=title, projectTitle=title, autoSelect="", json_data=json_data)

@app.route('/custom', methods=['POST', 'GET'])
@app.route('/custom/<preset>', methods=['POST', 'GET'])
def custom_preset(preset=str):
    hostname = request.remote_addr
    print(hostname)
    json_data = get_printer_settings(hostname)

    if json_data == {}:
        create_settings_entry(hostname)
        json_data = get_printer_settings(hostname)
    
    if preset == None:
        preset = ""
    print(json_data)
    title = "Custom Package Labels"
    return render_template("index.html", title=title, projectTitle=title, autoSelect=preset, json_data=json_data)


@app.route('/bulk', methods=['POST', 'GET'])
def bulk():
    hostname = request.remote_addr
    print(hostname)
    json_data = get_printer_settings(hostname)

    if json_data == {}:
        create_settings_entry(hostname)
        json_data = get_printer_settings(hostname)

    title = "Express Package Labels"

    return render_template("bulk labels.html", title=title, projectTitle=title, autoSelect="", json_data=json_data)

###########################
#Post Label Creation Screen: postLabelCreate.js

#When an order is scanned, create a label
@socketio.on("scan_submit")
def scan_submit(rawScanData, label_type, selected_printers):
    session = request.sid
    hostname = request.remote_addr
    
    #Delete old label files
    #remove_temp_files()

    try:
        if label_type == "stringer":
            try:
                package = json.loads(rawScanData)
                package_id = int(package["package_id"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    package_id = int(rawScanData)
                else:
                    socketio.emit("from_scan_submit", (False, "invalid"))
                    return 
            items_df, order_number, order_id = get_package_items(package_id)
            
            #Print a label if there is only one item in the package Stringer = 1 Item
            if len(items_df) == 1:
                
                if selected_printers[0] != "None":
                    create_stringer_label(package_id, items_df, order_number, order_id, SERVER_IP, SERVER_URL, selected_printers[0])
                if selected_printers[1] != "None":
                    print_pdf_label(resultsDF, "CUSTOMER INSTALL", "pdf_1_HL.pdf", SERVER_URL, selected_printers[1])
            else:
                create_multiple_stringer_label(package_id, items_df, order_number, order_id, SERVER_URL, selected_printers)
                print_pdf_label(resultsDF, "CUSTOMER INSTALL", "pdf_1_HL.pdf", SERVER_URL, selected_printers[1])
        
        elif label_type == "manifest":
            try:
                package = json.loads(rawScanData)
                package_id = int(package["package_id"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    package_id = int(rawScanData)
                else:
                    socketio.emit("from_scan_submit", (False, "invalid"))
                    return
            resultsDF, orderNumber, orderID = get_package_items(package_id)
            if selected_printers[0] != "None":
                createManifestLabel(package_id, resultsDF, SERVER_IP, selected_printers[0])


        elif label_type == "metal_handrail":
            print(rawScanData)
            try:
                scan_json = json.loads(rawScanData)
                oli_piece_id = int(scan_json["i"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    oli_piece_id = int(rawScanData)
                else:
                    socketio.emit("from_scan_submit", (False, "invalid"))
                    return
            print("Making Label")
            handrail_df = get_handrail_info(oli_piece_id)
            print(selected_printers[0])
            if selected_printers[0] != "None":
                complete = create_handrail_label(handrail_df, SERVER_IP, SERVER_URL, selected_printers[0])
                print(complete)
        socketio.emit("from_scan_submit", (True, "success"))
        return

    except Exception as error:
        print(str(error))
        traceback.print_exc()
        socketio.emit("from_scan_submit", (False, "no_parts_found"), room=session)
        return


@socketio.on("bulkPrintExpressPost")
def bulkPrintExpressPost(details_dict):
    session = request.sid
    print(details_dict)
    success_message = "Label Sent to Printer"
    try:
        if details_dict["config"] == "angle" and details_dict["height"] == "42":
            message = "Angle 42\" Express Posts do not Exist. No Labels Printed"
            success_bool = False
        else:
            url = f"http://{SERVER_IP}:5050/static/bulk_pdf/express_post/{details_dict['config']} {details_dict['height']}.pdf"
            print(url)
            
            #Try 2 times to print the stickers
            response_code = send_request_printall(url, details_dict["printer"], int(details_dict["quantity"]))
            if response_code != 200:
                time.sleep(1)
                response_code = send_request_printall(url, details_dict["printer"], int(details_dict["quantity"]))
                if response_code != 200:
                    message = "Cannot Connect to Print Server/Printer<br>Label(s) Not Printed<br>Status: "+ str(response_code)
                    success_bool = False
                else:
                    success_bool = True
                    message = success_message
            else:
                success_bool = True
                message = success_message
            
    except Exception as error:
        traceback.print_exc()
        message = error
        success_bool = False
    
    socketio.emit("fromBulkPrintExpressPost", (message, success_bool), room=session)
    

# Print Beverage or Handrail label
@socketio.on("printBevHandLabel")
def printBevHandLabel(details_dict):
    print("Printing Beverage/Handrail Label")
    session = request.sid
    print(details_dict)
    success_message = "Label Sent to Printer"
    try:
        url = f"http://{SERVER_IP}:5050/static/bulk_pdf/express/{details_dict['config']}.pdf"
        print(url)
            
            
        #Try 2 times to print the stickers
        response_code = send_request_printall(url, details_dict["printer"], int(details_dict["quantity"]))
        if response_code != 200:
            time.sleep(1)
            response_code = send_request_printall(url, details_dict["printer"], int(details_dict["quantity"]))
            if response_code != 200:
                message = "Cannot Connect to Print Server/Printer<br>Label(s) Not Printed<br>Status: "+ str(response_code)
                success_bool = False
            else:
                success_bool = True
                message = success_message
        else:
            success_bool = True
            message = success_message
            
    except Exception as error:
        traceback.print_exc()
        message = error
        success_bool = False
    
    socketio.emit("fromPrintBevHandLabel", (message, success_bool), room=session)

@socketio.on("updatePrintSettings")
def updatePrintSettings(update_json):
    hostname = request.remote_addr
    print(hostname)
    print(update_json)
    update_printer_settings(update_json, hostname)
    