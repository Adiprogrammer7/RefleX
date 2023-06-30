// to set time for flashed messages in 'layout.html'
var flash_div = document.getElementById("flash_div");
if (flash_div) {
	setTimeout(function () {
		flash_div.style.display = "none";
	}, 10000); // Hide the div after 10 seconds
}

// for 'text_editor.html'
function toggleFormatting(command, value = null) {
	document.execCommand(command, false, value);
	var button = document.getElementById(command + 'Btn');
	button.classList.toggle('active-button', document.queryCommandState(command));
}
function addLink() {
	const url = prompt('Insert url: ');
	toggleFormatting('createLink', url);
}
function save_diary() {
	var title = document.querySelector('.title-input').value;
	var tag = document.querySelector('.tag-input').value;
	var content = document.getElementById('diary-content').innerHTML;

	console.log("Diary Title:", title);
	console.log("Diary Tag:", tag);
	console.log("Diary Content:", content);
}
