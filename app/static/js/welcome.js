"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // PopUps
    document.getElementById('add-button').addEventListener('click', function () {
        openPopup('add-popup');
    });

    // Import Input
    const dropArea = document.getElementById('file-drop-area');
    const fileInput = document.getElementById('file-input');

    dropArea.addEventListener('click', () => fileInput.click());

    dropArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropArea.style.borderColor = '#000';
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.style.borderColor = '#ccc';
    });

    dropArea.addEventListener('drop', (event) => {
        event.preventDefault();
        dropArea.style.borderColor = '#ccc';
        fileInput.files = event.dataTransfer.files;
    });

});