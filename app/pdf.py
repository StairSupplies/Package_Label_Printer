#Description: Functions to dynamically create PDF labels and print labels 
#             for printers that do not play well with CUPS (Zebra Printers)
#             This specfic file is for 3.5 x 1.375 inch labels for HPC Containers
#             Background printing function has not been tested in LINUX/MAC systems (Windows only) 

#Author: AMB
#Created: 01/12/2022

from fpdf import FPDF
import os
import time
import datetime
import qrcode
import math
import win32api
import win32gui
from pypdf import PdfWriter, PdfReader
import requests
import io
from PIL import Image
import requests
import random
import string

import globals

if globals.local:
    from terminalDBFunctions import *
    from terminalFileUploader import *
    from utils import *
else:
    from .terminalDBFunctions import *
    from .terminalFileUploader import *
    from .utils import *

LABEL_PATH = ''

DYMO_PRINTER = "DYMO LabelWriter 450"
ZEBRA_PRINTER = "Zebra ZP 500"

PDF_FOLDER = os.getcwd()+"//app//static//download_temp_files//"

#import ahk
import regex as re
#from .GoogleChatBot import *

# Try to import one way, if it fails, try the other way
try:
    from utils import LETTER_DICT
except:
    from .utils import LETTER_DICT



def createManifestLabel(packageID, resultsDF, SERVER_IP, printer):
        NUMBER_OF_ITEMS_PER_LABEL = 10

        number_of_labels = math.ceil(len(resultsDF) / NUMBER_OF_ITEMS_PER_LABEL)
        print("Number of labels: " + str(number_of_labels))
        
        for label in range(0, number_of_labels):
            #Make a QR code image
            qr = qrcode.make('{"package_id": '+ str(packageID) + '}')
            
            #save the QR code as a png
            qr.save(os.getcwd() + "/app/static/label_pdf/qr_code.png")

            #Set Paths to Images
            logo = os.getcwd()+"/app/static/img/viewrailLogoBW.png"
            #Grabs the correct part image in "label_image folder"
            #image_path = os.getcwd()+"\\app\\static\\label_image\\" + str(partNumber)+".jpg"
            #grabs the newly created qr_code
            qr_path = os.getcwd() + r"/app/static/label_pdf/qr_code.png"

            #Read "FPDF2" library documentation for more info
            #Set up PDF page (dimensions in inches)
            
            #Set label Size
            pdf = FPDF(unit='in', format=[2.25,7.4])
            #create a page
            pdf.add_page()
            #set margins
            pdf.set_margins(left=.05, top=.01, right=.1)
            pdf.set_auto_page_break(auto=False)
            
            #add images, resize, and postion
            pdf.image(logo, x=.6, y=.15, w =1)
            #pdf.image(qr_path, x=1.4, y=.1, w = .5)
            # #make new line
            
            pdf.set_line_width(.01)
            pdf.line(.05,.62,2.2,.62)
            #create Indents to postion text "Arial" "Bold" Font Size: 10 (add "border=True" argument to see cell borders)
            pdf.set_font('Arial', 'B', size=16)
            
            pdf.cell(0.05, 1, ln=True)

        
            #write Order Number
            pdf.text(.2, .9, txt='Package: '+ str(packageID))
            pdf.set_font('Arial', 'B', size=8)
            if number_of_labels > 1:
                pdf.text(0.05, 7.3, txt='Label ' + str(label+1) + " / " + str(number_of_labels))
            
            #Time stamp
            #pdf.set_font('Arial', 'B', size=7)
            #now = datetime.datetime.now()
            #pdf.cell(.05, .25, txt='Printed: ' + str(now.strftime("%m/%d/%Y %I:%M %p") + '          Label: ' + str(label+1) + " / " + str(number_of_labels)) , ln=True)

            row_count = 0
            
            for index, post in resultsDF.iterrows():
                
                if row_count >= NUMBER_OF_ITEMS_PER_LABEL:
                    #When label is complete, reset the index for the next label (since current labels rows were removed)
                    resultsDF = resultsDF.reset_index()
                    break
                
                #Add a second line if description overflows first line
                pdf.set_font('Arial','B', size=8)
                pdf.cell(.2,.15, txt="", ln=True)
                nameString = str(resultsDF.at[index, "getProduct.name"])
                lines = split_string(nameString, 39)
                for line in lines: 
                    pdf.cell(.2,.14, txt=line, ln=True)

                pdf.set_font('Arial', size=7)
                #pdf.cell(.01,.1, txt="  PRODUCT ID       FINISH                         QTY", ln=True)
                if str(resultsDF.at[index, "lineItemFinishes"]) == "none":
                    finish_option = ""
                else:
                    finish_option = str(resultsDF.at[index, "lineItemFinishes"]) 
                pdf.cell(1.85,.15, txt="  "+str(resultsDF.at[index, "getProduct.id"]) + "                 "  + finish_option)
                pdf.set_font('Arial','B', size=9)
                quantity = resultsDF['packableItemsPivots'].apply(lambda x: x[0]['quantity'])
                print(quantity)
                pdf.cell(.65,.15, txt=""+str(resultsDF.at[index,'packableItemsPivots'][0]["quantity"]), ln=True)
                pdf.cell(0.1,0.06)
                pdf.ln(.05)

                row_count += 1
                #remove row from Dataframe after rendering pdf row
                resultsDF = resultsDF.drop(index=index)
            
            #save the pdf
            output_file = os.getcwd() + f"/app/static/label_pdf/label{label}.pdf"
            pdf.output(output_file)
            

            #print label creation confirmation
            print("New Label Created")

            url = f"http://{SERVER_IP}:5050/static/label_pdf/label{label}.pdf"
            send_request_printall(url, printer, 1)
        
        return True


#Create a dynamic label with Product Image, QR Code, and Description
def createMultiStringerLabel(packageID, resultsDF, orderNumber, orderID):
        
    NUMBER_OF_ITEMS_PER_LABEL = 7

    number_of_labels = math.ceil(len(resultsDF) / NUMBER_OF_ITEMS_PER_LABEL)
    print("Number of labels: " + str(number_of_labels))
    
    for label in range(0, number_of_labels):
        
        qr1_path, qr2_path = getPDFLinks(resultsDF)

        #Set Paths to Images
        logo = os.getcwd()+"/app/static/img/viewrailLogoBW.png"
        
        #grabs the newly created qr_code
        qr_path = qr1_path

        #Read "FPDF2" library documentation for more info
        #Set up PDF page (dimensions in inches)
        
        #Set label Size
        pdf = FPDF(unit='in', format=[2.25,7.4])
        #create a page
        pdf.add_page()
        #set margins
        pdf.set_margins(left=.05, top=.01, right=.1)
        pdf.set_auto_page_break(auto=False)     
        
        try:
            pdf.set_font('Arial', 'B', size=6)
            pdf.image(qr_path, x=1.4, y=0.1, w = .8)
            pdf.text(x=1.5, y=0.1, txt="Scan for Prints")
        except:
            pass
        # #make new line
        
        pdf.set_line_width(.01)
        pdf.line(.05,.9,2.2,.9)
        #create Indents to postion text "Arial" "Bold" Font Size: 10 (add "border=True" argument to see cell borders)
        pdf.set_font('Arial', 'B', size=16)
        
        pdf.ln(0.6)

    
        #write Order Number
        pdf.cell(.05, .25, txt='Package: '+ str(packageID), ln=True)
        pdf.cell(.05, .1, txt='', ln=True)

        #Write Part Number
        pdf.set_font('Arial', 'B', size=7)
        now = datetime.datetime.now()
        pdf.text(.08, 7.3, txt='Printed: ' + str(now.strftime("%m/%d/%Y %I:%M %p") + '          Label: ' + str(label+1) + " / " + str(number_of_labels)))

        pdf.set_font('Arial','B', size=8)  
        pdf.set_font('Arial', size=8)
        
        row_count = 0
        
        for index, post in resultsDF.iterrows():
            letter = ""
            if row_count >= NUMBER_OF_ITEMS_PER_LABEL:
                #When label is complete, reset the index for the next label (since current labels rows were removed)
                resultsDF = resultsDF.reset_index(drop=True)
                break
            
            #Add a second line if description overflows first line
            
            nameString = str(resultsDF.at[index, "getProduct.name"])
            quantity = str(resultsDF.at[index,'packableItemsPivots'][0]["quantity"])
            lines = split_string(nameString, 39)
            stringer = ""
            item_title = "Stringer ID:"
            try:
                #Order pattern
                pattern = r"M\d+([A-Z]\d+)"
                match = re.search(pattern, nameString)
                if match:
                    stringer = match.group()
                    print(stringer)  # output: 01A5
                else:
                    #Remake Order PAttern
                    pattern = r"M\d+-\d+([A-Z]\d+)"
                    match = re.search(pattern, nameString)
                    if match:
                        stringer = match.group()
                        print(stringer)  # output: 01A5
                        
            except:
                pass

            if stringer == "":
                item_title = "QTY - Product ID:"
                stringer = str(resultsDF.at[index, "getProduct.id"])
                #Try to find the Shortcut Letter for Stringer Small Part
                try:
                    letter = LETTER_DICT[int(stringer)]
                except:
                    letter = ""
                
                enable_qty = True
            else:
                enable_qty = False
                letter = ""
                
            pdf.image(logo, x=.2, y=.25, w =1)
                
            pdf.set_font('Arial','B', size=6)
            pdf.cell(.2,.1, txt=item_title, ln=True)
            pdf.set_font('Arial','B', size=20)
            if enable_qty:
                #Draw shortcut letter beside the product ID
                if letter != "":
                    pdf.cell(1.6,.3, txt=quantity + " - " + stringer, ln=False)
                    
                    pdf.set_fill_color(0,-1,-1)
                    pdf.set_text_color(255,-1,-1)
                    
                    cell_width = pdf.get_string_width(letter) + .1
                    pdf.cell(cell_width, 0.3, txt=letter, ln=1, fill=True, align="C", border=1)
                    pdf.set_fill_color(50,-1,-1)
                    pdf.set_text_color(0,-1,-1)
                else:
                    pdf.cell(.2,.3, txt=quantity + " - " + stringer, ln=True)
            else:
                pdf.cell(.2,.3, txt=stringer, ln=True)
            pdf.set_font('Arial', size=8)
            
            for line in lines: 
                pdf.cell(.2,.14, txt=line, ln=True)
            pdf.cell(.2,.1, txt="", ln=True)

            row_count += 1
            #remove row from Dataframe after rendering pdf row
            resultsDF = resultsDF.drop(index=index)
        
        #save the pdf
        output_file = os.getcwd() + f"/app/static/label_pdf/label{label}.pdf"
        pdf.output(output_file)
   
        #print label creation confirmation
        print("New Label Created")


def createStringerLabel(packageID, resultsDF, orderNumber, orderID, SERVER_IP, SERVER_URL, printer):
    #Set Paths to Images
    logo = os.getcwd()+"/app/static/img/viewrailLogoBW.png"

    #Read "FPDF2" library documentation for more info
    #Set up PDF page (dimensions in inches)
    #Set label Size
    pdf = FPDF(unit='in', format=[7.4,2.25])
    #create a page
    pdf.add_page()
    #set margins
    pdf.set_margins(left=.05, top=.01, right=.1)
    pdf.set_auto_page_break(auto=False)
    
    #add images, resize, and postion
    pdf.image(logo, x=1.6, y=.2, w = 1)
    # #make new line
    
    pdf.set_line_width(.01)
    pdf.line(.15,.62,4,.62)
    #create Indents to postion text "Arial" "Bold" Font Size: 10 (add "border=True" argument to see cell borders)
    pdf.set_font('Arial', 'B', size=10)
    
    for index, post in resultsDF.iterrows():
        #Add a second line if description overflows first line
        stringer = ""
        nameString = str(resultsDF.at[index, "getProduct.name"])
        productID = str(resultsDF.at[index, "getProduct.id"])
        finishOption = str(resultsDF.at[index, "lineItemFinishes"])
        quantity = str(resultsDF.at[index,'packableItemsPivots'][0]["quantity"])
        part_title = "Stringer ID:"
        
        try:
            #Order pattern
            pattern = r"M\d+([A-Z]\d+)"
            match = re.search(pattern, nameString)
            if match:
                stringer = match.group()
                print(stringer)  # output: 01A5
            else:
                #Remake Order PAttern
                pattern = r"M\d+-\d+([A-Z]\d+)"
                match = re.search(pattern, nameString)
                if match:
                    stringer = match.group()
                    print(stringer)  # output: 01A5
        except:
            stringer = "None"
    
    if stringer == "":
        product_label = True
        stringer = str(resultsDF.at[index, "getProduct.id"])
        part_title = "Product ID:"
    else:
        product_label = False

        
        
    #Get PDF Link Files
    
    qr1_path, qr2_path, pdfLink_1, pdfLink_2 = getPDFLinks(resultsDF)
    if pdfLink_1 != "":
        download_file(pdfLink_1, "pdf_1.pdf")
        time.sleep(1)
        try:
            pdfLink_1 = highlight_text_in_pdf(f"{PDF_FOLDER}pdf_1.pdf", f"{PDF_FOLDER}pdf_1_HL.pdf", stringer)
        except:
            pass
    if pdfLink_2 != "":
        download_file(pdfLink_2, "pdf_2.pdf")

    if pdfLink_1 != "" and pdfLink_2 != "":
        
        merged_pdf_file = build_merged_pdfs([SERVER_URL+"pdf_1_HL.pdf", pdfLink_2], stringer, "stringer_QR", orderID)
        time.sleep(2)

        merged_pdf_url = get_terminal_file_url(packageID, stringer+"_Combined")
        print(merged_pdf_url)
        qr1_path = make_qr_code(merged_pdf_url)
        qr2_path = ""
    
    #draw QR Codes if file path exists
    if qr1_path != "":
        pdf.set_font('Arial', 'B', size=14)
        
        
        
        pdf.image(qr1_path, x=5.5, y=.3, w = 1.75)
        pdf.text(4.4, .6, txt='Scan For')
        pdf.text(4.5, .8, txt='Prints')
        
        #pdf.image("app\static\img\qr_scan_icon.png", x=4.4, y=.9, w = 1)
        pdf.image("app\static\img\phone.jpg", x=4.45, y=.9, w=.7)
        
        pdf.set_line_width(0.02)  # Set line width to 1
        pdf.rect(4.25, .25, 3.05, 1.8)  # Draw a rectangle at (50, 50) with width 100 and height 80
# Output the PDF
        pdf.set_font('Arial', size=8)
       
    # if qr2_path != "":
    #     pdf.set_font('Arial', 'B', size=10)
    #     pdf.image(qr2_path, x=5.9, y=.3, w = 1.5)
    #     pdf.text(6.15, .35, txt='Scan For Prints')
    #     pdf.set_font('Arial', size=8)
    #     pdf.text(x=6.3, y=1.85, txt="Stringer PDF")
    #write Order Number
    

    pdf.set_font('Arial', 'B', size=28)
    pdf.ln(.001)
   
    pdf.text(0.1, 1.3, txt=part_title)
    pdf.set_font('Arial', 'B', size=40)
    
    pdf.text(.1, 1.85, txt=stringer)

    if product_label:
        try:
            letter = LETTER_DICT[int(stringer)]
        except:
            letter = ""
        
        if letter != "":
            pdf.set_font('Arial', 'B', size=60)
            pdf.set_fill_color(0,-1,-1)
            pdf.set_text_color(255,-1,-1)
            
            cell_width = pdf.get_string_width(letter) + .2
            pdf.cell(.2,2, ln=True)
            pdf.cell(4.5,0.9, ln=False)
            pdf.cell(cell_width, 0.9, txt=letter, ln=1, fill=True, align="C", border=1)
            pdf.set_fill_color(50,-1,-1)
            pdf.set_text_color(0,-1,-1)
            pdf.set_font('Arial', 'B', size=40)
    #pdf.set_font('Arial', 'B', size=8)
    #pdf.cell(.05, .16, txt='Label' + str(label+1) + "/" + str(number_of_labels), ln=True)
    
    #Write Part Number
    

    #pdf.cell(.05, .25, txt='Posts in Gaylord: ' + postsInGaylord, ln=True)


    #Write Part Description
    #pdf.set_font('Arial',"B", size=10)
    #pdf.text(1.6, 1.85, txt="QTY " + quantity + " - " + productID + " - " + nameString)

    #pdf.set_font('Arial', 'B', size=18)
    #pdf.text(1.6,2.15, txt=finishOption)
    
    #pdf.set_font('Arial', 'B', size=7)
    #now = datetime.datetime.now()
    #pdf.text(6, 2.17, txt='Printed: ' + str(now.strftime("%m/%d/%Y %I:%M %p")))
        
    #remove row from Dataframe after rendering pdf row
    resultsDF = resultsDF.drop(index=index)
    
    #save the pdf
    output_file = os.getcwd() + f"/app/static/label_pdf/label.pdf"
    pdf.output(output_file)
    #printLabel_PDF(output_file, DYMO_PRINTER)
    
    url = f"http://{SERVER_IP}:5050/static/label_pdf/label.pdf"
    send_request_printall(url, printer, 1)
    #print label creation confirmation
    print("New Stringer QR Label Created")
    return True

def createHandrailLabel(resultsDF, SERVER_IP, SERVER_URL, printer):
    print(resultsDF.columns)
    #Set Paths to Images
    logo = os.getcwd()+"/app/static/img/viewrailLogoBW.png"

    #Read "FPDF2" library documentation for more info
    #Set up PDF page (dimensions in inches)
    #Set label Size
    pdf = FPDF(unit='in', format=[7.4,2.25])
    #create a page
    pdf.add_page()
    #set margins
    pdf.set_margins(left=.05, top=.01, right=.1)
    pdf.set_auto_page_break(auto=False)
    
    #add images, resize, and postion
    pdf.image(logo, x=1.6, y=.2, w = 1)
    # #make new line
    
    pdf.set_line_width(.01)
    pdf.line(.15,.62,4,.62)
    #create Indents to postion text "Arial" "Bold" Font Size: 10 (add "border=True" argument to see cell borders)
    pdf.set_font('Arial', 'B', size=10)
    
    for index, post in resultsDF.iterrows():
        #Add a second line if description overflows first line
        stringer = ""


        handrail_order_number = "Order:" 
        pdf.set_font('Arial', 'B', size=14)
        pdf.text(1.35, 0.95, txt=handrail_order_number)
        
        pdf.set_font('Arial', 'B', size=18)
        pdf.text(2.05, 0.95, txt=resultsDF.at[0,"order.order_number"])
        
        #handrail_title = "Handrail ID:" 
        #pdf.set_font('Arial', 'B', size=28)
        #pdf.text(0.1, 1.8, txt=handrail_title)
        
        pdf.set_font('Arial', 'B', size=64)
        #pdf.text(1.25, 1.8, txt=resultsDF.at[0,"piece_number"])

        pdf.set_xy(1.25, 1.4)  # Position of the text
        pdf.cell(1.8, .2, resultsDF.at[0,"piece_number"], align="C", border=False)

        url = resultsDF.at[0,"product.website_image_override_url"]
        profile_image_filename = download_file(url, "handrail_profile.jpg")
        pdf.image(profile_image_filename, x=5, y=.2, w = 1.8)


        
        profile_name = resultsDF.at[0,"lineItem.handrail_style"].replace("_", " ").title()
        pdf.set_font('Arial', size=12)
        #pdf.text(5.2, 2.1, txt=profile_name)
        pdf.set_xy(5.2, 2)  # Position of the text
        pdf.cell(1.5, .2, profile_name, align="C", border=False)

        #remove row from Dataframe after rendering pdf row
        resultsDF = resultsDF.drop(index=index)
        
        #save the pdf
        alphanumeric = generate_random_string(4) 
        output_file = os.getcwd() + f"/app/static/label_pdf/handrail_"+str(alphanumeric)+".pdf"
        
        pdf.output(output_file)
        #printLabel_PDF(output_file, DYMO_PRINTER)
        
        url = f"http://{SERVER_IP}:5050/static/label_pdf/handrail_"+str(alphanumeric)+".pdf"
        send_request_printall(url, printer, 1)
        #print label creation confirmation
        print("New Stringer QR Label Created")
    return True


def printPDFlabel(resultsDF, search_string, filename, SERVER_URL, printer):
    print(resultsDF)
    qr1_path= ""
    qr2_path= ""

    #Get the stinger ID
    
    nameString = str(resultsDF.at[0, "getProduct.name"])
    try:
        #Order pattern
        pattern = r"M\d+([A-Z]\d+)"
        match = re.search(pattern, nameString)
        if match:
            stringer = match.group()
            print(stringer)  # output: 01A5
        else:
            #Remake Order Pattern
            pattern = r"M\d+-\d+([A-Z]\d+)"
            match = re.search(pattern, nameString)
            if match:
                stringer = match.group()
                print(stringer)  # output: 01A5
    except:
        stringer = ""
    
    
    
    if os.path.exists(os.getcwd()+ f'\\app\\static\\download_temp_files\\{filename}'):
        pass
    else:
        found_pdfLink = ""
        #Try to find system blueprint
        numberOfPDFFiles = len(resultsDF.at[0,'lineItem.od1Files'])
        print(numberOfPDFFiles)
        try:
            
            for pdf in range(0,numberOfPDFFiles):
                try:
                    pdfLink = resultsDF.at[0,'lineItem.od1Files'][pdf]["url"]
                    
                    if search_string in pdfLink:
                        found_pdfLink = pdfLink
                        break
                except Exception as error:
                    print(error)
            pdf_local_path = download_file(found_pdfLink, filename)
        
        except Exception as error:
            print(error)

    url = SERVER_URL+filename
    print(url)
    send_request_printall(url, printer, 1)

    
def build_merged_pdfs(pdf_list, part_name, label_type, orderID):
    merged_path = f"{PDF_FOLDER}merged.pdf"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}
    writer = PdfWriter()
    for pdf in pdf_list:
        response = requests.get(url=pdf, headers=headers, timeout=120)
        mem_pdf = io.BytesIO(response.content)
        pdf_open = PdfReader(mem_pdf)
        writer.append_pages_from_reader(pdf_open)

    outputStream = open(merged_path,"wb")
    writer.write(outputStream)
    outputStream.close()

    pack_url = upload_file_to_Terminal(label_type, part_name, merged_path, orderID)

    return pack_url 


def split_string(string, n):
    """Split a string into chunks of length n, while keeping words together."""
    # Create a list to store the chunks
    chunks = []
    
    # Split the string into words
    words = string.split()
    
    # Initialize the current chunk
    current_chunk = ""
    
    # Loop over the words and add them to the current chunk
    for word in words:
        # If the current chunk plus the next word is longer than n,
        # append the current chunk to the list of chunks and start a new chunk
        if len(current_chunk + " " + word) > n:
            chunks.append(current_chunk.strip())
            current_chunk = word
        # Otherwise, add the word to the current chunk
        else:
            current_chunk += " " + word
    
    # Append the last chunk to the list of chunks
    chunks.append(current_chunk.strip())
    
    return chunks


def getPDFLinks(resultsDF):
    print(resultsDF)
    qr1_path= ""
    qr2_path= ""

    #Get the stinger ID
    
    nameString = str(resultsDF.at[0, "getProduct.name"])
    try:
        #Order pattern
        pattern = r"M\d+([A-Z]\d+)"
        match = re.search(pattern, nameString)
        if match:
            stringer = match.group()
            print(stringer)  # output: 01A5
        else:
            #Remake Order Pattern
            pattern = r"M\d+-\d+([A-Z]\d+)"
            match = re.search(pattern, nameString)
            if match:
                stringer = match.group()
                print(stringer)  # output: 01A5
    except:
        stringer = ""
    
    #Try to find system blueprint
    numberOfPDFFiles = len(resultsDF.at[0,'lineItem.od1Files'])
    print(resultsDF.at[0,'lineItem.od1Files'])
    print(numberOfPDFFiles)
    qr_path_1, qr_path_2 = "", ""
    pdfLink_1, pdfLink_2 = "", ""
    try:
        for pdf in range(0,numberOfPDFFiles):
            try:
                pdfLink_1 = resultsDF.at[0,'lineItem.od1Files'][pdf]["url"]
                if "CUSTOMER INSTALL" in pdfLink_1:
                    print("Flight System PDF Found: " + pdfLink_1)
                    qr1 = qrcode.make(pdfLink_1.replace(" ","%20"), error_correction=qrcode.constants.ERROR_CORRECT_L)
                    qr1.save(os.getcwd() + "/app/static/label_pdf/qr_code_pdf_1.png")
                    qr_path_1 = os.getcwd() + r"/app/static/label_pdf/qr_code_1.png"
                    break
            except Exception as error:
                print(error)
                qr_path_1 = ""
        #Try to find the stringer blueprint
        for pdf in range(0,numberOfPDFFiles):
            try:
                pdfLink_2 = resultsDF.at[0,'lineItem.od1Files'][pdf]["url"]
                print(pdfLink_2)
                if stringer in pdfLink_2 and "CUSTOMER INSTALL" not in pdfLink_2:
                    print("Stringer PDF Found: " + pdfLink_2)
                    qr2 = qrcode.make(pdfLink_2.replace(" ","%20"), error_correction=qrcode.constants.ERROR_CORRECT_L)
                    qr2.save(os.getcwd() + "/app/static/label_pdf/qr_code_pdf_2.png")
                    qr_path_2 = os.getcwd() + r"/app/static/label_pdf/qr_code_2.png"
                    break
            except Exception as error:
                print(error)
                qr_path_2 = ""
    except Exception as error:
        print(error)
        qr1_path= ""
        qr2_path= ""
    
    print(qr1_path, qr2_path)
    return qr_path_1, qr_path_2, pdfLink_1, pdfLink_2


def crop_pdf_image(image_path, left, top, right, bottom):
     # Open the image using PIL
    image = Image.open(image_path)

    # Crop the image using the specified coordinates
    cropped_image = image.crop((left, top, right, bottom))

    cropped_image.save(image_path)

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string