"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // Upload Button Listener
    //document.getElementById('uploadButton').addEventListener('click', uploadFile);

});


/**
 * Shows a given Result in the Result-Box.
 *
 * @param {string} result - The text to be shwon.
 */
function printResult(result){
    var box = document.getElementById('result-text');
    box.innerHTML = result;
}


/**
 * Sends a file to the server for upload.
 * The file is selected via the file input element 'input_file'.
 */
function uploadFile() {
    const fileInput = document.getElementById('input_file');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'input_file' }; // The key 'file' corresponds to the input element's ID
    apiSubmit('upload', params, function (responseText, error) {
        if (error) {
            printResult('File upload failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('File uploaded successfully!' + responseText);
            window.location.reload();

        }
    }, true);
}


/**
 * Truncates the database.
 * An optional IBAN to truncate is selected by input with ID 'iban'.
 */
function truncateDB() {
    var iban = document.getElementById('input_iban').value;

    apiGet('truncateDatabase/'+iban, {}, function (responseText, error) {
        if (error) {
            printResult('Truncate failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Database truncated successfully!' + responseText);
            window.location.reload();

        }
    }, 'DELETE');
    
}


/**
 * Tags the entries in the database.
 * Optional Tagging commands are read from the input with ID
 * 'input_tagging_name' (more in the Future)
 */
function tagEntries() {
    // TODO: Implement more, complex tagging rules
    var rule_name = document.getElementById('input_tagging_name').value;
    var rules = {
        'rule_name': rule_name
    }

    apiSubmit('tag', rules, function (responseText, error) {
        if (error) {
            printResult('Tagging failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tagged successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


/**
 * Tags the entries in the database in a direct manner (assign Categories, no rules)
 * Optional Tagging commands are read from the inputs with IDs
 * 'input_manual_primary' , 'input_manual_secondary' , 'input_iban' and 'input_tid'.
 * While the IBAN and Transaction_ID are mandatory, the other inputs are optional.
 */
function manualTagEntries() {
    var primary_tag = document.getElementById('input_manual_primary').value;
    var secondary_tag = document.getElementById('input_manual_secondary').value;
    var iban = document.getElementById('input_iban').value;
    var t_id = document.getElementById('input_t_id').value;

    if (!iban || !t_id) {
        alert('Please provide an IBAN.');
        return;
    }

    var tags = {
        'primary_tag': primary_tag,
        'secondary_tag': secondary_tag
    }
    apiSubmit('setManualTag/'+iban+'/'+t_id, tags, function (responseText, error) {
        if (error) {
            printResult('Tagging failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tagged successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


function getInfo(uuid) {
    var iban = document.getElementById('input_iban').value;

    apiGet('getTx/'+iban+'/'+uuid, {}, function (responseText, error) {
        if (error) {
            printResult('getTx failed: ' + '(' + error + ')' + responseText);

        } else {
            alert(responseText);

        }
    });
}
