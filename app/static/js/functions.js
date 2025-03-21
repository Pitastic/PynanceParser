"use strict";

// ----------------------------------------------------------------------------
// -- AJAX Functions ----------------------------------------------------------
// ----------------------------------------------------------------------------

function concatURI(value_dict, formData){
	/**
	 * Constructs a URI string or FormData object from a dictionary of key-value pairs.
	 *
	 * @param {Object} value_dict - An object containing key-value pairs to be converted into an URI or FormData.
	 *                              Keys ending with "[]" are treated as arrays.
	 * @param {FormData} [formData] - An optional FormData object to append the key-value pairs to
	 * 								  instead of creating an URI string.
	 * @returns {string|FormData} - Returns an URI string or FormData object.
	 */
	var uri = "";
	for (var key in value_dict) {
		if (value_dict.hasOwnProperty(key)) {
			if (typeof formData == 'undefined') {
				// URI
				if (key.endsWith("[]")){
					for (var i = 0; i < value_dict[key].length; i++) {
						var val = encodeURIComponent(value_dict[key][i]);
						uri += key + "=" + val + "&";
					}
				}else{
					var val = encodeURIComponent(value_dict[key]);
					uri += key + "=" + val + "&";
				}
			}else{
				// formData
				var value = value_dict[key];
				if (key == 'file') {
					var fileInput = document.getElementById(value);
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

function createAjax(callback) {
	/**
	 * Creates and returns a new XMLHttpRequest object
	 * configured with a callback to handle its response.
	 *
	 * @param {function} callback - A callback function to handle the response.
	 * 								Receives the response text and stsatus code as arguments.
	 * @returns {XMLHttpRequest} - The newly created XMLHttpRequest object.
	 */
	var ajax = new XMLHttpRequest();
	ajax.onreadystatechange = function () {
		if (this.readyState == 4 && this.status >= 200 && this.status < 300) {
			callback(this.responseText);
		} else if (this.readyState != 4) {
			// pending
		} else {
			callback(this.responseText, this.status);
		}
	};
	return ajax
}

function apiGet(sub, params, callback) {
	/**
	 * Sends a GET request to the specified API endpoint with the given parameters.
	 *
	 * @param {string} sub - The API endpoint to append to the base URL.
	 * @param {Object} params - An object containing key-value pairs to be sent as query parameters.
	 * @param {function} callback - A callback function to handle the response.
	 * 								Receives the response text and stsatus code as arguments.
	 */
	var ajax = createAjax(callback);
	var request_uri = concatURI(params);
	ajax.open("GET", "/api/" + sub, true);
	ajax.send(request_uri);
}

function apiPost(sub, params, callback, isFile){
	/**
	 * Sends a POST request to the specified API endpoint with the given parameters.
	 *
	 * @param {string} sub - The API endpoint to append to the base URL.
	 * @param {Object} params - An object containing key-value pairs to be sent as query parameters.
	 * @param {function} callback - A callback function to handle the response.
	 * 								Receives the response text and stsatus code as arguments.
	 * @param {boolean} isFile - A switch to enable special file upload handling.
	 */
	var ajax = createAjax(callback);
	ajax.open("POST", "/api/"+sub, true);
	if (!isFile) {
		// Concat Uri
		var request_uri = concatURI(params);
		ajax.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	}else{
		// Append Form
		var newForm = new FormData();
		var request_uri = concatURI(params, newForm);
	}
	ajax.send(request_uri);
}