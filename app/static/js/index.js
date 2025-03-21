"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // Upload Button Listener
    document.getElementById('uploadButton').addEventListener('click', uploadFile);

});


function uploadFile() {
    /**
     * Sends a file to the server for upload.
     */
    const fileInput = document.getElementById('tx_file');
    if (fileInput.files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const params = { file: 'tx_file' }; // The key 'file' corresponds to the input element's ID
    apiPost('upload', params, function (responseText, error) {
        if (error) {
            alert('File upload failed: ' + '(' + error + ')' + responseText);
        } else {
            alert('File uploaded successfully!' + responseText);
            window.location.reload();
        }
    }, true);
}
