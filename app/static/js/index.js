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
    const box = document.getElementById('result-text');
    box.innerHTML = result;
}


/**
 * Sends a file to the server for upload.
 * The file is selected via the file input element 'input_file'.
 */
function uploadFile() {
    const iban = document.getElementById('input_iban').value;
    const fileInput = document.getElementById('input_file');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'input_file' }; // The key 'file' corresponds to the input element's ID
    apiSubmit('upload/' + iban, params, function (responseText, error) {
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
    const iban = document.getElementById('input_iban').value;

    apiGet(iban + '/truncateDatabase', {}, function (responseText, error) {
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
    const iban = document.getElementById('input_iban').value;
    const rule_name = document.getElementById('input_tagging_name').value;
    const rules = {
        'rule_name': rule_name
    }

    apiSubmit(iban + '/tag', rules, function (responseText, error) {
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
    const primary_tag = document.getElementById('input_manual_primary').value;
    const secondary_tag = document.getElementById('input_manual_secondary').value;
    const iban = document.getElementById('input_iban').value;

    const checkboxes = document.querySelectorAll('input[name="entry-select[]"]');
    const t_ids = [];    
    checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
            t_ids.push(checkbox.value);
        }
    });

    if (!iban) {
        alert('Please provide an IBAN.');
        return;
    }
    if (!t_ids) {
        alert('Please provide a Transaction ID (checkbox).');
        return;
    }

    let tags = {
        'primary_tag': primary_tag,
        'secondary_tag': secondary_tag
    }
    
    let api_function;
    if (t_ids.length == 1) {
        api_function = iban+'/setManualTag/'+t_ids[0];
    } else {
        api_function = iban+'/setManualTags';
        tags['t_ids'] = t_ids;
    };

    apiSubmit(api_function, tags, function (responseText, error) {
        if (error) {
            printResult('Tagging failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tagged successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


/**
 * Fetches information based on the provided UUID and IBAN input value.
 *
 * @param {string} uuid - The unique identifier used to fetch specific information.
 * 
 * This function retrieves the info for a given uuid from the server.
 */
function getInfo(uuid) {
    const iban = document.getElementById('input_iban').value;

    apiGet('/'+iban+'/'+uuid, {}, function (responseText, error) {
        if (error) {
            printResult('getTx failed: ' + '(' + error + ')' + responseText);

        } else {
            alert(responseText);

        }
    });
}


function saveMeta() {
    const meta_type = document.getElementById('select_meta').value;
    const fileInput = document.getElementById('input_file');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'input_file' }; // The key 'file' corresponds to the input element's ID
    apiSubmit('upload/metadata/'+meta_type, params, function (responseText, error) {
        if (error) {
            printResult('Rule saving failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Rule saved successfully!' + responseText);

        }
    }, true);
}
