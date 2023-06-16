import globals
from flask import render_template, request
from flask_socketio import SocketIO, emit


if globals.local:
    import waitress
else:
    from app import app

import json
import regex as re
import traceback
import time

from app.terminalDBFunctions import *
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
@app.route('/custom', methods=['POST', 'GET'])
def index1():
    hostname = request.remote_addr
    print(hostname)
    json_data = get_printer_settings(hostname)

    if json_data == {}:
        create_settings_entry(hostname)
        json_data = get_printer_settings(hostname)

    title = "Custom Label Printing"
    return render_template("index.html", title=title, projectTitle=title, autoSelect="", json_data=json_data)


@app.route('/custom/<preset>', methods=['POST', 'GET'])
def index2(preset):
    hostname = request.remote_addr
    print(hostname)
    json_data = get_printer_settings(hostname)

    if json_data == {}:
        create_settings_entry(hostname)
        json_data = get_printer_settings(hostname)

    print(json_data)
    title = "Custom Label Printing"
    return render_template("index.html", title=title, projectTitle=title, autoSelect=preset, json_data=json_data)


@app.route('/bulk', methods=['POST', 'GET'])
def bulk():
    hostname = request.remote_addr
    print(hostname)
    json_data = get_printer_settings(hostname)

    if json_data == {}:
        create_settings_entry(hostname)
        json_data = get_printer_settings(hostname)

    title = "Bulk Label Printing"

    return render_template("bulk labels.html", title=title, projectTitle=title, autoSelect="", json_data=json_data)

###########################
#Post Label Creation Screen: postLabelCreate.js

#When an order is scanned, create a label
@socketio.on("scanLabel")
def scanLabel(rawScanData, labelType, selected_printers):
    session = request.sid
    hostname = request.remote_addr
    #Delete old label files
    remove_temp_files()
    print(labelType)
    
   
    

    #Query for all unpacked Small Parts
   
    
    #Make and Print a label
    
    try:
        if labelType == "stringer":
            try:
                package = json.loads(rawScanData)
                packageID = int(package["package_id"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    packageID = int(rawScanData)
                else:
                    socketio.emit("fromScanLabel", (False, "invalid"))
                    return 
            resultsDF, orderNumber, orderID = getParts(packageID)
            
            if len(resultsDF) == 1:
                if selected_printers[0] != "None":
                    createStringerLabel(packageID, resultsDF, orderNumber, orderID, SERVER_IP, SERVER_URL, selected_printers[0])
                if selected_printers[1] != "None":
                    printPDFlabel(resultsDF, "CUSTOMER INSTALL", "pdf_1_HL.pdf", SERVER_URL, selected_printers[1])
            else:
                createMultiStringerLabel(packageID, resultsDF, orderNumber, orderID, SERVER_URL, selected_printers)
                printPDFlabel(resultsDF, "CUSTOMER INSTALL", "pdf_1_HL.pdf", SERVER_URL, selected_printers[1])
        

        elif labelType == "manifest":
            try:
                package = json.loads(rawScanData)
                packageID = int(package["package_id"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    packageID = int(rawScanData)
                else:
                    socketio.emit("fromScanLabel", (False, "invalid"))
                    return
            resultsDF, orderNumber, orderID = getParts(packageID)
            if selected_printers[0] != "None":
                createManifestLabel(packageID, resultsDF, SERVER_IP, selected_printers[0])


        elif labelType == "metal_handrail":
            print(rawScanData)
            try:
                piece = json.loads(rawScanData)
                pieceID = int(piece["i"])
            #if not, try a raw scan input
            except:
                print("Raw Order Input Detected")
                if re.search(r"\d+", rawScanData): 
                    pieceID = int(rawScanData)
                else:
                    socketio.emit("fromScanLabel", (False, "invalid"))
                    return
            
            resultsDF = getPieceInfo(pieceID)

            if selected_printers[0] != "None":
                createHandrailLabel(resultsDF, SERVER_IP, SERVER_URL, selected_printers[0])

        socketio.emit("fromScanLabel", (True, "success"))
        return

    except Exception as error:
        print(str(error))
        traceback.print_exc()
        socketio.emit("fromScanLabel", (False, "no_parts_found"), room=session)
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

if globals.local:
    waitress.serve(app, host='0.0.0.0', port=5050, threads=5) #WAITRESS!
