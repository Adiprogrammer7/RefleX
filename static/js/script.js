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