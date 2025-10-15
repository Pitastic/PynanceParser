"use strict";

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