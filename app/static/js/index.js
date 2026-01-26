"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // Import Input (IBAN)
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    const fileDropArea = document.getElementById('file-drop-area');

    fileDropArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileLabel.textContent = fileInput.files.length + " Datei(en) ausgewählt";
        } else {
            fileLabel.textContent = '.csv,.pdf,.html';
        }
    });

    fileDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
    });

    fileDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileLabel.textContent = files.length + " Datei(en) ausgewählt";
        }
    });

    // Import Input (Settings)
    const settingsInput = document.getElementById('settings-input');
    const settingsLabel = document.getElementById('settings-label');
    const settingsDropArea = document.getElementById('settings-drop-area');

    settingsDropArea.addEventListener('click', () => {
        settingsInput.click();
    });

    settingsInput.addEventListener('change', () => {
        if (settingsInput.files.length > 0) {
            settingsLabel.textContent = settingsInput.files[0].name;
        } else {
            settingsLabel.textContent = '.json';
        }
    });

    settingsDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
    });

    settingsDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            settingsInput.files = files;
            settingsLabel.textContent = files[0].name;
        }
    });

    // Metadata-Select
    document.getElementById('read-setting').addEventListener('change', function () {
        document.getElementById('set-setting').value = "";
    });
});

// ----------------------------------------------------------------------------
// -- DOM Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Prepares and configures a modal dialog for adding or editing data based on the provided mode.
 * This function handles both "group" and "IBAN" modes, dynamically loading data and updating the modal's content.
 *
 * @param {string} modal_id - The ID of the modal element to be prepared.
 * @param {Event} event - The event object triggered by the user interaction.
 * @param {string} [force_id] - Optional parameter to force a specific mode or ID, overriding the event's dataset.
 *
 * @returns {void}
 */
function prepareAddModal(modal_id, event, force_id) {
    const mode = modal_id.split('-')[1];
    const text_input = document.getElementById(mode + "-input");
    const link_open = document.querySelector("#" + modal_id + " footer a");
    const iban_stats = document.getElementById('iban-stats');
    
    if (force_id || (event && event.currentTarget.dataset[mode])) {
        // Load and fill
        const id = force_id || event.currentTarget.dataset[mode];
        text_input.value = id;
        link_open.href = '/' + encodeURIComponent(id);
        link_open.classList.remove('hide');

        if (mode == "group") {
            // Get Group Info; Activate Checkboxes for Ibans in Group
            const iban_checkboxes = document.querySelectorAll("#" + modal_id + " fieldset input");
            apiGet("getMeta/" + id, {}, function (responseText, error) {
                const ibans = JSON.parse(responseText)['ibans'] || [];
                iban_checkboxes.forEach(box => {
                    if (ibans.includes(box.value)) {
                        // Activate IBAN as Groupmember
                        box.checked = true;
                    }
                });
            });

            return;
        }

        // Modal is Add-IBAN
        const stat_points = iban_stats.getElementsByTagName('b');
        apiGet('stats/' + id, {}, function (responseText, error) {
            // Get basic Stats
            if (error) {
                alert(error);
                return;
            }
            const r = JSON.parse(responseText);
            stat_points[0].innerHTML = r.count;
            stat_points[1].innerHTML = formatUnixToDate(r.min);
            stat_points[2].innerHTML = formatUnixToDate(r.max);
            iban_stats.classList.remove('hide');
        })

        return;
    }

    // Clean
    text_input.value = "";
    link_open.classList.add('hide');
    iban_stats.classList.add('hide');
}

/**
 * Gets a value for a Metadate into a textarea.
 * The key is selected via the select input element 'read-setting'
 * and written to 'set-setting'.
 */
function loadSetting() {
    const setting_uuid = document.getElementById('read-setting').value;
    const result_text = document.getElementById('set-setting');
    if (!setting_uuid) {
        alert('Kein Name einer Einstellung angegeben!');
        return;
    }

    apiGet('getMeta/' + setting_uuid, {}, function (responseText, error) {
        if (error) {
            showAjaxError(error, responseText);

        } else {
            result_text.value = formatResultText(responseText);

        }
    });
}

/**
 * Sets a value for a Metadate.
 * The key is selected via the select input element 'read-setting'
 * and the value is taken from 'set-setting'.
 */
function saveSetting() {
    const setting_uuid = document.getElementById('read-setting').value;
    const result_text = document.getElementById('set-setting');
    if (!setting_uuid || !result_text.value) {
        alert('Kein Name einer Einstellung oder Wert angegeben!');
        return;
    }

    let payload;
    let meta_type;
    try {
        payload = JSON.parse(result_text.value);
        if (!payload['metatype']) {
            throw new ValueError("No metatype provided!");
        }
        meta_type = payload['metatype'];

    } catch (error) {
        alert('Could not parse settingsvalue!' + error);
        return;
    }

    apiSubmit('saveMeta/' + meta_type, payload, function (responseText, error) {
        if (error) {
            showAjaxError(error, responseText);

        } else {
            alert('Einstellungen gespeichert' + responseText)
            result_text.value = '';

        }
    }, false);
}


// ----------------------------------------------------------------------------
// -- API Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Sends a file to the server for upload.
 * The file is selected via the file input element 'settings-input'.
 */
function importSettings() {
    const settings_type = document.getElementById('settings-type').value;

    const fileInput = document.getElementById('settings-input');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'settings-input' }; // The value of 'file' corresponds to the input element's ID
    apiSubmit('upload/metadata/' + settings_type, params, function (responseText, error) {
        if (error) {
            showAjaxError(error, responseText);

        } else {
            let success_msg = JSON.parse(responseText);
            alert('Es wurden ' + success_msg.inserted + ' Einträge aus der Datei importiert.');
            window.location.href = '/';

        }
    }, true);
}

/**
 * Sends transactions in a file or a batch of files to the server for upload.
 * The file is selected via the file input element 'file-input' (multiple)
 * but every entry is send step-by-step to get results per call directly.
 * Therefore this methods differ from the global `apiSubmit()` function.
 */
function uploadIban() {
    const iban = document.getElementById('iban-input').value;
    if (!iban) {
        alert("Keine IBAN angegeben!");
        return;
    }

    const bank_id = document.getElementById('bank-type').value
    const fileInput = document.getElementById('file-input');
    if (fileInput.files.length === 0) {
        alert('Es wurde keine Datei ausgewählt.');
        return;
    }

    // Prepare List entry for clone in loop
    const open_btn = document.querySelector('#upload-list footer a');
    open_btn.setAttribute('disabled', 'true');
    const list_table = document.querySelector('#upload-list table');
    list_table.innerHTML = "";
    const list_tr = document.createElement('tr');
    const cell1 = document.createElement('td');
    const cell2 = document.createElement('td');
    const span = document.createElement('span');
    span.setAttribute('aria-busy', "true");
    cell2.appendChild(span);
    list_tr.appendChild(cell1);
    list_tr.appendChild(cell2);

    //TODO: May need to create Promises per Loop
    for (let i = 0; i < fileInput.files.length; i++) {
        // DOM
        const tr = list_tr.cloneNode(true);
        const td2 = tr.querySelector('td:last-child');
        const td1 = tr.querySelector('td:first-child');
        let file_name = fileInput.files[i].name.slice(-30);
        if (fileInput.files[i].name.length > 30) {
            file_name = '...' + file_name;
        }
        td1.innerHTML = file_name + '<br><small>&nbsp;</small>';
        list_table.appendChild(tr);

        // Form
        const fileFormData = new FormData();
        fileFormData.append('bank', bank_id)
        fileFormData.append('file-batch', fileInput.files[i]);

        const ajax = createAjax(function (responseText, error) {

            // Update List of uploads with results per File
            let result = JSON.parse(responseText);
            if (error) {
                console.warn(fileInput.files[i].name, error, responseText);
                td2.setAttribute('aria-busy', 'false');
                td2.classList.add('error');
                td2.innerHTML = '&times;';
                result = result.error;

            } else {
                console.info(fileInput.files[i].name, responseText);
                td2.setAttribute('aria-busy', 'false');
                td2.innerHTML = '&#10004;';
                result = result.inserted + ' Transaktionen importiert';
        
            }
            td1.querySelector('small').innerHTML = result;

        });

        // Show Upload Modal
        document.querySelector('#add-iban header button').click();
        const upload_modal = document.getElementById('upload-list');
        openModal(upload_modal, { 'currentTarget': { 'dataset': {} }});

        // Send request(s)
    	ajax.open("POST", "/api/upload/" + iban, true);
	    ajax.send(fileFormData);

    }

    //TODO: Show an overall OK or confirm() for opening IBAN
    console.log("All AJAX Requests finished");
    open_btn.removeAttribute('disabled');
}

/**
 * Saves a group with the specified name and associated IBANs.
 * 
 * This function retrieves the group name from an input field and the selected IBANs
 * from checkboxes. It then sends the data to the server using the `apiSubmit` function.
 * If the operation is successful, the page is reloaded; otherwise, an error message is displayed.
 */
function saveGroup() {
    const groupname = document.getElementById("group-input").value;
    if (!groupname) {
        alert("Keine Gruppe angegeben!");
        return;
    }

    const checkboxes = document.querySelectorAll('input[name="iban-checkbox"]:checked');
    const selectedIbans = Array.from(checkboxes).map(checkbox => checkbox.value);
    const params = {'ibans': selectedIbans}

    apiSubmit('addgroup/' + groupname, params, function (responseText, error) {
        if (error) {
            showAjaxError(error, responseText);

        } else {
            alert('Gruppe gespeichert!');
            window.location.reload();

        }
    }, false);

    return selectedIbans;
}

/**
 * Deletes the database for the given IBAN or the Config for a Groupname
 */
function deleteDB(delete_group) {
    let collection;
    if (delete_group) {
        collection = document.getElementById('group-input').value;
    } else {
        collection = document.getElementById('iban-input').value;
    }
    
    if (!collection) {
        alert("Keine IBAN/Gruppe angegeben!");
        return;
    }

    apiGet('deleteDatabase/'+ collection, {}, function (responseText, error) {
        if (error) {
            showAjaxError(error, responseText);

        } else {
            let success_msg = JSON.parse(responseText);
            alert(success_msg.deleted + ' IBAN(s) / Gruppe(n) gelöscht');
            window.location.reload();

        }
    }, 'DELETE');
    
}
