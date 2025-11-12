"use strict";

document.addEventListener('DOMContentLoaded', function () {

    // Tag Chip Bullets
    const inputTagContainers = [
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
        const query = getFilteredList();
        window.location.href = '/' + IBAN + '/stats' + query;
    })
    document.getElementById('reset-filter').addEventListener('click', () => {
        window.location.href = '/' + IBAN + '/stats';
    })
});