
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

var url = '/search-meeting'; 
var url = '/search-by-date'; // Example URL for searching by date
var url = '/search-by-title'; // Example URL for searching by title

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");
var pauseButton = document.getElementById("pauseButton");
var nameInput = document.getElementById("name"); // Add reference to the name input field

// Initially disable the record button
recordButton.disabled = true;

// Add an event listener to the name input field to enable/disable the record button based on its value
nameInput.addEventListener("input", function () {
	if (nameInput.value.trim() !== "") {
		recordButton.disabled = false;
	} else {
		recordButton.disabled = true;
	}
});

// Add an event listener to the record button to check if the name is provided before starting recording
recordButton.addEventListener("touchstart", function () {
	if (nameInput.value.trim() === "") {
		alert("Please enter the name of the meeting.");
		return; // Prevent further execution
	}

	startRecording();
});

recordButton.addEventListener("mouseover", function () {
	if (nameInput.value.trim() === "") {
		alert("Please enter the name of the meeting.");
		return; // Prevent further execution
	}

	startRecording();
});

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);
pauseButton.addEventListener("click", pauseRecording);

function startRecording() {
	document.getElementById('recordButton').classList.add('recording-indicator');
	console.log("recordButton clicked");
	var constraints = { audio: true, video: false }

	recordButton.disabled = true;
	stopButton.disabled = false;
	pauseButton.disabled = false

	navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		audioContext = new AudioContext();

		//update the format 
		document.getElementById("formats")

		/*  assign to gumStream for later use  */
		gumStream = stream;

		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)

		*/
		rec = new Recorder(input, { numChannels: 1 })

		//start the recording process
		rec.record()

		console.log("Recording started");

	}).catch(function (err) {
		//enable the record button if getUserMedia() fails
		recordButton.disabled = false;
		stopButton.disabled = true;
		pauseButton.disabled = true
	});
}

function pauseRecording() {
	console.log("pauseButton clicked rec.recording=", rec.recording);
	if (rec.recording) {
		//pause
		rec.stop();
		pauseButton.innerHTML = "Resume";
	} else {
		//resume
		rec.record()
		pauseButton.innerHTML = "Pause";

	}
}

function stopRecording() {
	document.getElementById('recordButton').classList.remove('recording-indicator');
	console.log("stopButton clicked");

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	pauseButton.disabled = true;

	//reset button just in case the recording is stopped while paused
	pauseButton.innerHTML = "Pause";

	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(uploadRecording);
	rec.exportWAV(createDownloadLink);

}

function uploadRecording(blob) {
    var progress = document.getElementById('uploadProgress');
    var progressBar = progress.querySelector('.progress-bar');
    progress.style.display = 'block';
    progressBar.style.width = '0%';
    document.querySelector('.upload-link i').classList.replace('fa-upload', 'fa-spinner');

    // Get the current datetime
    const currentDatetime = new Date().toISOString().replace(/[-T:]/g, '');

    // Create a filename with the current datetime
    const filename = `recording_${currentDatetime}.wav`;
    // Get the name value
    const name = document.getElementById("name").value;

    // Create a new Date object
    var currentDateT = new Date();
    // Get the current date and time components
    var year = currentDateT.getFullYear();
    var month = currentDateT.getMonth() + 1; // Month is zero-indexed, so we add 1
    var day = currentDateT.getDate();

    // Format the date and time as a string
    var currentDate = year + '-' + addLeadingZero(month) + '-' + addLeadingZero(day);

    // Function to add leading zero to single-digit numbers
    function addLeadingZero(number) {
        return number < 10 ? '0' + number : number;
    }

    // Upload the recording to the server
    const formData = new FormData();
    formData.append('audio', blob, filename);
    formData.append('name', name);
    formData.append('date', currentDate);

    fetch('/uploadAudioRoute_prefix/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
	// ............................................................
	.then(data => {
		clearInterval(uploadInterval); // Clear the interval for simulated progress
		progressBar.style.width = '100%';
		setTimeout(() => {
			progress.style.display = 'none';
			progressBar.style.width = '0%';
			document.getElementById('uploadCompleteMessage').style.display = 'block'; // Show upload complete message
	
			// Hide the upload complete message after 2 seconds (adjust as needed)
			setTimeout(() => {
				document.getElementById('uploadCompleteMessage').style.display = 'none';
				window.location.reload(); // Reload the page
			}, 5000);
		}, 1000);
	
		// Reset the upload icon when the recording process is finished
		document.querySelector('.upload-link i').classList.replace('fa-spinner', 'fa-upload');
	})

    .catch(error => {
        console.error('Error uploading audio:', error);
        // Handle the error, perhaps by showing an error message to the user
        // Reset the upload icon when the recording process is finished
        document.querySelector('.upload-link i').classList.replace('fa-spinner', 'fa-upload');
        // Hide the progress bar if an error occurs during upload
        progress.style.display = 'none';
        progressBar.style.width = '0%';
    });

    // Simulate progress
    var uploadInterval = setInterval(function () {
        if (parseInt(progressBar.style.width, 10) >= 100) {
            clearInterval(uploadInterval);
        } else {
            var currentWidth = parseInt(progressBar.style.width, 10);
            progressBar.style.width = (currentWidth + 10) + '%';
        }
    }, 1000);
}
// ............................................................
// ............................................................
function createDownloadLink(blob) {
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');

    // Name of .wav file to use during upload and download (without extension)
    var filename = new Date().toISOString();

    // Add controls to the <audio> element
    au.controls = true;
    au.src = url;

// Function to create button element with specified icon and tooltip
function createButton(iconClass, title) {
    var button = document.createElement('button');
    button.innerHTML = `<i class="${iconClass}"></i>`;
    button.setAttribute('title', title);
    button.classList.add('button'); // Add a class for styling
    return button;
}

// Play button
var playButton = createButton('fas fa-play', 'Play');
playButton.addEventListener('click', function () {
    au.play();
});
li.appendChild(playButton);

// Stop button
var stopButton = createButton('fas fa-stop', 'Stop');
stopButton.addEventListener('click', function () {
    au.pause();
    au.currentTime = 0;
});
li.appendChild(stopButton);

// Save to disk link
var downloadButton = createButton('fas fa-download', 'Save to disk');
downloadButton.href = url;
downloadButton.download = filename + ".wav";
var link = document.createElement('a'); // Create 'a' element for the download link
link.appendChild(downloadButton);
li.appendChild(link);

// Upload button
var uploadButton = createButton('fas fa-upload', 'Upload');
uploadButton.addEventListener("click", function (event) {
    event.preventDefault();
    uploadRecording(blob);
});
uploadButton.style.marginLeft = "10px"; // Add left margin
uploadButton.style.display = "none"; // Hide the upload button initially
li.appendChild(uploadButton);


// Apply flexbox styles to the list item to evenly space the buttons
li.style.display = 'flex';
li.style.justifyContent = 'space-between';

// Add the new audio element to li
li.appendChild(au);

// Create a span element to wrap the filename text
var filenameSpan = document.createElement('span');
filenameSpan.textContent = filename + ".wav";


filenameSpan.style.display = "none"; 

// Append the span element to the list item
li.appendChild(filenameSpan);


// Add the li element to the ol
recordingsList.appendChild(li);

}

    // ............................................................
