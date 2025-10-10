"use strict";

let rowCheckboxes = null;

document.addEventListener('DOMContentLoaded', function () {

    // PopUps
    document.getElementById('settings-button').addEventListener('click', function () {
        openPopup('settings-popup');
    });

    // Additional JavaScript for enabling/disabling the edit button based on checkbox selection
    const selectAllCheckbox = document.getElementById('select-all');
    rowCheckboxes = document.querySelectorAll('.row-checkbox');

    selectAllCheckbox.addEventListener('change', function () {
        rowCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        });
        updateEditButtonState();
    });

    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
        if (!this.checked) {
            selectAllCheckbox.checked = false;
        } else if (Array.from(rowCheckboxes).every(cb => cb.checked)) {
            selectAllCheckbox.checked = true;
        }
        updateEditButtonState();
        });
    });

});

// ----------------------------------------------------------------------------
// -- DOM Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Opens a popup to display details for a specific element and optionally fetches transaction details.
 *
 * @param {string} id - The ID of the HTML element to display as a popup.
 * @param {string|null} [tx_hash=null] - Optional transaction hash to fetch additional details for.
 */
function openDetailsPopup(id, tx_hash = null) {
	if (tx_hash) {
		// Use AJAX to fetch and populate details for the transaction with the given ID
		console.log(`Fetching details for transaction hash: ${tx_hash}`);
        const currentURI = window.location.pathname;
        const iban = currentURI.split('/').pop();
        resetDetails();
        getInfo(iban, tx_hash, fillTxDetails);
        openPopup(id);

	} else {
        openPopup(id);
		
	}
}


/**
 * Clears information from a result Box
*
*/
function resetDetails() {
    const box = document.getElementById('result-text');
    box.innerHTML = "";
}


/**
 * Shows a given Result in the Result-Box.
 *
 * @param {string} result - The text to be shwon.
 */
function fillTxDetails(result){
    const box = document.getElementById('result-text');
    box.innerHTML = result;
}

/**
 * Updates the state of the "Edit Selected" button based on the checkbox selections.
 * 
 * This function checks if any row checkboxes are selected and enables or disables
 * the "Edit Selected" button accordingly. It also updates the button's title to
 * reflect the number of selected checkboxes.
 * 
 * Assumes that `rowCheckboxes` is a collection of checkbox elements and that
 * there is a button with the ID `edit-selected` in the DOM.
 */
function updateEditButtonState() {
	const anyChecked = Array.from(rowCheckboxes).some(cb => cb.checked);
	const editButton = document.getElementById('edit-selected');
	editButton.disabled = !anyChecked;
	editButton.title = anyChecked
	? `Edit selected (${Array.from(rowCheckboxes).filter(cb => cb.checked).length} selected)`
	: 'Edit selected (0 selected)';
}


/**
 * Truncates the database.
 * An optional IBAN to truncate is selected by input with ID 'iban'.
 */
function truncateDB() {
    const iban = document.getElementById('input_iban').value;

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
    const iban = document.getElementById('input_iban').value;
    const rule_name = document.getElementById('tagging_name').value;
    let rules = {}
    if (rule_name) {
        rules['rule_name'] = rule_name
    }

    apiSubmit('tag/'+iban, rules, function (responseText, error) {
        if (error) {
            printResult('Tagging failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tagged successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


function removeTags() {
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

    let api_function;
    let tags = {};
    if (t_ids.length == 1) {
        api_function = 'removeTag/'+iban+'/'+t_ids[0];
    } else {
        api_function = 'removeTags/'+iban;
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
 * Tags the entries in the database in a direct manner (assign Categories, no rules)
 * Optional Tagging commands are read from the inputs with IDs
 * 'input_manual_category' , 'input_manual_tags' , 'input_iban' and 'input_tid'.
 * While the IBAN and Transaction_ID are mandatory, the other inputs are optional.
 */
function manualTagEntries() {
    const category = document.getElementById('input_manual_category').value;
    let tags = document.getElementById('input_manual_tags').value;
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

    let tagging = {
        'category': category,
        'tags': tags
    }
    
    let api_function;
    if (t_ids.length == 1) {
        api_function = 'setManualTag/'+iban+'/'+t_ids[0];
    } else {
        api_function = 'setManualTags/'+iban;
        tagging['t_ids'] = t_ids;
    };

    apiSubmit(api_function, tagging, function (responseText, error) {
        if (error) {
            printResult('Tagging failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tagged successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


/**
 * Fetches information based on the provided IBAN and UUID, and processes the response.
 *
 * @param {string} iban - The International Bank Account Number (IBAN) to identify the account.
 * @param {string} uuid - The unique identifier associated with the request.
 * @param {Function} [callback=alert] - A callback function to handle the response text. Defaults to `alert`.
 */
function getInfo(iban, uuid, callback = alert) {
    apiGet('/'+iban+'/'+uuid, {}, function (responseText, error) {
        if (error) {
            printResult('getTx failed: ' + '(' + error + ')' + responseText);

        } else {
            callback(responseText);

        }
    });
}


function saveMeta() {
    const meta_type = document.getElementById('select_meta').value;
    const fileInput = document.getElementById('input-json');
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
