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
