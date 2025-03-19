"use strict";

// ----------------------------------------------------------------------------
// -- AJAX Functions ----------------------------------------------------------
// ----------------------------------------------------------------------------

function concatURI(value_dict, formData){
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

function apiAction(params, callback, isFile){
	// Create Request
	var ajax = new XMLHttpRequest();

	// -- Handle Response
	ajax.onreadystatechange = function () {
		if (this.readyState == 4 && this.status >= 200 && this.status < 300) {
			callback(this.responseText);
		} else if (this.readyState != 4) {
			// pending
		} else {
			callback(this.responseText, this.status);
		}
	};

	// -- Send
	ajax.open("POST", "/action", true);
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