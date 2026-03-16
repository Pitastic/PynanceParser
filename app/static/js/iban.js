"use strict";

const selectAllCheckbox = document.getElementById('select-all');
let ROW_CHECKBOXES = null;
let PAGE = 1;

document.addEventListener('DOMContentLoaded', function () {

    // enabling/disabling the edit button based on checkbox selection
    ROW_CHECKBOXES = document.querySelectorAll('.row-checkbox');
    selectAllCheckbox.addEventListener('change', set_all_checkboxes);
    ROW_CHECKBOXES.forEach(checkbox => set_row_checkboxes(checkbox));

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

    // Update Details Link ("_blank" for non-PWA)
    updateDetailsLink();

});

// ----------------------------------------------------------------------------
// -- DOM Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Set all checkboxes to the state of the headerbox
 */
function set_all_checkboxes() {
    ROW_CHECKBOXES.forEach(checkbox => {
        checkbox.checked = this.checked;
    });
    updateEditButtonState();
    listTxElements();
}

/**
 * Set "more" button to target "_blank" if not PWA
 */
function updateDetailsLink() {
    var a = document.querySelector('#details-popup footer a.secondary');
    if (!a) return;
    if (sessionStorage.getItem('pwa_installed') == 'true') {
        a.removeAttribute('target');
    } else {
        a.setAttribute('target', '_blank');
    }
}

/**
 * Set an eventlistener for every box and change the header when unselected
 * 
 * @param {DOMElement} checkbox 
 */
function set_row_checkboxes(checkbox){
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
}

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
    const selector = "#dynamic-results td.";
    for (const key in result) {
        if (result.hasOwnProperty(key)) {
            const value = result[key];
            let td = document.querySelector(selector + key);
            if (!td) {
                continue;
            }

            if (key == 'date_tx' || key == "valuta") {
                // Dateformat
                td.innerHTML = formatUnixToDate(result[key]);

            } else if ((key == 'category' || key == "tags") && result[key]) {
                // Tag Chips
                const row = Array.isArray(result[key]) ? result[key] : [result[key]];
                for (let index = 0; index < row.length; index++) {
                    const a_link = document.createElement('a');
                    a_link.innerHTML = row[index];
                    a_link.href = "?tags=" + row[index];
                    a_link.className = 'tag-chip ' + generateClass(row[index]);
                    if (key == 'category') {
                        a_link.className += ' category';
                    }
                    a_link.dataset.tooltip = "Add Filter";
                    td.appendChild(a_link);
                }

            } else if (key == 'amount') {
                // Round
                td.innerHTML = result[key].toFixed(2);

            } else if (key == 'peer') {
                // Add Filter link
                const a_link = document.createElement('a');
                a_link.innerHTML = result[key];
                a_link.className = "secondary";
                a_link.href = "?peer=" + result[key];
                a_link.dataset.tooltip = "Add Filter";
                td.appendChild(a_link);

            } else {
                td.innerHTML = result[key];

            }
        }
    }

    const tx_link = document.querySelector('#details-popup footer a');
    tx_link.href = '/' + IBAN + '/' + result['uuid'];
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
 * Show the final summary PopUp after Tagging or Categorization.
 * 
 * @param {string} operation Switch for the type of operation. One of [tag, cat]
 * @param {string} response parsed JSON from the response
 * @param {string} error Error Message
 */
function showFinalPop(response, error) {
	const popup = document.getElementById('response-popup');
    
    //Überschrift ändern "...erfolgreich"
    const heading = popup.querySelector('header h2')
    heading.textContent = heading.textContent.split(' ')[0] + " erfolgreich";
    
    //Loading Spinner entfernen
    heading.setAttribute('aria-busy', 'false');
}

/**
 * Show PopUp and start to fill results
 * 
 * @param {Object} response Parsed JSON from response with partial results
 */
function showPartsPop(op, response){
    if (response.error){
        errorPopUp(
            op[0].toUpperCase() + op.substring(1) + " fehlgeschlagen",
            response.error, response.raw
        )
        return;
    }

    const rule_list = document.getElementById('result-rule-entries');
    let rule_line = rule_list.querySelector('details[name="' + response.rule + '"]');
    let ul; let update_count;
    
    if (!rule_line) {
        // Create new Rule Line
        rule_line = document.createElement('details');
        rule_line.setAttribute('name', response.rule);
        
        const summary = document.createElement('summary');
        summary.innerHTML = response.rule;
        
        update_count = document.createElement('span');
        update_count.className = "updated-count";
        summary.appendChild(update_count);
        
        ul = document.createElement('ul');
        
        rule_line.appendChild(summary);
        rule_line.appendChild(ul);
        rule_list.appendChild(rule_line);
    }
    
    // Add information about the current rule
    const number_updated = op == 'tag' ? response.tagged : response.categorized;
    ul = rule_line.querySelector('ul');
    update_count = rule_line.querySelector('summary .updated-count');
    update_count.innerHTML = "(" + number_updated + "/" + response.matched + ")";
    
    if (!response.entries.length) {
        return;
    }
    const li = document.createElement('li');
    const entry = response.entries[response.entries.length - 1];

    const a = document.createElement('a');
    a.href = '/' + IBAN + '/' + entry;
    a.innerHTML = entry;

    // Use '_blank' when not in PWA
    if (sessionStorage.getItem('pwa_installed') != 'true'){
        a.target = '_blank';
    }

    li.appendChild(a);
    ul.appendChild(li);
}


/**
 * Tag or Cat the entries in the database.
 * Optional rule_name input and custom json rule are read
 * from input elements with corresponding IDs
 * 
 * @param {string} operation    One of [tag, cat]. Switch for the type of operation
 */
function tagAndCat(operation) {
    let payload = {'streaming': true};
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

    // Open Result PopUp (fill with parts later)
    const heading = operation == 'tag' ? 'Tagging' : 'Kategorisierung';

    const paragraph1 = document.createElement('p');
    paragraph1.innerHTML = "Die folgenden Regeln haben Einträge geupdated bzw. selektiert:";

    const paragraph2 = document.createElement('p');
    paragraph2.id = 'result-rule-entries';

    responsePopUp(
        heading + ' läuft ...',
        [paragraph1, paragraph2],
        true
    );

    // Start Request
    if (payload.streaming) {
        // Single / Multiple Rules
        apiSubmitStreaming(api_url + IBAN, payload, function(response, error) {
            showPartsPop(operation, response);
        }, showFinalPop);

    } else {
        // Custom / Single Rule (Feed parts manually)
        apiSubmit(api_url + IBAN, payload, function(response, error) {
            const entries = response.entries || [];
            let responsePart = response;
            for (let index = 0; index < entries.length; index++) {
                responsePart.entries = [entries[index]];
                showPartsPop(operation, responsePart);
            }
            showFinalPop(response, error);
        }, false);

    }
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
            errorPopUp('Tag entfernen fehlgeschlagen', error, responseText);

        } else {
            const p = document.createElement('p');
            p.innerHTML = 'Die Tags der ausgewählten Einträge wurden erfolgreich entfernt.';
            responsePopUp('Tags entfernt', [p]);

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
            errorPopUp('Kategorie entfernen fehlgeschlagen', error, responseText);

        } else {
            const p = document.createElement('p');
            p.innerHTML = 'Die Kategorie der ausgewählten Einträge wurden erfolgreich entfernt.';
            responsePopUp('Kategorie entfernt', [p]);

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
            errorPopUp('Transaktionsabruf fehlgeschlagen', error, responseText);

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

        // enabling/disabling the edit button based on checkbox selection
        const selectAllCheckbox = document.getElementById('select-all');
        ROW_CHECKBOXES = document.querySelectorAll('.row-checkbox');
        selectAllCheckbox.addEventListener('change', set_all_checkboxes);
        ROW_CHECKBOXES.forEach(checkbox => set_row_checkboxes(checkbox));
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
