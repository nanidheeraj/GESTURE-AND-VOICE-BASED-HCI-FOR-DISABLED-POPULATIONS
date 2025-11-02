const socket = io();

// State
let gestureEnabled = false;
let voiceEnabled = false;
let allActionsList = [];

// DOM Elements
const gestureToggle = document.getElementById("gestureToggle");
const voiceToggle = document.getElementById("voiceToggle");
const gestureStatus = document.getElementById("gestureStatus");
const voiceStatus = document.getElementById("voiceStatus");
const gestureResult = document.getElementById("gestureResult");
const voiceResult = document.getElementById("voiceResult");
const videoFeed = document.getElementById("videoFeed");

// Stat elements
const gestureCount = document.getElementById("gestureCount");
const commandCount = document.getElementById("commandCount");
const actionCount = document.getElementById("actionCount");

// Save Buttons
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const saveGesturesBtn = document.getElementById("saveGesturesBtn");
const saveVoiceBtn = document.getElementById("saveVoiceBtn");

// Learn Gesture DOM Elements
const learnGestureBtn = document.getElementById("learn-gesture-btn");
const newGestureNameInput = document.getElementById("new-gesture-name");
const learnStatusEl = document.getElementById("learn-status");

// Tab functionality
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const tabName = btn.dataset.tab;
    document
      .querySelectorAll(".tab-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document
      .querySelectorAll(".tab-content")
      .forEach((content) => content.classList.remove("active"));
    document.getElementById(tabName).classList.add("active");
  });
});

// Gesture toggle
gestureToggle.addEventListener("change", () => {
  if (gestureToggle.checked) {
    socket.emit("start_gesture");
    gestureEnabled = true;
  } else {
    socket.emit("stop_gesture");
    gestureEnabled = false;
    // Update state in case it was disabled
    gestureStatus.textContent = `Status: Gesture recognition stopped`;
  }
});

// Voice toggle
voiceToggle.addEventListener("change", () => {
  if (voiceToggle.checked) {
    socket.emit("start_voice");
    voiceEnabled = true;
  } else {
    socket.emit("stop_voice");
    voiceEnabled = false;
    voiceStatus.textContent = `Status: Voice recognition stopped`;
  }
});

// Socket.IO events
socket.on("connect", () => {
  console.log("Connected to server");
});

socket.on("gesture_status", (data) => {
  gestureStatus.textContent = `Status: ${data.message}`;
});

socket.on("voice_status", (data) => {
  voiceStatus.textContent = `Status: ${data.message}`;
});

// --- MODIFIED: Fixed stat counting ---
socket.on("gesture_recognized", (data) => {
  gestureResult.textContent = `✓ Gesture: ${data.gesture} (${(
    data.confidence * 100
  ).toFixed(1)}%) → Action: ${data.action || "None"}`;

  // Only increment counters for valid actions, not for "None" or toggles
  gestureCount.textContent = parseInt(gestureCount.textContent) + 1;
  if (
    data.action &&
    data.action !== "None" &&
    !data.action.startsWith("Cursor Mode")
  ) {
    actionCount.textContent = parseInt(actionCount.textContent) + 1;
  }
});

socket.on("voice_recognized", (data) => {
  voiceResult.textContent = `✓ Voice: "${data.text}" → Action: ${
    data.action || "None"
  }`;
  commandCount.textContent = parseInt(commandCount.textContent) + 1;
  if (data.action && data.action !== "None") {
    actionCount.textContent = parseInt(actionCount.textContent) + 1;
  }
});

socket.on("video_frame", (data) => {
  videoFeed.src = "data:image/jpeg;base64," + data.frame;
});

socket.on("error", (data) => {
  alert("Error: " + data.message);
  // Re-enable toggles if they failed
  if (data.message.includes("gesture")) {
    gestureToggle.checked = false;
    gestureEnabled = false;
  }
});

// --- Customization UI Functions ---

function createActionDropdown(actionList, selectedAction) {
  const select = document.createElement("select");
  select.className = "action-select";
  const noneOption = document.createElement("option");
  noneOption.value = "null";
  noneOption.textContent = "None";
  select.appendChild(noneOption);
  actionList.forEach((action) => {
    const option = document.createElement("option");
    option.value = action;
    option.textContent = action;
    if (action === selectedAction) {
      option.selected = true;
    }
    select.appendChild(option);
  });
  return select;
}

// --- MODIFIED: To add delete button and sorting ---
function populateGestureTab(gesturesConfig, allActions) {
  const gestureTableBody = document.querySelector("#gestureList tbody");
  gestureTableBody.innerHTML = "";

  // Sort gestures: built-in first, then custom
  const sortedGestures = Object.entries(gesturesConfig).sort((a, b) => {
    const aIsCustom = a[1].name === a[0];
    const bIsCustom = b[1].name === b[0];
    if (aIsCustom && !bIsCustom) return 1;
    if (!aIsCustom && bIsCustom) return -1;
    return a[1].name.localeCompare(b[1].name);
  });

  for (const [gestureKey, gestureData] of sortedGestures) {
    const row = document.createElement("tr");
    const isCustom = gestureKey === gestureData.name; // Check if it's a custom gesture

    const nameCell = document.createElement("td");
    nameCell.textContent = gestureData.name;
    if (isCustom) {
      nameCell.textContent += " (Custom)";
      nameCell.style.color = "#0056b3";
      nameCell.style.fontWeight = "bold";
    }

    const actionCell = document.createElement("td");
    const dropdown = createActionDropdown(allActions, gestureData.action);
    dropdown.dataset.gestureKey = gestureKey;
    actionCell.appendChild(dropdown);

    // NEW: Controls Cell
    const controlsCell = document.createElement("td");
    if (isCustom) {
      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "Delete";
      deleteBtn.className = "btn-danger";
      deleteBtn.dataset.gestureKey = gestureKey;
      deleteBtn.addEventListener("click", deleteCustomGesture);
      controlsCell.appendChild(deleteBtn);
    }

    row.appendChild(nameCell);
    row.appendChild(actionCell);
    row.appendChild(controlsCell); // Add new cell
    gestureTableBody.appendChild(row);
  }
}

function populateVoiceTab(voiceConfig, allActions) {
  const voiceTableBody = document.querySelector("#voiceList tbody");
  voiceTableBody.innerHTML = "";
  for (const [commandKey, commandData] of Object.entries(voiceConfig)) {
    const row = document.createElement("tr");
    const commandCell = document.createElement("td");
    commandCell.textContent = commandData.command;
    const actionCell = document.createElement("td");
    const dropdown = createActionDropdown(allActions, commandData.action);
    dropdown.dataset.commandKey = commandKey;
    actionCell.appendChild(dropdown);
    row.appendChild(commandCell);
    row.appendChild(actionCell);
    voiceTableBody.appendChild(row);
  }
}

async function loadInitialData() {
  try {
    let actionsResponse = await fetch("/api/actions");
    allActionsList = await actionsResponse.json();
    let configResponse = await fetch("/api/config");
    const config = await configResponse.json();

    document.getElementById("cameraIndex").value = config.settings.camera_index;
    document.getElementById("cameraWidth").value = config.settings.camera_width;
    document.getElementById("cameraHeight").value =
      config.settings.camera_height;
    document.getElementById("gestureCooldown").value =
      config.settings.gesture_cooldown;
    document.getElementById("voiceCooldown").value =
      config.settings.voice_cooldown;
    populateGestureTab(config.gestures, allActionsList);
    populateVoiceTab(config.voice_commands, allActionsList);
  } catch (error) {
    console.error("Failed to load initial data:", error);
    alert("Failed to load configuration from server.");
  }
}

document.addEventListener("DOMContentLoaded", loadInitialData);

// --- Save Listeners (Unchanged) ---
saveSettingsBtn.addEventListener("click", () => {
  const settings = {
    settings: {
      camera_index: parseInt(document.getElementById("cameraIndex").value),
      camera_width: parseInt(document.getElementById("cameraWidth").value),
      camera_height: parseInt(document.getElementById("cameraHeight").value),
      gesture_cooldown: parseFloat(
        document.getElementById("gestureCooldown").value
      ),
      voice_cooldown: parseFloat(
        document.getElementById("voiceCooldown").value
      ),
    },
  };
  fetch("/api/config/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert(
          "Settings saved successfully! Restarting gesture recognition if active."
        );
      } else {
        alert("Error saving settings: " + data.error);
      }
    });
});
saveGesturesBtn.addEventListener("click", () => {
  const gestureMappings = {};
  document.querySelectorAll("#gestureList .action-select").forEach((select) => {
    const gestureKey = select.dataset.gestureKey;
    const actionValue = select.value;
    gestureMappings[gestureKey] = actionValue;
  });
  fetch("/api/gestures", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(gestureMappings),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Gesture actions saved successfully!");
      } else {
        alert("Error saving gesture actions: " + data.error);
      }
    });
});
saveVoiceBtn.addEventListener("click", () => {
  const voiceMappings = {};
  document.querySelectorAll("#voiceList .action-select").forEach((select) => {
    const commandKey = select.dataset.commandKey;
    const actionValue = select.value;
    voiceMappings[commandKey] = actionValue;
  });
  fetch("/api/voice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(voiceMappings),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Voice actions saved successfully!");
      } else {
        alert("Error saving voice actions: " + data.error);
      }
    });
});

// --- NEW: Delete Gesture Function ---
async function deleteCustomGesture(event) {
  const gestureKey = event.target.dataset.gestureKey;
  if (
    !confirm(
      `Are you sure you want to delete the custom gesture "${gestureKey}"? This cannot be undone.`
    )
  ) {
    return;
  }
  try {
    const response = await fetch("/api/gesture/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: gestureKey }),
    });
    const result = await response.json();
    if (result.success) {
      alert("Gesture deleted successfully.");
      loadInitialData(); // Refresh the UI
    } else {
      alert("Error deleting gesture: " + result.error);
    }
  } catch (error) {
    alert("Failed to contact server: " + error);
  }
}

// --- MODIFIED: LEARN GESTURE FUNCTIONALITY ---

learnGestureBtn.addEventListener("click", startLearning);

async function startLearning() {
  const gestureName = newGestureNameInput.value.trim();
  if (!gestureName) {
    alert("Please enter a name for the new gesture.");
    return;
  }

  // --- NEW: Check if gesture is enabled ---
  if (!gestureEnabled) {
    alert("Please enable Gesture Recognition before learning a new gesture.");
    return;
  }

  learnGestureBtn.disabled = true;
  learnGestureBtn.textContent = "Learning...";
  learnStatusEl.textContent = "Starting...";
  learnStatusEl.className = "status-message learning";

  try {
    const response = await fetch("/api/learn_gesture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: gestureName }),
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.message);
    }

    learnStatusEl.textContent = result.message;

    // --- NEW: Auto-switch to dashboard ---
    alert(
      "Learning started! Please go to the 'Dashboard' tab to see the video feed and hold your gesture."
    );
    document.querySelector('.tab-btn[data-tab="dashboard"]').click();

    pollLearningStatus();
  } catch (error) {
    console.error("Error starting learning:", error);
    learnStatusEl.textContent = `Error: ${error.message}`;
    learnStatusEl.className = "status-message error";
    learnGestureBtn.disabled = false;
    learnGestureBtn.textContent = "Learn New Gesture";
  }
}

async function pollLearningStatus() {
  try {
    const response = await fetch("/api/get_learning_status");
    const result = await response.json();

    if (result.status === "learning") {
      learnStatusEl.textContent = result.message;
      setTimeout(pollLearningStatus, 500); // Check again
    } else if (result.status === "success") {
      learnStatusEl.textContent = result.message;
      learnStatusEl.className = "status-message success";
      newGestureNameInput.value = "";
      learnGestureBtn.disabled = false;
      learnGestureBtn.textContent = "Learn New Gesture";

      alert(
        "Gesture learned successfully! It has been added to the gesture list."
      );
      loadInitialData(); // Refresh the gesture table
      document.querySelector('.tab-btn[data-tab="gestures"]').click(); // Switch back to gestures tab
    } else if (result.status === "error") {
      learnStatusEl.textContent = result.message;
      learnStatusEl.className = "status-message error";
      learnGestureBtn.disabled = false;
      learnGestureBtn.textContent = "Learn New Gesture";
    }
  } catch (error) {
    console.error("Error polling status:", error);
    learnStatusEl.textContent = "Error checking learning status.";
    learnStatusEl.className = "status-message error";
    learnGestureBtn.disabled = false;
    learnGestureBtn.textContent = "Learn New Gesture";
  }
}
