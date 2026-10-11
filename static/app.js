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
    rebuildClientDropdownList();
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
    synchronizeActiveClientRecord();
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
function triggerAddClient() {
    const name = prompt("Enter client name:");
    if (!name || name.trim() === "") return;

    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');
    if (clients[name]) {
        alert(`Client data object [${name}] already initialized.`);
        return;
    }

    clients[name] = {
        id: Date.now(),
        name: name,
        age: 0, height: 0.0, weight: 0.0,
        program: "None Assigned", calories: 2000,
        target_weight: 0.0, target_adherence: 80,
        status: "Active", end: "2027-12-31"
    };
    localStorage.setItem('db_clients', JSON.stringify(clients));

    const progress = JSON.parse(localStorage.getItem('db_progress') || '{}');
    progress[name] = [{ week: "Wk 1", val: 75 }];
    localStorage.setItem('db_progress', JSON.stringify(progress));

    const workouts = JSON.parse(localStorage.getItem('db_workouts') || '{}');
    workouts[name] = [];
    localStorage.setItem('db_workouts', JSON.stringify(workouts));

    currentActiveClient = name;
    rebuildClientDropdownList();
    synchronizeActiveClientRecord();
    alert(`Client ${name} saved successfully.`);
}

/**
 * Uses a basic randomization loop to emulate the original script's automated assignment logic.
 */
function triggerAIGenerator() {
    if (!currentActiveClient) return alert("Select a client first");
    const keys = Object.keys(AI_PROGRAM_TEMPLATES);
    const randomType = keys[Math.floor(Math.random() * keys.length)];
    const list = AI_PROGRAM_TEMPLATES[randomType];
    const chosenDetail = list[Math.floor(Math.random() * list.length)];

    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');
    clients[currentActiveClient].program = chosenDetail;
    localStorage.setItem('db_clients', JSON.stringify(clients));

    alert(`Program Generated for ${currentActiveClient}: ${chosenDetail}`);
    synchronizeActiveClientRecord();
}

/**
 * Emulates the original report builder pipeline.
 */
function triggerPDFReport() {
    if (!currentActiveClient) return alert("Select a client first");
    alert(`PDF Structural Serialization complete:\n"${currentActiveClient}_report.pdf" created successfully.`);
}

/**
 * Reads profile timelines to return target subscription values.
 */
function triggerMembershipCheck() {
    if (!currentActiveClient) return alert("Select a client first");
    const clients = JSON.parse(localStorage.getItem('db_clients') || '{}');
    const data = clients[currentActiveClient];
    alert(`Membership: ${data.status}\nRenewal Date: ${data.end || 'N/A'}`);
}

/**
 * Re-renders the rows inside the workout table.
 */
function renderWorkoutLedgerTable() {
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
    const dateVal = document.getElementById('modal-workout-date').value;
    const typeVal = document.getElementById('modal-workout-type').value;
    const durVal = parseInt(document.getElementById('modal-workout-duration').value) || 60;
    const notesVal = document.getElementById('modal-workout-notes').value || "N/A";

    const workouts = JSON.parse(localStorage.getItem('db_workouts') || '{}');
    if (!workouts[currentActiveClient]) workouts[currentActiveClient] = [];

    workouts[currentActiveClient].unshift({ date: dateVal, type: typeVal, duration: durVal, notes: notesVal });
    localStorage.setItem('db_workouts', JSON.stringify(workouts));

    closeModalWindow('workout-modal');
    renderWorkoutLedgerTable();
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
});