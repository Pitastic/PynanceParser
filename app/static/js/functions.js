"use strict";

// ----------------------------------------------------------------------------
// -- DOM Functions ----------------------------------------------------------
// ----------------------------------------------------------------------------


/**
 * Opens a popup to display details
 *
 * @param {string} id - The ID of the HTML element to display as a popup.
 */
function openPopup(id) {
    document.getElementById(id).style.display = 'block';
}

/**
 * Closes a popup by setting its display style to 'none'.
 *
 * @param {string} popupId - The ID of the popup element to be closed.
 */
function closePopup(popupId) {
	document.getElementById(popupId).style.display = 'none';
}


// ----------------------------------------------------------------------------
// -- AJAX Functions ----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Constructs a URI string or FormData object from a dictionary of key-value pairs.
 *
 * @param {Object} value_dict - An object containing key-value pairs to be converted into an URI or FormData.
 *                              Keys ending with "[]" are treated as arrays.
 * @param {FormData} [formData] - An optional FormData object to append the key-value pairs to
 * 								  instead of creating an URI string.
 * @returns {string|FormData} - Returns an URI string or FormData object.
 */
function concatURI(value_dict, formData){
	let uri = "";
	for (let key in value_dict) {
		if (value_dict.hasOwnProperty(key)) {
			if (typeof formData == 'undefined') {
				// URI
				if (key.endsWith("[]")){
					for (let i = 0; i < value_dict[key].length; i++) {
						const val = encodeURIComponent(value_dict[key][i]);
						uri += key + "=" + val + "&";
					}
				}else{
					const val = encodeURIComponent(value_dict[key]);
					uri += key + "=" + val + "&";
				}
			}else{
				// formData
				let value = value_dict[key];
				if (key == 'file') {
					const fileInput = document.getElementById(value);
					value = fileInput.files[0];
					key = value_dict[key];
				}
				formData.append(key, value);
			}
		}
	}
	uri = uri.substring(0, uri.length-1);
	return (typeof formData == 'undefined') ? uri : formData;
}

/**
 * Creates and returns a new XMLHttpRequest object
 * configured with a callback to handle its response.
 *
 * @param {function} callback - A callback function to handle the response.
 * 								Receives the response text and stsatus code as arguments.
 * @returns {XMLHttpRequest} - The newly created XMLHttpRequest object.
 */
function createAjax(callback) {
	const ajax = new XMLHttpRequest();
	ajax.onreadystatechange = function () {
		if (this.readyState == 4 && this.status >= 200 && this.status < 300) {
			callback(this.responseText);
		} else if (this.readyState != 4) {
			// pending
		} else {
			callback(this.responseText, this.status);
		}
	};
	return ajax;
}

/**
 * Sends a GET request to the specified API endpoint with the given parameters.
 *
 * @param {string} sub - The API endpoint to append to the base URL.
 * @param {Object} params - An object containing key-value pairs to be sent as query parameters.
 * @param {function} callback - A callback function to handle the response.
 * 								Receives the response text and stsatus code as arguments.
 * @param {string} [method="GET"] - The HTTP method to use for the request (e.g., "GET", "DELETE").
 */
function apiGet(sub, params, callback, method = "GET") {
	const ajax = createAjax(callback);
	const request_uri = concatURI(params);
	ajax.open(method, "/api/" + sub, true);
	ajax.send(request_uri);
}

/**
 * Sends data to the specified API endpoint with the given parameters.
 * The HTTP method will adapt to the presence of a file in the parameters.
 * If a file is present, it will use 'POST' else 'PUT'.
 *
 * @param {string} sub - The API endpoint to append to the base URL.
 * @param {Object} params - An object containing key-value pairs to be sent as query parameters.
 * @param {function} callback - A callback function to handle the response.
 * 								Receives the response text and stsatus code as arguments.
 * @param {boolean} [isFile=false] - A switch to enable special file upload handling.
 */
function apiSubmit(sub, params, callback, isFile = false) {
	const ajax = createAjax(callback);
	let method;
	let request_uri;

	if (isFile) {
		// Concat Uri
		method = "POST";
		const newForm = new FormData();
		request_uri = concatURI(params, newForm);

	} else {
		// Append JSON
		method = "PUT";
		request_uri = JSON.stringify(params);
	}
	
	ajax.open(method, "/api/" + sub, true);

	if (method != "POST") {
		ajax.setRequestHeader("Content-type", "application/json");
	}
	ajax.send(request_uri);
}