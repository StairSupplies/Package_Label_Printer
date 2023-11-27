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

    setInterval(checkExpressInput, 1000)

    numpad.attach({
        target: "bev_hand_quantity_input",
        max: 3, // 3 DIGITS MAX
        decimal: false
    });


    //Get printer settings JSON
    console.log(json_data);
    if (json_data != null) {
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
    // var currentSelectedLabel = document.getElementById("selectOverride").innerHTML
    // var standardLabelButton = document.getElementById("standardLabel")
    // var stringerLabelButton = document.getElementById("stringerLabel")

    printer_name_list = [json_data.printer_1.name, json_data.printer_2.name, json_data.printer_3.name,]

    create_printer_dropdown("bev_hand_label_printer_select", "packing")


    express_post_label_btn = document.getElementById("bev_hand_label_btn")
    express_post_label_btn.onclick = function () {
        $('#bev_hand_Modal').modal('show')
    }


    settingsButton = document.getElementById("settingsButton")
    settingsButton.onclick = function () {
        $('#settingsModal').modal('show')
    }

    modalSettingsCancel = document.getElementById("cancelSettingsModal")
    modalSettingsCancel.onclick = function () {
        $('#settingsModal').modal('hide')
    }


    modalExpressPostCancel = document.getElementById("cancel_bev_hand_modal")
    modalExpressPostCancel.onclick = function () {
        $('#bev_hand_Modal').modal('hide')
    }


    // Beverage and Handrail button
    print_bev_hand_submit = document.getElementById("print_bev_hand_submit")
    print_bev_hand_submit.onclick = function () {
        var express_post_config = document.getElementById("bev_hand_config_input")
        var express_post_quantity = document.getElementById("bev_hand_quantity_input")
        var bulk_express_label_printer_select = document.getElementById("bev_hand_label_printer_select")

        var express_json = {
            "config": express_post_config.value,
            "quantity": express_post_quantity.value,
            "printer": bulk_express_label_printer_select.value,
        }


        socket.emit("printBevHandLabel", express_json)
        // bootstrapAlert("<h3 style='color: green'><h3>", "success")
        express_post_quantity.value = "1"
        print_express_post_submit.disabled = true
        $('#bev_hand_Modal').modal('hide')
        return false
    }


    socket.on("from_scan_submit", function (successBool, postJSON) {
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

    socket.on("fromPrintBevHandLabel", function (message, successBool) {

        if (successBool == true) {
            bootstrapAlert("<h3 style='color: green'>" + message + "<h3>", "success")
            success_sound()
        }
        else {
            bootstrapAlert("<h3 style='color: red'>" + message + "<h3>", "danger")
            error_sound()
        }

    });


})

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


async function set_printer_settings_from_server(json_data) {

    // Printer 1
    printer_1_name_input = document.getElementById("printer_1_name_input")
    printer_1_name_input.value = json_data.printer_1.name

    printer_1_type_input = document.getElementById("printer_1_type_input")
    printer_1_type_input.value = json_data.printer_1.type

    // Printer 2
    printer_2_name_input = document.getElementById("printer_2_name_input")
    printer_2_name_input.value = json_data.printer_2.name

    printer_2_type_input = document.getElementById("printer_2_type_input")
    printer_2_type_input.value = json_data.printer_2.type

    // Printer 3
    printer_3_name_input = document.getElementById("printer_3_name_input")
    printer_3_name_input.value = json_data.printer_3.name

    printer_3_type_input = document.getElementById("printer_3_type_input")
    printer_3_type_input.value = json_data.printer_3.type


    submitSettingsModalButton = document.getElementById("submitSettingsModal")
    submitSettingsModalButton.onclick = function () {
        // printer_1_name_input = document.getElementById("printer_1_name_input")
        // printer_1_type_input = document.getElementById("printer_1_type_input")
        // printer_2_name_input = document.getElementById("printer_2_name_input")
        // printer_2_type_input = document.getElementById("printer_2_type_input")
        // printer_3_name_input = document.getElementById("printer_3_name_input")
        // printer_3_type_input = document.getElementById("printer_3_type_input")

        update_json = {
            "printer_1": { name: printer_1_name_input.value, type: printer_1_type_input.value },
            "printer_2": { name: printer_2_name_input.value, type: printer_2_type_input.value },
            "printer_3": { name: printer_3_name_input.value, type: printer_3_type_input.value }
        }
        socket.emit("updatePrintSettings", update_json)
        setTimeout(function refreshTimeout() {
            history.go(0)
        }, 1000);
        
    }
}


async function create_printer_dropdown(id, label_type) {
    var stringerPrintPrinterSelect = document.getElementById(id)

    var option = document.createElement("option");
    option.text = "None"
    stringerPrintPrinterSelect.add(option);

    for (var i = 0; i < printer_name_list.length; i++) {
        var option = document.createElement("option");
        option.text = printer_name_list[i];
        if (json_data["printer_" + (i + 1)].type == label_type) {
            option.selected = true;
        }
        if (!Number.isNaN(printer_name_list[i])) {
            stringerPrintPrinterSelect.add(option);
        }
    }
}

async function checkBevHandInput() {
    var quantity = document.getElementById("bev_hand_quantity_input");
    var submitButton = document.getElementById("print_bev_hand_submit");

    // Check if quantity is valid
    // If not, disable submit
    submitButton.disabled = true;
    if (quantity.value === "" || (isNaN(quantity.value))) { // Pass
    }
    else if (quantity.value < 1) {  // Pass
    }
    else {
        submitButton.disabled = false;
    }
}

function bootstrapAlert(alertMessage, type) {
    $.bootstrapGrowl(alertMessage, {
        type: type,
        offset: { from: 'bottom', amount: 150 },
        align: 'center',
        delay: 5000,
        allow_dismiss: false,
        width: 'auto'
    });
}

function success_sound() {
    var snd = new Audio("/static/wav/success.wav")
    snd.play();
}

function error_sound() {
var snd = new Audio("/static/wav/error.wav")
snd.play();
}