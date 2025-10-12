"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // PopUps
    document.getElementById('add-iban-btn').addEventListener('click', function () {
        openPopup('add-iban');
    });
    document.getElementById('add-group-btn').addEventListener('click', function () {
        openPopup('add-group');
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

});

// ----------------------------------------------------------------------------
// -- DOM Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------



// ----------------------------------------------------------------------------
// -- API Functions -----------------------------------------------------------
// ----------------------------------------------------------------------------

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
