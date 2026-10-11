// =========================================================================
// ACEest RUNTIME MACHINE SCRIPT ENGINE
// =========================================================================

const AI_PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]
};

let currentActiveClient = "";
let activeChartInstance = null;

/**
 * Bootstraps and seeds the client framework payload layer
 * to mock relational schema requirements.
 */
function bootApplicationStorageDB() {
    if (!localStorage.getItem('db_clients')) {
        localStorage.setItem('db_clients', JSON.stringify({
            "Jane Doe": { id: 1, name: "Jane Doe", age: 28, height: 165.0, weight: 62.5, program: "Full Body HIIT", calories: 1800, target_weight: 58.0, target_adherence: 85, status: "Active", end: "2027-08-14" },
            "Morgan Smith": { id: 2, name: "Morgan Smith", age: 32, height: 180.5, weight: 85.2, program: "Push/Pull/Legs", calories: 2700, target_weight: 80.0, target_adherence: 90, status: "Active", end: "2027-03-22" }
        }));
        localStorage.setItem('db_progress', JSON.stringify({
            "Jane Doe": [{ week: "Wk 1", val: 80 }, { week: "Wk 2", val: 95 }, { week: "Wk 3", val: 85 }, { week: "Wk 4", val: 90 }],
            "Morgan Smith": [{ week: "Wk 1", val: 70 }, { week: "Wk 2", val: 85 }, { week: "Wk 3", val: 80 }]
        }));
        localStorage.setItem('db_workouts', JSON.stringify({
            "Jane Doe": [{ date: "2026-10-10", type: "Cardio", duration: 45, notes: "HIIT treadmill system circuits" }],
            "Morgan Smith": [{ date: "2026-10-09", type: "Strength", duration: 60, notes: "Barbell compound loading sequences" }]
        }));
    }
    //rebuildClientDropdownList();
    refreshClientList();
}

/**
 * Executes a role-based login validation and view swap sequence.
 */
/**
 * Executes a role-based login validation and view swap sequence.
 */

/**
 * Re-reads profile descriptors from storage to refresh the dropdown menu selectors.
 */
function rebuildClientDropdownList() {
    const select = document.getElementById('client-selector');
    select.innerHTML = '<option value="">-- No Profile Selected --</option>';
    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');

    Object.keys(clients).forEach(key => {
        const opt = document.createElement('option');
        opt.value = key;
        opt.innerText = key;
        select.appendChild(opt);
    });
    select.value = currentActiveClient;
}

/**
 * Active element wrapper caught by select change events.
 */
function onClientProfileActivated(val) {
    currentActiveClient = val;
    //synchronizeActiveClientRecord();
    //refreshClientList();
    loadClient();
}

/**
 * Syncs active dashboard text fragments and table data loops.
 */
function synchronizeActiveClientRecord() {
    if (!currentActiveClient) {
        document.getElementById('summary-diagnostics-console').innerText = "Select an active client profile matrix from the selector console to generate dynamic diagnostic summary records...";
        document.getElementById('workout-ledger-rows').innerHTML = '<tr><td colspan="4" style="text-align:center;" class="text-neutral-500 italic">Select active profile to render ledger tracking sequences</td></tr>';
        if (activeChartInstance) activeChartInstance.destroy();
        return;
    }

    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');
    const data = clients[currentActiveClient];
    if (!data) return;

    document.getElementById('summary-diagnostics-console').innerText =
        `Name: ${data.name}\nProgram: ${data.program || 'None Assigned'}\nCalories: ${data.calories || 'N/A'}\nMembership: ${data.status}`;

    renderWorkoutLedgerTable();
    renderPerformanceChartLoop();
}

/**
 * Captures name variables to generate an independent database record.
 */
/**
 * Captures name inputs via dialog to generate an independent database record on the API backend.
 */
function triggerAddClient() {
    const name = prompt("Enter client name:");
    if (!name || name.trim() === "") return;

    fetch("/api/client", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            name: name
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Save execution failure"); });
        }
        return response.json();
    })
    .then(data => {
        currentActiveClient = name;

        if (typeof refreshClientList === "function") {
            refreshClientList();
        }
        alert(`Client ${name} saved successfully.`);
    })
    .catch(error => {
        console.error("Save Client Endpoint Mismatch Exception:", error);
        alert(`Failed to execute record insertion: ${error.message}`);
    });
}


/**
 * Uses a basic randomization loop to emulate the original script's automated assignment logic.
 */
/**
 * Triggers the backend AI generator to randomly select and assign a template protocol to a profile.
 */
function triggerAIGenerator() {
    if (!currentActiveClient) {
        return alert("Select a client first");
    }

    // Capture the template dictionary keys to pick a type category random variable
    const trackingKeys = Object.keys(AI_PROGRAM_TEMPLATES);
    if (trackingKeys.length === 0) {
        return alert("Configuration Error: No operational AI templates initialized.");
    }
    const pickedProgramType = trackingKeys[Math.floor(Math.random() * trackingKeys.length)];

    // Dispatch the payload directly to your backend endpoint matrix
    fetch("/api/ai_program", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            name: currentActiveClient,
            program_type: pickedProgramType
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || "AI script generator engine failure");
            });
        }
        return response.json();
    })
    .then(data => {
        // Unpack response message or fallback to dynamic alert layout parameters
        const serverFeedbackMessage = data.message || `Program Generated for ${currentActiveClient}`;
        alert(serverFeedbackMessage);

        // Force systematic interface layout re-renders to load fresh profile state rows
        if (typeof loadClient === "function") {
            loadClient();
        }
    })
    .catch(error => {
        console.error("AI Generation Exception:", error);
        alert(`Failed to execute engine script: ${error.message}`);
    });
}


/**
 * Emulates the original report builder pipeline.
 */
function triggerPDFReport() {
    if (!currentActiveClient) {
        return alert("Select a client first");
    }
    alert(currentActiveClient);

    // Encode parameter safely to handle spaces and complex special characters
    const targetUrl = `/api/generate_pdf?name=${encodeURIComponent(currentActiveClient)}`;

    fetch(targetUrl, {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    })
    .then(response => {
        if (!response.ok) {
            // Unpack structured error messages if client profile context is missing
            return response.json().then(err => { throw new Error(err.error || "Server error"); });
        }
        return response.json();
    })
    .then(data => {
        // Precise string feedback alert matching successful output logs
        alert(`PDF Structural Serialization complete:\n"${currentActiveClient}_report.pdf" created successfully.`);
    })
    .catch(error => {
        console.error("PDF Generation Exception:", error);
        alert(`Export Failure: ${error.message}`);
    });
}

/**
 * Reads profile timelines to return target subscription values.
 */
function triggerMembershipCheck() {
   /* if (!currentActiveClient) return alert("Select a client first");
    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');
    const data = clients[currentActiveClient];
    alert(`Membership: ${data.status}\nRenewal Date: ${data.end || 'N/A'}`); */
    if (!currentActiveClient) {
        return alert("Select a client first");
    }

    // Safely encode parameters to protect spaces and special characters inside URLs
    const targetUrl = `/api/check_membership?name=${encodeURIComponent(currentActiveClient)}`;

    fetch(targetUrl, {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    })
    .then(response => {
        if (!response.ok) {
            // Extract server exception payloads cleanly if records are missing
            return response.json().then(err => { throw new Error(err.error || "Membership check failed"); });
        }
        return response.json();
    })
    .then(data => {
        // Unpack the exact pre-formatted multi-line message block returned by Python
        if (data && data.message) {
            alert(data.message);
        } else {
            alert(`Membership: Active\nRenewal Date: N/A`);
        }
    })
    .catch(error => {
        console.error("Membership Check Engine Exception:", error);
        alert(`Verification Error: ${error.message}`);
    });
}

/**
 * Re-renders the rows inside the workout table.
 */
/*function renderWorkoutLedgerTable() {
    const tbody = document.getElementById('workout-ledger-rows');
    tbody.innerHTML = "";
    const workoutList = JSON.parse(localStorage.getItem('db_workouts') || '{}')[currentActiveClient] || [];

    if (workoutList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;" class="text-neutral-500 italic">No historical data logs recorded.</td></tr>';
        return;
    }

    workoutList.forEach(w => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${w.date}</td><td>${w.type}</td><td style="text-align:center;">${w.duration} min</td><td>${w.notes}</td>`;
        tbody.appendChild(tr);
    });
}
*/

/**
 * Fetches and renders historical workout ledger entries straight from the backend database.
 */
function renderWorkoutLedgerTable() {
    const tbody = document.getElementById('workout-ledger-rows');
    if (!tbody) return;

    if (!currentActiveClient) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;" class="text-neutral-500 italic">Select active profile to render ledger tracking sequences</td></tr>';
        return;
    }

    // Safely encode parameters to support spaces and special characters inside URLs
    const targetUrl = `/api/workout?name=${encodeURIComponent(currentActiveClient)}`;

    fetch(targetUrl, {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Failed to load history"); });
        }
        return response.json();
    })
    .then(data => {
        tbody.innerHTML = "";

        // Extract the tuple collection block array returned from Python
        const historyList = data.workout_history || [];

        if (historyList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;" class="text-neutral-500 italic">No historical data logs recorded.</td></tr>';
            return;
        }

        // Iterate over arrays by index position to mirror the SQLite SELECT column sorting rules exactly
        historyList.forEach(workoutTuple => {
            const dateVal = workoutTuple[0] || "N/A";
            const typeVal = workoutTuple[1] || "N/A";
            const durationVal = workoutTuple[2] !== undefined ? `${workoutTuple[2]} min` : "N/A";
            const notesVal = workoutTuple[3] || "";

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${dateVal}</td>
                <td>${typeVal}</td>
                <td style="text-align:center;">${durationVal}</td>
                <td>${notesVal}</td>
            `;
            tbody.appendChild(tr);
        });
    })
    .catch(error => {
        console.error("Workout Ledger Interface Exception Failure Loop:", error);
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: #ef4444;" class="font-semibold">Sync Failure: ${error.message}</td></tr>`;
    });
}


/**
 * Initializes form validation defaults inside open input modals.
 */
function openLogWorkoutWindow() {
    if (!currentActiveClient) return alert("Select an active client target frame first.");
    document.getElementById('modal-workout-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('modal-workout-duration').value = "60";
    document.getElementById('modal-workout-notes').value = "";
    document.getElementById('workout-modal').classList.remove('hidden');
}

/**
 * Appends a new item payload directly to your workspace tracking histories.
 */
function commitWorkoutEntry() {
    /* const dateVal = document.getElementById('modal-workout-date').value;
    const typeVal = document.getElementById('modal-workout-type').value;
    const durVal = parseInt(document.getElementById('modal-workout-duration').value) || 60;
    const notesVal = document.getElementById('modal-workout-notes').value || "N/A";

    const workouts = JSON.parse(localStorage.getItem('db_workouts') || '{}');
    if (!workouts[currentActiveClient]) workouts[currentActiveClient] = [];

    workouts[currentActiveClient].unshift({ date: dateVal, type: typeVal, duration: durVal, notes: notesVal });
    localStorage.setItem('db_workouts', JSON.stringify(workouts));

    closeModalWindow('workout-modal');
    renderWorkoutLedgerTable(); */
     // 1. Extract values straight from the modal form input element fields
    const dateVal = document.getElementById('modal-workout-date').value;
    let typeVal = document.getElementById('modal-workout-type').value;
    const durVal = parseFloat(document.getElementById('modal-workout-duration').value) || 60.0;
    const notesVal = document.getElementById('modal-workout-notes').value || "";

    if (!currentActiveClient) {
        return alert("Select an active client profile first.");
    }

    // SANITIZATION LAYER: Normalise "Cardio" down to "Conditioning" to prevent 404 validation failures
    if (typeVal === "Cardio") {
        typeVal = "Conditioning";
    }

    // 2. Map payload keys precisely to match request.json lookups inside Python
    const payload = {
        name: currentActiveClient,
        date: dateVal,
        workout: typeVal, // Keyed explicitly to "workout" as required by data.get("workout")
        duration: durVal,
        notes: notesVal
    };

    // 3. Dispatch payload to backend endpoint matrix
    fetch("/api/workout", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            // Unpack custom server exception messages cleanly if parameters fail constraint checks
            return response.json().then(err => { throw new Error(err.error || "Failed to log entry"); });
        }
        return response.json();
    })
    .then(data => {
        // Notify operator using success messages returned straight from the backend
        alert(data.message || "Workout logged successfully");

        // 4. Hide form modal backdrop view frame
        if (typeof closeModalWindow === "function") {
            closeModalWindow('workout-modal');
        }

        // 5. Instantly refresh the historical ledger layout table view to load new database rows
        if (typeof renderWorkoutLedgerTable === "function") {
            renderWorkoutLedgerTable();
        }
    })
    .catch(error => {
        console.error("Workout Logging Mismatch Exception:", error);
        alert(`Log Failure: ${error.message}`);
    });
}

/**
 * Replicates the Tkinter Notebook widget tab switches.
 */
function switchNotebookTab(targetId) {
    document.querySelectorAll('.tab-link').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.notebook-pane').forEach(pane => pane.classList.remove('active'));

    document.getElementById(`tab-btn-${targetId}`).classList.add('active');
    document.getElementById(`notebook-tab-${targetId}`).classList.add('active');

    if (targetId === 'summary') {
renderPerformanceChartLoop();
}
}
/**
• Captures historical indices to re-draw linear chart lines over canvas grids.
*/
function renderPerformanceChartLoop() {
if (!currentActiveClient) return;
const ctx = document.getElementById('analyticsAdherenceChart').getContext('2d');
if (activeChartInstance) activeChartInstance.destroy();const trackData = JSON.parse(localStorage.getItem('db_progress') || '{}')[currentActiveClient] || [];
const labels = trackData.map(item => item.week);
const values = trackData.map(item => item.val);activeChartInstance = new Chart(ctx, {
type: 'line',
data: {
labels: labels,
datasets: [{
label: 'Weekly Adherence (%)',
data: values,
borderColor: '#d4af37',
backgroundColor: 'rgba(212, 175, 55, 0.08)',
borderWidth: 2,
fill: true,
tension: 0.15
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
scales: {
y: { min: 0, max: 100, grid: { color: '#2a2a2a' }, ticks: { color: '#aaa' } },
x: { grid: { color: '#2a2a2a' }, ticks: { color: '#aaa' } }
},
plugins: { legend: { display: false } }
}
});
}
/**
• Utility helper to close targeted window models.
*/
function closeModalWindow(id) {
document.getElementById(id).classList.add('hidden');
}
// Ensure the page boots strictly directly into the authentication layout context
/*document.addEventListener("DOMContentLoaded", function() {
document.getElementById('login-screen').classList.remove('hidden');
document.getElementById('login-screen').style.display = 'flex';
document.getElementById('app-container').classList.add('hidden');
document.getElementById('app-container').style.display = 'none';
});*/

function executeLogin() {
    const user = document.getElementById('auth-username').value.trim();
    const pass = document.getElementById('auth-password').value.trim();

    if (user === "admin" && pass === "admin") {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('app-container').classList.remove('hidden');
        document.getElementById('app-title-header').innerText = "ACEest Dashboard (Admin)";
        bootApplicationStorageDB();
    } else {
        alert("Login Failed: Invalid credentials layout parameters.");
    }
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-container').classList.add('hidden');
    refreshClientList();
});

function refreshClientList() {
    fetch('/api/clients/names', { method: 'GET' })
    .then(res => {
        if (!res.ok) throw new Error("Backend program definitions sync failure");
        return res.json();
    })
    .then(data => {
        const combobox = document.getElementById("client-selector");
        combobox.innerHTML = '<option value="" selected>-- Select Existing Client --</option>';

        // Handles safe fallback tracking array iteration loops cleanly
        const clients = data.clients || data.names || data;

        clients.forEach(client => {
            // Unpack element array row structures sent directly from SQLite data sets
            const nameValue = (typeof client === 'object' && client !== null) ? (client.name || client[0]) : client;
            if (nameValue) {
                const option = document.createElement("option");
                option.value = nameValue;
                option.textContent = nameValue;
                combobox.appendChild(option);
            }
        });
        if (currentClient) combobox.value = currentClient;
    })
    .catch(err => console.error("API error loading fitness modules:", err));
}

/**
 * Loads an active client profile's parameters and logs it to the console terminal view.
 */
function loadClient() {
    const name = currentActiveClient;

    if (!currentActiveClient) {
        document.getElementById('summary-diagnostics-console').innerText = "Select an active client profile matrix from the selector console to generate dynamic diagnostic summary records...";
        document.getElementById('workout-ledger-rows').innerHTML = '<tr><td colspan="4" style="text-align:center;" class="text-neutral-500 italic">Select active profile to render ledger tracking sequences</td></tr>';
        if (activeChartInstance) activeChartInstance.destroy();
        return;
    }

    if (!name) {
        alert("Enter or select client name first.");
        return;
    }

    fetch('/api/refresh_summary?name=' + encodeURIComponent(name))
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.error || "Client tracking structure not found."); });
        }
        return res.json();
    })
    .then(data => {
        // FIXED: Extract the lower-case payload nested inside your API's "message" key
        if (!data || !data.message) return;
        const profile = data.message;

        // Render data using the exact case matching your backend dict keys (profile.name, profile.program, etc.)
        document.getElementById('summary-diagnostics-console').innerText =
            `Name: ${profile.name || 'N/A'}\n` +
            `Program: ${profile.program || 'None Assigned'}\n` +
            `Calories: ${profile.calories || 'N/A'}\n` +
            `Membership: ${profile.membership || 'Active'}`;

        // Cascade execution signals to update associated tabs and analytics
        if (typeof renderWorkoutLedgerTable === "function") {
            renderWorkoutLedgerTable();
        }
        if (typeof renderPerformanceChartLoop === "function") {
            renderPerformanceChartLoop();
        }
    })
    .catch(err => {
        console.error("Load Client System Exception:", err);
        alert(err.message);
    });
}

