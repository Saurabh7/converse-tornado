$(document).ready(function() {
	
$("#messageform").submit(function(event) {
		console.log("haha");
		var formdata = $('#messageform').formData();
		var button = $('#messageform').find("input[type=submit]");
		formdata._xsrf = getCookie("_xsrf");

		button.prop("disabled", true);
		$.ajax({
			url: "/new",
			type: 'POST',
			data: $.param(formdata),
			dataType:'json',
			success: function(response){
				messageBox.show(response);
				button.prop("disabled", false);
			}
				});
		$("#message").val("").select();
		event.preventDefault();
	});

messageBox.poll();

});

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
};


var messageBox = {
	poll: function() {
		var data = {"_xsrf": getCookie("_xsrf")};
		$.ajax({url: "/updates",
			type: "POST",
			data: data,
			success: messageBox.endPoll,
			error: messageBox.error
			})
	},

	show: function(message){
		var mid = $("#mi"+ message.id);
		if (mid.length>0) return;
		var content = $(message.html);
		content.hide()
		$("#inbox").append(content);
		content.slideDown();
	},

	endPoll: function(message){
		try {
			messageBox.show(message);
		} catch(error) {
			messageBox.error();
			return;
		}
		window.setTimeout(messageBox.poll, 0);
	},

	error: function(){
		window.setTimeout(messageBox.poll, 2500)	
	}

}

jQuery.fn.formData = function() {
    var fields = this.serializeArray();
    var json = {};
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    return json;
	};
