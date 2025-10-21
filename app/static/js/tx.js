"use strict";

document.addEventListener('DOMContentLoaded', function () {

    const inputField = document.getElementById("tag-input");

    inputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            addTagBullet(inputField, "tag-container");
        }
    });

    inputField.addEventListener("blur", () => {
        addTagBullet(inputField, "tag-container");
    });

});

/**
 * Clear Tags from selected transactions
 * @param {string} uuid - The unique identifier associated with the request.
 */
function removeTags(uuid) {

    apiSubmit('removeTag/'+IBAN+'/'+uuid, {}, function (responseText, error) {
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
 * @param {string} uuid - The unique identifier associated with the request.
 */
function removeCats(uuid) {
    apiSubmit('removeCat/'+IBAN+'/' + uuid, {}, function (responseText, error) {
        if (error) {
            alert('Cat removal failed: ' + '(' + error + ')' + responseText);

        } else {
            alert('Entries category deleted successfully!' + responseText);
            window.location.reload();

        }
    }, false);
}

/**
 * Tags this one entrie in the database in a direct manner
 * @param {string} uuid - The unique identifier associated with the request.
 */
function manualTagTx(uuid) {
    // Replace Tag Liste
    return manualTag([uuid], TAGS, true);
}

/**
* Categorize this one entrie in the database in a direct manner
 * @param {string} uuid - The unique identifier associated with the request.
 */
function manualCatTx(uuid) {
    return manualCat([uuid], document.getElementById('cat-input').value);
}