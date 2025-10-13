"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // PopUps
    document.getElementById('add-iban-btn').addEventListener('click', function () {
        openPopup('add-iban');
    });
    document.getElementById('add-group-btn').addEventListener('click', function () {
        openPopup('add-group');
    });
    document.getElementById('settings-button').addEventListener('click', function () {
        openPopup('settings-popup');
    });

    // Import Input
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    const fileDropArea = document.getElementById('file-drop-area');

    fileDropArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileLabel.textContent = fileInput.files[0].name;
        } else {
            fileLabel.textContent = 'Datei hier ablegen oder auswählen (PDF / CSV / HTML)';
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
            fileLabel.textContent = files[0].name;
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
            alert('Settings not loaded: ' + '(' + error + ')' + responseText);

        } else {
            result_text.value = responseText;

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
            alert('Settings not saved: ' + '(' + error + ')' + responseText);

        } else {
            alert('Settings saved: ' + responseText)
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
function uploadFile() {
    const settings_type = document.getElementById('settings-type').value;

    const fileInput = document.getElementById('settings-input');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'file-input' }; // The value of 'file' corresponds to the input element's ID
    apiSubmit('upload/metadata/' + settings_type, params, function (responseText, error) {
        if (error) {
            alert('File upload failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('File uploaded successfully!' + responseText);
            window.location.href = '/' + settings_type;

        }
    }, true);
}

/**
 * Sends a file to the server for upload.
 * The file is selected via the file input element 'file-input'.
 */
function uploadFile() {
    const iban = document.getElementById('iban-input').value;
    if (!iban) {
        alert("Keine IBAN angegeben!");
        return;
    }

    const fileInput = document.getElementById('file-input');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'file-input' }; // The value of 'file' corresponds to the input element's ID
    apiSubmit('upload/' + iban, params, function (responseText, error) {
        if (error) {
            alert('File upload failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('File uploaded successfully!' + responseText);
            window.location.href = '/' + iban;

        }
    }, true);
}

/**
 * Saves a group with the specified name and associated IBANs.
 * 
 * This function retrieves the group name from an input field and the selected IBANs
 * from checkboxes. It then sends the data to the server using the `apiSubmit` function.
 * If the operation is successful, the page is reloaded; otherwise, an error message is displayed.
 */
function saveGroup() {
    const groupname = document.getElementById("groupname-input").value;
    if (!groupname) {
        alert("Keine Gruppe angegeben!");
        return;
    }

    const checkboxes = document.querySelectorAll('input[name="iban-checkbox"]:checked');
    const selectedIbans = Array.from(checkboxes).map(checkbox => checkbox.value);
    const params = {'ibans': selectedIbans}

    apiSubmit('addgroup/' + groupname, params, function (responseText, error) {
        if (error) {
            alert('Gruppe nicht angelegt: ' + '(' + error + ')' + responseText);

        } else {
            alert('Gruppe gespeichert!' + responseText);
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
        collection = document.getElementById('groupname-input').value;
    } else {
        collection = document.getElementById('iban-input').value;
    }
    
    if (!collection) {
        alert("Keine IBAN/Gruppe angegeben!");
        return;
    }

    apiGet('deleteDatabase/'+ collection, {}, function (responseText, error) {
        if (error) {
            printResult('Delete failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('DB deleted successfully!' + responseText);
            window.location.reload();

        }
    }, 'DELETE');
    
}
