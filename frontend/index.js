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
