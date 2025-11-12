"use strict";

let ROW_CHECKBOXES = null;
let PAGE = 1;

document.addEventListener('DOMContentLoaded', function () {

    // enabling/disabling the edit button based on checkbox selection
    const selectAllCheckbox = document.getElementById('select-all');
    ROW_CHECKBOXES = document.querySelectorAll('.row-checkbox');

    selectAllCheckbox.addEventListener('change', function () {
        ROW_CHECKBOXES.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        });
        updateEditButtonState();
        listTxElements();
    });

    ROW_CHECKBOXES.forEach(checkbox => {
        checkbox.checked = false;
        checkbox.addEventListener('change', function () {
        if (!this.checked) {
            selectAllCheckbox.checked = false;
        } else if (Array.from(ROW_CHECKBOXES).every(cb => cb.checked)) {
            selectAllCheckbox.checked = true;
        }
        updateEditButtonState();
        listTxElements();
        });
    });

    // Tag Chip Bullets
    const inputTagContainers = [
        [document.getElementById("add-tag"), "add-tag-container"],
        [document.getElementById("filter-tag"), "filter-tag-container", "filter-tag-result"]
    ];

    for (let index = 0; index < inputTagContainers.length; index++) {
        const inputTag = inputTagContainers[index][0];
        const tagContainer = inputTagContainers[index][1];
        const hiddenInput = inputTagContainers[index][2] || null;
    
        inputTag.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                addTagBullet(inputTag, tagContainer, hiddenInput);
            }
        });
    
        inputTag.addEventListener("blur", () => {
            addTagBullet(inputTag, tagContainer, hiddenInput);
        });
        
    }

    // Filter IBAN Button
    document.getElementById('apply-filter').addEventListener('click', () => {
        window.location.href = '/' + IBAN + getFilteredList();
    })
    document.getElementById('reset-filter').addEventListener('click', () => {
        window.location.href = '/' + IBAN;
    })

});

// ----------------------------------------------------------------------------
// -- DOM Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Clears information from a result Box
*
*/
function resetDetails() {
    const all_td = document.querySelectorAll('#dynamic-results td');
    all_td.forEach(td => {
        td.innerHTML = "";
    });
}


/**
 * Shows a given Result in the Result-Box.
 *
 * @param {string} result - The text to be shwon as JSON string.
 */
function fillTxDetails(result) {
    const r = JSON.parse(result);
    const selector = "#dynamic-results td.";
    for (const key in r) {
        if (r.hasOwnProperty(key)) {
            const value = r[key];
            let td = document.querySelector(selector + key);
            if (!td) {
                continue;
            }

            if (key == 'date_tx' || key == "valuta") {
                // Dateformat
                td.innerHTML = formatUnixToDate(r[key]);

            } else if ((key == 'category' || key == "tags") && r[key]) {
                // Tag Chips
                const row = Array.isArray(r[key]) ? r[key] : [r[key]];
                for (let index = 0; index < row.length; index++) {
                    const span = document.createElement('span');
                    span.innerHTML = row[index];
                    span.className = 'tag-chip ' + key;
                    td.appendChild(span)
                }

            } else {
                td.innerHTML = r[key];

            }
        }
    }

    const tx_link = document.querySelector('#details-popup footer a');
    tx_link.href = '/' + IBAN + '/' + r['uuid'];
}

/**
 * Updates the state of the "Edit Selected" button based on the checkbox selections.
 * 
 * This function checks if any row checkboxes are selected and enables or disables
 * the "Edit Selected" button accordingly. It also updates the button's title to
 * reflect the number of selected checkboxes.
 * 
 * Assumes that `ROW_CHECKBOXES` is a collection of checkbox elements and that
 * there is a button with the ID `edit-selected` in the DOM.
 */
function updateEditButtonState() {
	const anyChecked = Array.from(ROW_CHECKBOXES).some(cb => cb.checked);
    const editButton = document.getElementById('edit-selected');
    const badge = editButton.parentNode.querySelector('.badge');
    editButton.disabled = !anyChecked;
    if (anyChecked) {
        const selectedCount = Array.from(ROW_CHECKBOXES).filter(cb => cb.checked).length;
        editButton.className = "primary";
        editButton.classList.remove('hide');
        badge.innerHTML = selectedCount;
    } else {
        editButton.className = "secondary outline";
        editButton.classList.add('hide');
        badge.innerHTML = "0";
    }
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
    ROW_CHECKBOXES.forEach(checkbox => {
        if (checkbox.checked) {
            const li = document.createElement('li');
            li.textContent = formatUnixToDate(checkbox.dataset.txdate) + " ";
            const a = document.createElement('a');
            a.textContent = "(" + checkbox.dataset.txuuid.substring(0, 8) + ")";
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
    const t_ids = Array.from(ROW_CHECKBOXES)
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
    const t_ids = Array.from(ROW_CHECKBOXES)
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
 * be taken from ROW_CHECKBOXES.
 */
function addTag() {
    const t_ids = Array.from(ROW_CHECKBOXES)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('name'));
    return manualTag(t_ids, TAGS, false);
}

/**
 * Set a categorie for a set of Transactions.
 * Transaction will be taken from ROW_CHECKBOXES.
 */
function addCat() {
    const t_ids = Array.from(ROW_CHECKBOXES)
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


function loadMore() {
    // Increment global
    PAGE += 1;
    // Get Page Content with a custom ajax call
    const ajax = createAjax(function (responseText, error) {
        if (error) {
            // No more Pages could be loaded
            document.querySelector('.transactions + footer a').classList.add('hide');
            return;
        }

        // Append new Rows
        document.querySelector('.transactions tbody').innerHTML += responseText;
    });

    // Call URI
    let get_args = '';
    const page_args = concatURI({ 'page': PAGE });

    // -- Add Filter args if any
    const additional_filters = getFilteredList();
    if (additional_filters) {
        get_args = additional_filters + '&' + page_args;

    } else {
        get_args = '?' + page_args;

    }

    ajax.open('GET', "/" + IBAN + get_args, true);
	ajax.send();
}
