"use strict";

let rowCheckboxes = null;

document.addEventListener('DOMContentLoaded', function () {

    // enabling/disabling the edit button based on checkbox selection
    const selectAllCheckbox = document.getElementById('select-all');
    rowCheckboxes = document.querySelectorAll('.row-checkbox');

    selectAllCheckbox.addEventListener('change', function () {
        rowCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        });
        updateEditButtonState();
        listTxElements();
    });

    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
        if (!this.checked) {
            selectAllCheckbox.checked = false;
        } else if (Array.from(rowCheckboxes).every(cb => cb.checked)) {
            selectAllCheckbox.checked = true;
        }
        updateEditButtonState();
        listTxElements();
        });
    });

    // Tag Chip Bullets
    const inputField = document.getElementById("add-tag");

    inputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            addTagBullet(inputField, "tag-container");
        }
    });

    inputField.addEventListener("blur", () => {
        addTagBullet(inputField, "tag-container");
    });

    // Filter IBAN Button
    document.getElementById('apply-filter').addEventListener('click', () => {
        const startDate = document.getElementById('daterange-start').value;
        const endDate = document.getElementById('daterange-end').value;
        window.location.href = '/' + IBAN + '?startDate=' + startDate + '&endDate=' + endDate;
    })

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
		console.log('Fetching details for transaction hash: ' + tx_hash);
        resetDetails();
        getInfo(tx_hash, fillTxDetails);
        openPopup(id);

    } else {
        if (['cat-popup', 'tag-popup'].includes(id)) {
            document.getElementById('custom-tag').value = "";
            document.getElementById('custom-cat').value = "";
        }
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
	? `Edit (${Array.from(rowCheckboxes).filter(cb => cb.checked).length} selected)`
	: 'Edit (nichts ausgewählt)';
}

function listTxElements() {
    // Reset TAGS / Cats
    TAGS = [];
    const tag_chips = document.querySelectorAll('#tag-container > .tag-chip')
    for (let index = 0; index < tag_chips.length; index++) {
        tag_chips[index].remove();
    }
    document.getElementById('add-tag').value = "";
    document.getElementById('add-cat').value = "";

    // Clean and rewrite TX List
    const result_list = document.getElementById('tx-select-list');
    result_list.innerHTML = '';
    rowCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            const li = document.createElement('li');
            li.textContent = checkbox.dataset.txdate;
            const a = document.createElement('a');
            a.textContent = "(" + checkbox.dataset.txuuid + ")";
            a.href = "/" + IBAN + "/" + checkbox.dataset.txuuid;
            a.target = "_blank";
            li.appendChild(a);
            result_list.appendChild(li);
        }
    });
}

/**
 * Tag or Cat the entries in the database.
 * Optional rule_name input and custom json rule are read
 * from input elements with corresponding IDs
 * 
 * @param {string} operation    One of [tag, cat]. Switch for the type of operation
 */
function tagAndCat(operation) {
    let payload = {};
    const rule_name = document.getElementById(operation + '-select').value;
    let api_url = operation + '/';

    if (rule_name) {
        // Named or Custom Rule
        payload['rule_name'] = rule_name;
    }

    if (rule_name == "ui_selected_custom") {
        // Read Custom Rule from Textinput
        let rule_json = document.getElementById('custom-' + operation).value;
        payload['rule'] = JSON.parse(rule_json);
        if (!payload.rule.name || !payload.rule.metatype) {
            alert("Kein Namen oder kein Metatype bei der Custom-Regel angegeben");
            return;
        }

        api_url = 'tag-and-cat/';
    }

    const dry_run = document.getElementById(operation + '-dry').checked;
    if (dry_run) {
        payload['dry_run'] = dry_run;
    }

    apiSubmit(api_url + IBAN, payload, function (responseText, error) {
        if (error) {
            alert(operation + ' failed: ' + '(' + error + ')' + responseText);

        } else {
            alert(operation + ' successful!' + responseText);
            if (dry_run) {
                // List UUIDs which would have been tagged/cat
                const r = JSON.parse(responseText)
                let txt_list = ""
                r.entries.forEach(element => {
                    txt_list += "\n- " + element
                });
                alert("Folgende UUIDs würden geändert werden:\n" + txt_list);

            } else {
                // Tagged/Cat -> Reload
                window.location.reload();
            }

        }
    }, false);
}

/**
 * Clear Tags from selected transactions
 */
function removeTags() {
    const t_ids = Array.from(rowCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('name'));

    let api_function;
    let tags = {};
    if (t_ids.length == 1) {
        api_function = 'removeTag/'+IBAN+'/'+t_ids[0];
    } else {
        api_function = 'removeTags/'+IBAN;
        tags['t_ids'] = t_ids;
    };

    apiSubmit(api_function, tags, function (responseText, error) {
        if (error) {
            alert('Tag removal failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries tags deleted successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


/**
 * Clear Category from selected transactions
 */
function removeCats() {
    const t_ids = Array.from(rowCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('name'));

    let api_function;
    let payload = {};
    if (t_ids.length == 1) {
        api_function = 'removeCat/'+IBAN+'/'+t_ids[0];
    } else {
        api_function = 'removeCats/'+IBAN;
        payload['t_ids'] = t_ids;
    };

    apiSubmit(api_function, payload, function (responseText, error) {
        if (error) {
            alert('Cat removal failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries category deleted successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}


/**
 * Add one or more Tags to a Transaction withput overwriting existing ones.
 * Tags will be loaded from the global TAGS variable. Transaktion will
 * be taken from rowCheckboxes.
 */
function addTag() {
    const t_ids = Array.from(rowCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('name'));
    return manualTag(t_ids, TAGS, false);
}

/**
 * Set a categorie for a set of Transactions.
 * Transaction will be taken from rowCheckboxes.
 */
function addCat() {
    const t_ids = Array.from(rowCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('name'));
    const cat = document.getElementById('add-cat').value;
    return manualCat(t_ids, cat);
}

/**
 * Fetches information based on the provided IBAN and UUID, and processes the response.
 *
 * @param {string} uuid - The unique identifier associated with the request.
 * @param {Function} [callback=alert] - A callback function to handle the response text. Defaults to `alert`.
 */
function getInfo(uuid, callback = alert) {
    apiGet('/' + IBAN + '/' + uuid, {}, function (responseText, error) {
        if (error) {
            alert('getTx failed: ' + '(' + error + ')' + responseText);

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
            alert('Rule saving failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Rule saved successfully!' + responseText);

        }
    }, true);
}
