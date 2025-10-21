"use strict";

document.addEventListener('DOMContentLoaded', function () {
    // Filter IBAN Button
    document.getElementById('apply-filter').addEventListener('click', () => {
        const query = getFilteredList();
        console.log(query);
        window.location.href = '/' + IBAN + '/stats' + query;
    })
    document.getElementById('reset-filter').addEventListener('click', () => {
        window.location.href = '/' + IBAN + '/stats';
    })
});