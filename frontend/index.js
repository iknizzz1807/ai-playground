// Xử lý chuyển tab
const tabs = document.querySelectorAll(".tab");
const playgrounds = document.querySelectorAll(".playground");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // Removed active class from all tabs and playgrounds
    tabs.forEach((t) => t.classList.remove("active"));
    playgrounds.forEach((p) => p.classList.remove("active"));

    // Add active class to clicked tab and its playground
    tab.classList.add("active");
    const targetId = tab.id.replace("tab-", "playground-");
    document.getElementById(targetId).classList.add("active");
  });
});

// ================ DIGIT RECOGNITION PLAYGROUND ================
// Khởi tạo canvas và context để vẽ
const canvasContainer = document.getElementById("canvas-container");
const canvas = document.createElement("canvas");
canvas.width = 280; // Kích thước phổ biến cho nhận dạng chữ viết tay
canvas.height = 280;
canvasContainer.appendChild(canvas);
const ctx = canvas.getContext("2d");
ctx.fillStyle = "white"; // Nền trắng
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Biến để theo dõi trạng thái vẽ
let isDrawing = false;

// Hàm xử lý sự kiện chuột
canvas.addEventListener("mousedown", (e) => {
  isDrawing = true;
  ctx.beginPath();
  ctx.moveTo(e.offsetX, e.offsetY);
});

canvas.addEventListener("mousemove", (e) => {
  if (isDrawing) {
    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 10; // Độ dày nét vẽ
    ctx.stroke();
  }
});

canvas.addEventListener("mouseup", () => {
  isDrawing = false;
});

// Mobile/touch support
canvas.addEventListener("touchstart", (e) => {
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  const mouseEvent = new MouseEvent("mousedown", {
    clientX: touch.clientX,
    clientY: touch.clientY,
  });
  canvas.dispatchEvent(mouseEvent);
});

canvas.addEventListener("touchmove", (e) => {
  e.preventDefault();
  const touch = e.touches[0];
  const mouseEvent = new MouseEvent("mousemove", {
    clientX: touch.clientX,
    clientY: touch.clientY,
  });
  canvas.dispatchEvent(mouseEvent);
});

canvas.addEventListener("touchend", (e) => {
  e.preventDefault();
  const mouseEvent = new MouseEvent("mouseup", {});
  canvas.dispatchEvent(mouseEvent);
});

// Nút gửi dữ liệu tới backend
const recognizeButton = document.getElementById("recognize-button");
const clearButton = document.getElementById("clear-button");
const digitResultContainer = document.getElementById("digit-result-container");

recognizeButton.addEventListener("click", async () => {
  try {
    // Hiển thị trạng thái đang xử lý
    recognizeButton.disabled = true;
    recognizeButton.textContent = "Processing...";

    // Chuyển canvas thành base64 để gửi qua API
    const imageData = canvas.toDataURL("image/png");

    // Gửi request tới backend
    const response = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: imageData }),
    });

    const result = await response.json();

    // Hiển thị kết quả với độ tin cậy
    const resultText = `Predicted digit: ${result.prediction} (Confidence: ${result.confidence}%)`;

    // Cập nhật container kết quả
    digitResultContainer.innerHTML = "";
    const resultPara = document.createElement("p");
    resultPara.textContent = resultText;

    // Đánh dấu độ tin cậy bằng màu sắc
    if (result.confidence > 90) {
      resultPara.style.color = "green";
    } else if (result.confidence > 70) {
      resultPara.style.color = "blue";
    } else {
      resultPara.style.color = "red"; // Độ tin cậy thấp
    }

    digitResultContainer.appendChild(resultPara);
  } catch (error) {
    console.error("Error:", error);
    digitResultContainer.innerHTML =
      '<p style="color: red">Error recognizing digit. Please try again.</p>';
  } finally {
    // Khôi phục trạng thái nút
    recognizeButton.disabled = false;
    recognizeButton.textContent = "Recognize";
  }
});

// Nút xóa canvas
clearButton.addEventListener("click", () => {
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  // Reset result container
  digitResultContainer.innerHTML = '<p>Draw a digit and click "Recognize"</p>';
});

// ================ EMOJI PREDICTION PLAYGROUND ================
const textInput = document.getElementById("text-input");
const emojiButton = document.getElementById("emoji-button");
const emojiResultContainer = document.getElementById("emoji-result-container");

emojiButton.addEventListener("click", async () => {
  try {
    // Validate input
    const text = textInput.value.trim();
    if (!text) {
      emojiResultContainer.innerHTML =
        '<p style="color: red">Please enter some text first</p>';
      return;
    }

    // Show processing state
    emojiButton.disabled = true;
    emojiButton.textContent = "Analyzing...";

    // Send request to backend
    const response = await fetch("http://localhost:8000/predict-emoji", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    });

    const result = await response.json();

    // Check for error
    if (result.error) {
      emojiResultContainer.innerHTML = `<p style="color: red">Error: ${result.error}</p>`;
      return;
    }

    // Clear and update result container
    emojiResultContainer.innerHTML = "";

    // Create emoji display
    const emojiDiv = document.createElement("div");
    emojiDiv.className = "emoji";
    emojiDiv.textContent = result.emoji;
    emojiResultContainer.appendChild(emojiDiv);

    // Create result details
    const detailsDiv = document.createElement("div");
    detailsDiv.className = "emoji-details";
    detailsDiv.innerHTML = `
      <p><strong>Detected emotion:</strong> ${result.emotion}</p>
      <p><strong>Confidence:</strong> ${result.confidence}%</p>
    `;

    // Color based on confidence
    if (result.confidence > 90) {
      detailsDiv.style.color = "green";
    } else if (result.confidence > 70) {
      detailsDiv.style.color = "blue";
    } else {
      detailsDiv.style.color = "red";
    }

    emojiResultContainer.appendChild(detailsDiv);
  } catch (error) {
    console.error("Error:", error);
    emojiResultContainer.innerHTML =
      '<p style="color: red">Error analyzing text. Please try again.</p>';
  } finally {
    // Restore button state
    emojiButton.disabled = false;
    emojiButton.textContent = "Analyze Emotion";
  }
});

// ================ SPEECH TO TEXT PLAYGROUND ================
const recordButton = document.getElementById("record-button");
const recordingStatus = document.getElementById("recording-status");
const recordingTime = document.getElementById("recording-time");
const audioFileInput = document.getElementById("audio-file");
const fileNameDisplay = document.getElementById("file-name");
const transcribeButton = document.getElementById("transcribe-button");
const clearTranscriptionButton = document.getElementById(
  "clear-transcription-button"
);
const speechResultContainer = document.getElementById(
  "speech-result-container"
);

// Variables for recording
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingTimer;
let audioBlob;
let isRecording = false;

// Check if browser supports MediaRecorder
const hasRecordingSupport = () => {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
};

// Initialize recording functionality
if (hasRecordingSupport()) {
  recordButton.addEventListener("click", toggleRecording);
} else {
  recordingStatus.textContent = "Recording not supported in this browser";
  recordButton.style.backgroundColor = "#ccc";
  recordButton.style.cursor = "not-allowed";
}

// Function to toggle recording state
async function toggleRecording() {
  if (isRecording) {
    // Stop recording
    stopRecording();
  } else {
    // Start recording - Reset audio chunks here
    audioChunks = []; // Reset audio chunks mỗi lần bắt đầu ghi âm mới
    audioBlob = null; // Reset audio blob
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      startRecording(stream);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      recordingStatus.textContent =
        "Error accessing microphone. Please check permissions.";
    }
  }
}

// Start recording function
function startRecording(stream) {
  audioChunks = [];

  // Create MediaRecorder instance with specific MIME type for better compatibility
  const options = { mimeType: "audio/webm" };
  try {
    mediaRecorder = new MediaRecorder(stream, options);
  } catch (e) {
    console.error("WebM format not supported, trying alternative format", e);
    mediaRecorder = new MediaRecorder(stream);
  }

  // Update UI
  recordButton.classList.add("recording");
  recordingStatus.textContent = "Recording... Click to stop";
  isRecording = true;

  // Start timer
  recordingStartTime = Date.now();
  updateRecordingTime();
  recordingTimer = setInterval(updateRecordingTime, 1000);

  // Handle data available event
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };

  // Handle recording stop event
  mediaRecorder.onstop = () => {
    // Create audio blob with explicit MIME type
    const mimeType = mediaRecorder.mimeType || "audio/webm";
    audioBlob = new Blob(audioChunks, { type: mimeType });

    // Enable transcribe button
    transcribeButton.disabled = false;

    // Update status
    recordingStatus.textContent = "Recording saved. Click to record again.";

    // Stop all tracks to release microphone
    stream.getTracks().forEach((track) => track.stop());

    // Clear file input to prevent confusion
    audioFileInput.value = "";
    fileNameDisplay.textContent = "No file selected";
  };

  // Start recording - collect data every 1 second for more reliable data handling
  mediaRecorder.start(1000);
}

// Update recording time display
function updateRecordingTime() {
  const elapsedSeconds = Math.floor((Date.now() - recordingStartTime) / 1000);
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  recordingTime.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
    .toString()
    .padStart(2, "0")}`;
}

// Stop recording function
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();

    // Update UI
    recordButton.classList.remove("recording");
    isRecording = false;

    // Stop timer
    clearInterval(recordingTimer);
  }
}

// Handle file upload
audioFileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    const file = e.target.files[0];
    fileNameDisplay.textContent = file.name;

    // Disable transcribe button if recording is in progress
    if (!isRecording) {
      transcribeButton.disabled = false;
    }

    // Clear recorded audio
    audioBlob = null;
  }
});

// Transcribe function
transcribeButton.addEventListener("click", async () => {
  try {
    transcribeButton.disabled = true;
    transcribeButton.textContent = "Processing...";

    let response;

    if (audioBlob) {
      // Get MIME type of the blob
      const mimeType = audioBlob.type || "audio/webm";
      let format = "webm";

      // Extract format from MIME type
      if (mimeType.includes("webm")) format = "webm";
      else if (mimeType.includes("mp3") || mimeType.includes("mpeg"))
        format = "mp3";
      else if (mimeType.includes("ogg")) format = "ogg";
      else if (mimeType.includes("wav")) format = "wav";

      // Convert recorded audio to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);

      // Wait for the FileReader to complete
      const audioBase64 = await new Promise((resolve, reject) => {
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
      });

      // Send recorded audio with correctly detected format
      response = await fetch("http://localhost:8000/speech/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio: audioBase64, format: format }),
      });
    } else {
      throw new Error("No audio data available");
    }

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    // Display transcription
    displayTranscription(result);
    // Reset audio data after successful transcription to prevent reusing old data
    if (audioBlob) {
      // Keep a reference to current audioBlob for playback if needed
      const lastAudioBlob = audioBlob;

      // Reset for next recording
      audioBlob = null;
      audioChunks = [];

      // Optional: Create an audio element to test the transcribed audio
      /* 
      const audioURL = URL.createObjectURL(lastAudioBlob);
      const audioElement = document.createElement("audio");
      audioElement.controls = true;
      audioElement.src = audioURL;
      speechResultContainer.appendChild(audioElement);
      */
    }
  } catch (error) {
    console.error("Transcription error:", error);
    speechResultContainer.innerHTML = `
      <p style="color: red">Error: ${
        error.message || "Failed to transcribe audio"
      }</p>
    `;
  } finally {
    transcribeButton.disabled = false;
    transcribeButton.textContent = "Transcribe";
  }
});

// Display transcription results
function displayTranscription(result) {
  speechResultContainer.innerHTML = "";

  if (!result.transcription || result.transcription.trim() === "") {
    speechResultContainer.innerHTML = `
      <p>No speech detected. Please try again with clearer audio.</p>
    `;
    return;
  }

  const transcriptionContainer = document.createElement("div");

  // Create title
  const title = document.createElement("h3");
  title.textContent = "Transcription Result:";
  transcriptionContainer.appendChild(title);

  // Create transcription area
  const transcriptionArea = document.createElement("div");
  transcriptionArea.className = "transcription";

  if (result.timestamps && result.timestamps.length > 0) {
    // With timestamps
    result.timestamps.forEach((segment) => {
      const timestampSpan = document.createElement("span");
      timestampSpan.className = "timestamp";
      timestampSpan.textContent = `[${formatTime(segment.start)}-${formatTime(
        segment.end
      )}]`;

      const textSpan = document.createElement("span");
      textSpan.textContent = ` ${segment.text} `;

      transcriptionArea.appendChild(timestampSpan);
      transcriptionArea.appendChild(textSpan);
      transcriptionArea.appendChild(document.createElement("br"));
    });
  } else {
    // Without timestamps
    transcriptionArea.textContent = result.transcription;
  }

  transcriptionContainer.appendChild(transcriptionArea);

  // Add copy button
  const copyButton = document.createElement("button");
  copyButton.textContent = "Copy Text";
  copyButton.style.marginTop = "10px";
  copyButton.addEventListener("click", () => {
    navigator.clipboard
      .writeText(result.transcription)
      .then(() => {
        copyButton.textContent = "Copied!";
        setTimeout(() => {
          copyButton.textContent = "Copy Text";
        }, 2000);
      })
      .catch((err) => console.error("Failed to copy: ", err));
  });

  transcriptionContainer.appendChild(copyButton);
  speechResultContainer.appendChild(transcriptionContainer);
}

// Format time from seconds to MM:SS.ms
function formatTime(seconds) {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100);
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(
    2,
    "0"
  )}.${String(ms).padStart(2, "0")}`;
}

// Clear transcription button
clearTranscriptionButton.addEventListener("click", () => {
  speechResultContainer.innerHTML = `
    <p>Record or upload audio and click "Transcribe"</p>
  `;

  audioFileInput.value = "";
  fileNameDisplay.textContent = "No file selected";
  audioBlob = null;
  transcribeButton.disabled = true;
});
