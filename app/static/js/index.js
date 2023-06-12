//Description: Javascript Frontend for the Order Scan Screen
//             for index.html
//             User scans in orders and creates all the labels for the products in the system.
//             Uses Socket messaging to communicate to the Flask backend (views.py)
//             


//global variables
var SocketIpList = ["127.0.0.1:5050"];

//get the IP list of all the HMI screens to allow Socket Messaging to be enabled
async function getSocketIpList() {

    result = await fetch("/getSocketIpList", { method: "GET", mode: "no-cors", });

    //iterrate through SocketIPList and add IP to list
    for (let i = 0; i < result.length; i++) {
        console.log(SocketIpList[i]);
        SocketIpList.add(result[i]);
    }
}

//list of IP addresses that can access the SocketIO messages, main and all HMI's
var socket = io.connect(SocketIpList);
var entry = {};
var label_number = 0;
var ordernumber = '';
var lightTimeout;

//When the page elements are done loading, do the following
document.addEventListener("DOMContentLoaded", function () {

    //Get printer settings JSON
    console.log(json_data);
    if (json_data != null){
        set_printer_settings_from_server(json_data)
    }
    //run the Socket IP list generator function
    //getSocketIpList();
    //showProgressBar(true,"update")
    //Always Autofocus the Order Number input box if a keystroke is pressed!
    document.addEventListener("keypress", function (e) {
        if (e.target.tagName !== "INPUT") {
            var input = document.getElementById("scan_label");
            //autofocus input, recover the first keypress, and the rest of the keypresses will fill in
            input.focus();
            input.value = e.key;
            e.preventDefault();
        }

    });
    var currentSelectedLabel = document.getElementById("selectOverride").innerHTML
    var standardLabelButton = document.getElementById("standardLabel")
    var stringerLabelButton = document.getElementById("stringerLabel")
    var metalHandrailLabelButton = document.getElementById("metalHandrailLabel")

    printer_name_list = [json_data.printer_1.name, json_data.printer_2.name, json_data.printer_3.name,]
    
    create_printer_dropdown("stringer_qr_label_printer_select", "packing")
    create_printer_dropdown("stringer_print_printer_select", "letter")
    create_printer_dropdown("manifest_label_printer_select", "packing")
    create_printer_dropdown("metal_handrail_printer_select", "packing")

    console.log(currentSelectedLabel)
    if (currentSelectedLabel == "stringer"){
        stringerLabelButton.checked = true
    }
    else if (currentSelectedLabel == "standard"){
        standardLabelButton.checked = true
    }
    else if (currentSelectedLabel == "metal_handrail"){
        metalHandrailLabelButton.checked = true
    }
   
    else {
        standardLabelButton.checked = true
    }

    scanInput = document.getElementById("submit_label")
    scanInput.onsubmit = function() {
        showProgressBar(true, "")
    


        rawScanData = document.getElementById("scan_label").value;

        standardLabelButton = document.getElementById("standardLabel")
        stringerLabelButton = document.getElementById("stringerLabel")
        metalHandrailLabelButton = document.getElementById("metalHandrailLabel")

        
        if (standardLabelButton.checked) {
            currentSelectedLabel = "manifest"
            printer_1_name = stringer_qr_label_printer_select.value
            printer_2_name = ""
            printer_3_name = ""
        }
        else if (stringerLabelButton.checked) {
            currentSelectedLabel = "stringer"
            printer_1_name = stringer_qr_label_printer_select.value
            printer_2_name = stringer_print_printer_select.value
            printer_3_name = ""
        }
        else if (metalHandrailLabelButton.checked) {
            currentSelectedLabel = "metal_handrail"
            printer_1_name = stringer_qr_label_printer_select.value
            printer_2_name = ""
            printer_3_name = ""
            
        }
        else{
            currentSelectedLabel = "manifest"
            printer_1_name = stringer_qr_label_printer_select.value
            printer_2_name = ""
            printer_3_name = ""
        }

        
        // printer_1_name = stringer_qr_label_printer_select.value
        // printer_2_name = stringer_print_printer_select.value
        // printer_3_name = ""
        selected_printers = [printer_1_name, printer_2_name, printer_3_name]
        socket.emit("scanLabel", rawScanData, currentSelectedLabel, selected_printers)
        return false

    }

    settingsButton = document.getElementById("settingsButton")
    settingsButton.onclick = function(){
        $('#settingsModal').modal('show')
    }

    modalSettingsCancel = document.getElementById("cancelSettingsModal")
    modalSettingsCancel.onclick = function(){
        $('#settingsModal').modal('hide')
    }

    socket.on("fromScanLabel", function (successBool, postJSON) {
        document.getElementById("scan_label").value = '';

        if (successBool == true) {
            showProgressBar(false, "success")

        }
        else if (successBool == false) {
            
            if (postJSON == "invalid") {
                showProgressBar(false, "invalid")
            }
            
            if (postJSON == "no_parts_found") {
                showProgressBar(false, "no_parts_found")
            }
        }
        else {
            showProgressBar(false, "invalid")
        }
        
    })
    
    
    
});




/////////////////////
// Async Functions //
/////////////////////


//Logic for controlling the loading bar
async function showProgressBar(action, alertMessage) {
    var loadingBar = document.getElementById('loading_bar')

    function success_sound() {
        var snd = new Audio("/static/wav/success.wav")
        snd.play();
    }

    function error_sound() {
        var snd = new Audio("/static/wav/error.wav")
        snd.play();
    }

    if (action == true) {

        loadingBar.classList.remove("bg-danger");
        loadingBar.classList.remove("bg-warning");
        loadingBar.classList.remove("bg-success");
        loadingBar.classList.remove("bg-info");
        loadingBar.classList.add("bg-primary");
        loadingBar.classList.remove('fade')
        loadingBar.innerHTML = "<h2 id=\"loading_bar_text\" class=\"m-3\">Searching Database...</h2>"

        if (alertMessage == 'update') {
            loadingBar.classList.remove("bg-danger");
            loadingBar.classList.remove("bg-warning");
            loadingBar.classList.remove("bg-success");
            loadingBar.classList.remove("bg-info");
            loadingBar.classList.add("bg-primary");
            loadingBar.innerHTML = "<h2 id=\"loading_bar_text\" class=\"m-3\">Loading...<h2/>"

        }
    }

    //Prepare to Hide the Loading bar
    if (action == false) {
        console.log(alertMessage)

        //Display success message
        if (alertMessage == 'success') {
            
            loadingBar.classList.remove("bg-primary");
            loadingBar.classList.remove("bg-warning");
            loadingBar.classList.remove("bg-danger");
            loadingBar.classList.remove("bg-info");
            loadingBar.classList.add("bg-success");
            loadingBar.innerHTML = "<h2 id=\"loading_bar_text\">Products Found</h2><h4>Creating Label(s)...</h4></h2>"

            setTimeout(function success() {
                loadingBar.classList.add('fade')
                loadingBar.classList.remove("bg-success");
                loadingBar.classList.add("bg-primary");
            }, 1500);
        }

        //If order number entered is an invalid order number
        else if (alertMessage == 'invalid') {
            

            loadingBar.classList.remove("bg-warning")
            loadingBar.classList.remove("bg-primary");
            loadingBar.classList.remove("bg-success");
            loadingBar.classList.remove("bg-info");
            loadingBar.classList.add("bg-danger");
            loadingBar.innerHTML = "<h2 id=\"loading_bar_text\" class=\"m-3\">Invalid Scan</h2>"

            setTimeout(function invalid() {
                loadingBar.classList.add('fade')
                loadingBar.classList.remove("bg-success");
                loadingBar.classList.add("bg-primary");
            }, 5000);
        }

        else if (alertMessage == 'no_parts_found') {
            

            loadingBar.classList.remove("bg-warning")
            loadingBar.classList.remove("bg-primary");
            loadingBar.classList.remove("bg-success");
            loadingBar.classList.remove("bg-info");
            loadingBar.classList.add("bg-danger");
            loadingBar.innerHTML = "<h2 id=\"loading_bar_text\" class=\"m-3\">No Parts Found In Package</h2>"
            
            setTimeout(function invalid() {
                loadingBar.classList.add('fade')
                loadingBar.classList.remove("bg-success");
                loadingBar.classList.add("bg-primary");
            }, 5000);
        }
    }
}


async function set_printer_settings_from_server(json_data){
    printer_1_name_input = document.getElementById("printer_1_name_input")
    printer_1_name_input.value = json_data.printer_1.name

    printer_1_type_input = document.getElementById("printer_1_type_input")
    printer_1_type_input.value = json_data.printer_1.type

    printer_2_name_input = document.getElementById("printer_2_name_input")
    printer_2_name_input.value = json_data.printer_2.name

    printer_2_type_input = document.getElementById("printer_2_type_input")
    printer_2_type_input.value = json_data.printer_2.type

    printer_3_name_input = document.getElementById("printer_3_name_input")
    printer_3_name_input.value = json_data.printer_3.name

    printer_3_type_input = document.getElementById("printer_3_type_input")
    printer_3_type_input.value = json_data.printer_3.type

    submitSettingsModalButton = document.getElementById("submitSettingsModal")
    submitSettingsModalButton.onclick = function(){
        // printer_1_name_input = document.getElementById("printer_1_name_input")
        // printer_1_type_input = document.getElementById("printer_1_type_input")
        // printer_2_name_input = document.getElementById("printer_2_name_input")
        // printer_2_type_input = document.getElementById("printer_2_type_input")
        // printer_3_name_input = document.getElementById("printer_3_name_input")
        // printer_3_type_input = document.getElementById("printer_3_type_input")
        
        update_json = {"printer_1": {name: printer_1_name_input.value, type: printer_1_type_input.value},
                    "printer_2": {name: printer_2_name_input.value, type: printer_2_type_input.value},
                    "printer_3": {name: printer_3_name_input.value, type: printer_3_type_input.value}
                    }
        socket.emit("updatePrintSettings", update_json)
        history.go(0)
                }
}


async function create_printer_dropdown(id, label_type){
    var stringerPrintPrinterSelect = document.getElementById(id)

    var option = document.createElement("option");
    option.text = "None"
    stringerPrintPrinterSelect.add(option);

    for (var i = 0; i < printer_name_list.length; i++) {
        var option = document.createElement("option");
        option.text = printer_name_list[i];
        if (json_data["printer_"+(i+1)].type == label_type){
            option.selected = true;
        }
        if (!Number.isNaN(printer_name_list[i])){
            stringerPrintPrinterSelect.add(option);
        }
    }
}
