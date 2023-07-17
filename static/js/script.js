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
	// Get the content of the diary-content div
	var diaryContent = document.getElementById('diary-content').innerHTML;
	// Set the content as the value of the hidden input field
	document.getElementById('hidden-diary-content').value = diaryContent;
}


// start and end dates for 'plot.html'
const startDateInput = document.getElementById('start_date');
const endDateInput = document.getElementById('end_date');

const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

startDateInput.max = tomorrow.toISOString().split('T')[0];

startDateInput.addEventListener('change', function () {
    const selectedStartDate = new Date(this.value);
    // Enable end date input and set the minimum and maximum values
    endDateInput.disabled = false;
    endDateInput.min = this.value;
    endDateInput.max = tomorrow.toISOString().split('T')[0];
});
