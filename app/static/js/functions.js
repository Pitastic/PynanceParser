"use strict";

let IBAN = window.location.pathname.split('/')[1];
let TAGS = [];

// ----------------------------------------------------------------------------
// -- DOM Functions ----------------------------------------------------------
// ----------------------------------------------------------------------------

/**
 * Converts a Unix timestamp (in seconds) to a formatted date string.
 *
 * @param {number} unixSeconds - The Unix timestamp in seconds.
 * @returns {string} - The formatted date string in the format "%Y.%m.%d".
 */
function formatUnixToDate(unixSeconds) {
	if (!unixSeconds) {
		return "";
	}
	const date = new Date(unixSeconds * 1000); // Convert seconds to milliseconds
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
	const day = String(date.getDate()).padStart(2, '0');
	return `${day}.${month}.${year}`;
}

/**
 * Redirect to a GET URL using all defined Filters
 * 
 * @returns {string} - Returns one GET query args string for all filter inputs
 */
function getFilteredList() {
	let query_args = '';
	let arg_concat = '?';

	const startDate = document.getElementById('filter-range-start').value;
	if (startDate) {
		query_args = query_args + arg_concat + 'startDate=' + startDate;
		arg_concat = '&';
	}

	const endDate = document.getElementById('filter-range-end').value;
	if (endDate) {
		query_args = query_args + arg_concat + 'endDate=' + endDate;
		arg_concat = '&';
	}

	const text_search = document.getElementById('filter-text').value;
	if (text_search) {
		query_args = query_args + arg_concat + 'text=' + text_search;
		arg_concat = '&';
	}

	const peer = document.getElementById('filter-peer').value;
	if (peer) {
		query_args = query_args + arg_concat + 'pper=' + peer;
		arg_concat = '&';
	}

	const category = document.getElementById('filter-cat').value;
	if (category) {
		query_args = query_args + arg_concat + 'category=' + category;
		arg_concat = '&';
	}

	const tags = document.getElementById('filter-tag-result').value;
	if (tags) {
		query_args = query_args + arg_concat + 'tags=' + tags;
		arg_concat = '&';
		const tag_mode = document.getElementById('filter-tag-mode').value;
		if (tag_mode) {
			query_args = query_args + arg_concat + 'tag_mode=' + tag_mode;
			arg_concat = '&';
		}
	}

	let betrag_min = document.getElementById('filter-betrag-min').value;
	if (betrag_min) {
		betrag_min = betrag_min.replace(',', '.');
		query_args = query_args + arg_concat + 'betrag_min=' + betrag_min;
		arg_concat = '&';
	}

	let betrag_max = document.getElementById('filter-betrag-max').value;
	if (betrag_max) {
		betrag_max = betrag_max.replace(',', '.');
		query_args = query_args + arg_concat + 'betrag_max=' + betrag_max;
		arg_concat = '&';
	}

	return query_args;
}

/**
 * Dynamic Bullet list
 * Takes text-input to create new Tag-Bullets
 * 
 * @param {DOMElement} inputField for tag content input
 * 
 * @param {string} tagContainerId Id to select the container with tag-chips
 * 
 * @param {string} hiddenInputId (optional) Target id to push new values to instead of global var TAGS
 * 
 * @param {string} tagvalue (optional) Provide a Tag-Value insted of looking at text-input
 * 
 */
function addTagBullet(inputField, tagContainerId, hiddenInputId, tagvalue) {
	const tagConatiner = document.getElementById(tagContainerId);
	const value = tagvalue || inputField.value.trim();
	if (hiddenInputId) {
		// Select Elemnt to read and write from Tags
		var hiddenInput = document.getElementById(hiddenInputId);
		TAGS = hiddenInput.value.split(',').filter(t => t != "");
	}
	if (value && !TAGS.includes(value)) {
		TAGS.push(value);

		const tagEl = document.createElement("span");
		tagEl.className = "tag-chip " + generateClass(value);
		tagEl.textContent = value;
		tagEl.title = value;

		const removeBtn = document.createElement("a");
		removeBtn.className = "remove";
		removeBtn.innerHTML = "&times;";
		removeBtn.href = "javascript:void(0)";

		if (hiddenInputId) {
			// Care about the Input and pass it to the removal method
			hiddenInput.value = TAGS;
			removeBtn.addEventListener("click", () => removeTagBullet(tagEl, hiddenInputId));

		} else {
			removeBtn.addEventListener("click", () => removeTagBullet(tagEl));
		}

		tagEl.appendChild(removeBtn);
		tagConatiner.appendChild(tagEl);

		inputField.value = "";
	}
}

/**
 * Dynamic Bullet list
 * Deletes a dynamic Tag-Bullet from the global variable and the DOM
 * 
 * @param {DOMElement} element The Tagelement to remove
 * 
 * @param {string} hiddenInputId (optional) Target id to push new values to instead of global var TAGS
 */
function removeTagBullet(element, hiddenInputId) {
	TAGS = TAGS.filter(t => t !== element.firstChild.textContent);
	element.remove();

	if (hiddenInputId) {
		const hiddenInput = document.getElementById(hiddenInputId);
		hiddenInput.value = TAGS;
	}

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
function concatURI(value_dict, formData) {
	let uri = "";
	for (let key in value_dict) {
		if (value_dict.hasOwnProperty(key)) {
			if (typeof formData == 'undefined') {
				// URI
				if (key.endsWith("[]")) {
					for (let i = 0; i < value_dict[key].length; i++) {
						const val = encodeURIComponent(value_dict[key][i]);
						uri += key + "=" + val + "&";
					}
				} else {
					const val = encodeURIComponent(value_dict[key]);
					uri += key + "=" + val + "&";
				}
			} else {
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
	uri = uri.substring(0, uri.length - 1);
	return (typeof formData == 'undefined') ? uri : formData;
}

/**
 * Creates and returns a new XMLHttpRequest object
 * configured with a callback to handle its response.
 *
 * @param {function} callback - A callback function to handle the response.
 * 								Receives the response text and status code as arguments.
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

/**
 * Tags the entries in the database in a direct manner
 * A single or multiple transactions to tag could be provided
 *
 * @param {list} t_ids Liste von Transaktions IDs.
 * 					Wenn leer werden alle Transaktionen der IBAN berücksichtigt.
 * @param {list} tags	Liste mit zu setzenden Tags.
 * 						Wenn leer, werden alle Tags der Transaktion entfernt.
 * @param {boolean} overwrite Switch für das hinzufügen von Tags (append statt replace)
 */
function manualTag(t_ids, tags, overwrite) {
	if (typeof (t_ids) != "object" || typeof (tags) != "object") {
		alert("Falscher Typ von Transaktionsliste oder Tag-Liste !: " + typeof (t_ids) + " und " + typeof (tags));
		return;
	}

	let tagging = {
		'tags': tags
	}

	if (overwrite) {
		tagging['overwrite'] = true;
	}

	let api_function;
	if (t_ids.length == 1) {
		api_function = 'setManualTag/' + IBAN + '/' + t_ids[0];
	} else {
		api_function = 'setManualTags/' + IBAN;
		tagging['t_ids'] = t_ids;
	};

	apiSubmit(api_function, tagging, function (responseText, error) {
		if (error) {
			alert('Tagging fehlgeschlagen: ' + '(' + error + ')');

		} else {
			const success_msg = JSON.parse(responseText);
			const counts = success_msg.updated != 1 ? success_msg.updated + ' Einträge' : success_msg.updated + ' Eintrag';
			alert(counts + ' getaggt');
			window.location.reload();

		}
	}, false);
}

/**
 * Tags the entries in the database in a direct manner
 * A single or multiple transactions to tag could be provided
 *
 * @param {list} t_ids Liste von Transaktions IDs.
 * 					Wenn leer werden alle Transaktionen der IBAN berücksichtigt.
 * @param {string} cat	Name der zu setzenden Kategorie.
 * 						Wenn leer, wird die Kategorie entfernt.
 */
function manualCat(t_ids, cat) {
	if (typeof (t_ids) != "object" || typeof (cat) != "string") {
		alert("Falscher Typ von Transaktionsliste oder Tag-Liste !");
		return;
	}

	let payload = {
		'category': cat
	}

	let api_function;

	if (!cat) {
		// Delete Category		
		if (t_ids.length == 1) {
			api_function = 'removeCat/' + IBAN + '/' + t_ids[0];

		} else {
			api_function = 'removeCats/' + IBAN;
			payload['t_ids'] = t_ids;

		};

	} else {
		// Set Category		
		if (t_ids.length == 1) {
			api_function = 'setManualCat/' + IBAN + '/' + t_ids[0];

		} else {
			api_function = 'setManualCats/' + IBAN;
			payload['t_ids'] = t_ids;

		};

	}

	apiSubmit(api_function, payload, function (responseText, error) {
		if (error) {
			alert('Tagging failed: ' + '(' + error + ')' + responseText);

		} else {
			const success_msg = JSON.parse(responseText);
			const counts = success_msg.updated != 1 ? success_msg.updated + ' Einträge' : success_msg.updated + ' Eintrag';
			alert(counts + ' kategorisiert');
			window.location.reload();

		}
	}, false);
}


/* Formats an Error Responses from an AJAX Call
*
* @param {number} error_code The HTTP status code from the AJAX call
* @param {string} responseText The response text from the AJAX call
*
*/
function showAjaxError(error_code, responseText) {
	const error_msg = JSON.parse(responseText).error || "unbekannter Fehler";
	alert('Fehler ' + error_code + ': ' + error_msg);
}

/* Formats a Result from an AJAX Call (JSON as Text)
*
* @param {string} responseText The response text from the AJAX call
*
*/
function formatResultText(responseText) {
	return JSON.stringify(JSON.parse(responseText), null, 4);
}


/**
 * Generates a CSS class name based on the hash of the input string.
 * The resulting class name is in the format `gen-color-<number>`, where the number
 * is the absolute value of the hash modulo 1000, ensuring a short and unique class name.
 *
 * @param {string} inputString - The input string to generate the class name from.
 * @returns {string} - The generated class name.
 */
function generateClass(inputString) {
	if (! inputString) {
		return "";
	}
	let hash = 0;
	for (let i = 0; i < inputString.length; i++) {
		hash = (hash << 5) - hash + inputString.charCodeAt(i);
		hash |= 0; // Convert to 32bit integer
	}
	const className = `gen-color-${Math.abs(hash % 13)}`;
	return className;
}
