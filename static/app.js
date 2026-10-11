let currentClient = null;
let chartInstance = null;
let loadedPrograms = {}; // Renamed from duplicate reference tracking name to prevent compilation crash

const PROGRAMS = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"}
};

document.addEventListener("DOMContentLoaded", function() {
    refreshClientList();
    loadProgramsFromApi();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById('tab-' + tabId).style.display = 'block';

    const btnSummary = document.getElementById('btn-summary');
    const btnAnalytics = document.getElementById('btn-analytics');

    if (tabId === 'summary') {
        btnSummary.style.background = '#222'; btnSummary.style.color = '#d4af37'; btnSummary.style.borderBottom = '3px solid #d4af37';
        btnAnalytics.style.background = '#111'; btnAnalytics.style.color = '#888'; btnAnalytics.style.borderBottom = '3px solid transparent';
    } else {
        btnAnalytics.style.background = '#222'; btnAnalytics.style.color = '#d4af37'; btnAnalytics.style.borderBottom = '3px solid #d4af37';
        btnSummary.style.background = '#111'; btnSummary.style.color = '#888'; btnSummary.style.borderBottom = '3px solid transparent';
    }
}

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

function loadProgramsFromApi() {
    fetch('/api/programs', { method: 'GET' })
    .then(res => {
        if (!res.ok) throw new Error("Backend program definitions sync failure");
        return res.json();
    })
    .then(data => {
        const combobox = document.getElementById("my-combobox");
        combobox.innerHTML = '<option value="" disabled selected>-- Select a program --</option>';

        const programList = data.programs || data;

        programList.forEach(program => {
            const option = document.createElement("option");
            option.value = program;
            option.textContent = program;
            combobox.appendChild(option);
        });
    })
    .catch(err => console.error("API error loading fitness modules:", err));
}

function onClientSelected(name) {
    if (!name) return;
    document.getElementById("client-name").value = name;
    loadClient();
}

function saveClient() {
    const name = document.getElementById("client-name").value.trim();
    const program = document.getElementById("my-combobox").value;
    const ageInput = document.getElementById("client-age").value;
    const heightInput = document.getElementById("client-height").value;
    const weightInput = document.getElementById("client-weight").value;
    const targetWeight = document.getElementById("target-weight").value;
    const targetAdherence = document.getElementById("target-adherence").value;

    if (!name || !program) {
        alert("Please fill client name and program selection targets.");
        return;
    }

    try {
        const payload = {
            name: name,
            age: parseInt(ageInput) || 0,
            height: parseFloat(heightInput) || 0.0,
            weight: parseFloat(weightInput) || 0.0,
            program: program,
            target_weight: parseFloat(targetWeight) || 0.0,
            target_adherence: parseInt(targetAdherence) || 0
        };

        fetch('/api/client', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || "Server validation rejected parameters"); });
            }
            return response.json();
        })
        .then(data => {
            alert(data.message || "Client saved successfully!");
            currentClient = name;
            refreshClientList();
            refreshSummary();
        })
        .catch(error => alert(`Error: ${error.message}`));

    } catch (e) {
        alert("Application Execution Intercept Error: " + (e.message || e));
    }
}

function loadClient() {
    const name = document.getElementById("client-name").value.trim();
    if (!name) { alert("Enter or select client name first."); return; }

    fetch('/api/client?name=' + encodeURIComponent(name))
    .then(res => {
        if (!res.ok) throw new Error("Client tracking structure not found.");
        return res.json();
    })
    .then(data => {
        const profile = data["CLIENT PROFILE"] || data;
        currentClient = profile.name;

        document.getElementById("client-name").value = profile.name || "";
        document.getElementById("client-age").value = profile.age || 0;
        document.getElementById("client-height").value = parseFloat(profile.height) || 0.0;
        document.getElementById("client-weight").value = parseFloat(profile.weight) || 0.0;
        document.getElementById("my-combobox").value = profile.program || "";
        document.getElementById("target-weight").value = profile.target_weight || 0.0;
        document.getElementById("target-adherence").value = profile.target_adherence || 0;
        document.getElementById("client-selector").value = profile.name;

        // Process custom response format blocks cleanly to downstream output renders
        let formattedText = `CLIENT PROFILE\n--------------\n`;
        formattedText += `Name     : ${profile.name}\n`;
        formattedText += `Age      : ${profile.age || '-'}\n`;
        formattedText += `Height   : ${profile.height || '-'}\n`;
        formattedText += `Weight   : ${profile.weight || '-'}\n`;
        formattedText += `Program  : ${profile.program}\n`;
        formattedText += `Calories : ${profile.calories || '-'}\n\n`;

        formattedText += `PROGRAM NOTES\n-------------\n${data["PROGRAM NOTES"]?.description || ''}\n\n`;
        formattedText += `GOALS\n-----\n${data["GOALS"]?.summary || 'None'}\n\n`;
        formattedText += `PROGRESS SUMMARY\n----------------\nWeeks logged : ${data["PROGRESS SUMMARY"]?.["Weeks logged"] || 0}\nAverage adherence : ${data["PROGRESS SUMMARY"]?.["Average adherence"] || '0%'}\n\n`;
        formattedText += `LAST BODY METRICS\n-----------------\n${data["LAST BODY METRICS"]?.summary || 'None'}`;

        document.getElementById("work-label").innerText = formattedText;
        loadWorkoutHistory();
    })
    .catch(err => alert(err.message));
}

function refreshSummary() {
    if (currentClient) loadClient();
}

function saveProgress() {
    if (!currentClient) { alert("Load a valid client first."); return; }
    const adherence = parseInt(document.getElementById("adherence-slider").value);

    fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: currentClient, adherence: adherence })
    })
    .then(res => res.json())
    .then(data => {
        alert("Weekly progress logged successfully!");
        refreshSummary();
    });
}

function loadWorkoutHistory() {
    if (!currentClient) return;
    fetch('/api/workout?name=' + encodeURIComponent(currentClient))
    .then(res => res.json())
    .then(data => {
        const tbody = document.querySelector("#workout-history-table tbody");
        tbody.innerHTML = "";
        const history = data["workout_history"] || data;
        if (!history || history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding: 8px; text-align: center;">No history logs loaded</td></tr>';
            return;
        }
        history.forEach(w => {
            let row = `<tr>
                <td style="padding:8px; border-bottom:1px solid #333;">${w[0] || w.date}</td>
                <td style="padding:8px; border-bottom:1px solid #333;">${w[1] || w.workout_type}</td>
                <td style="padding:8px; border-bottom:1px solid #333; text-align:center;">${w[2] || w.duration_min}</td>
                <td style="padding:8px; border-bottom:1px solid #333;">${w[3] || w.notes || ''}</td>
            </tr>`;
            tbody.innerHTML += row;
        });
    });
}

function openLogWorkoutModal() {
    if (!currentClient) { alert("Select a client first."); return; }
    document.getElementById("workout-modal").style.display = "flex";
}

function submitWorkout() {
    const payload = {
        name: currentClient,
        workout: document.getElementById("modal-w-type").value,
        duration: parseInt(document.getElementById("modal-w-dur").value) || 60,
        notes: document.getElementById("modal-w-notes").value,
        ex_name: document.getElementById("modal-w-ex-name").value,
        ex_sets: parseInt(document.getElementById("modal-w-sets").value) || 0,
        ex_reps: parseInt(document.getElementById("modal-w-reps").value) || 0,
        ex_weight: parseFloat(document.getElementById("modal-w-weight").value) || 0.0
        };
        fetch('/api/workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
        }).then(() => {
        alert("Workout successfully saved.");
        document.getElementById("workout-modal").style.display = "none";
        loadWorkoutHistory();
        });
        }
        function openLogMetricsModal() {
        if (!currentClient) { alert("Select a client first."); return; }
        document.getElementById("modal-m-weight").value = parseFloat(document.getElementById("client-weight").value) || 0.0;
        document.getElementById("metrics-modal").style.display = "flex";
        }
        function submitMetrics() {
        const payload = {
        name: currentClient,
        date: new Date().toISOString().split('T')[0],
        weight: parseFloat(document.getElementById("modal-m-weight").value) || 0,
        waist: parseFloat(document.getElementById("modal-m-waist").value) || 0,
        body_fat: parseFloat(document.getElementById("modal-m-bf").value) || 0
        };
        fetch('/api/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
        }).then(() => {
        alert("Metrics logged safely.");
        document.getElementById("metrics-modal").style.display = "none";
        refreshSummary();
        });
        }
        function initChartContext(title, type, labels, data, labelName, color) {
    if (chartInstance) chartInstance.destroy();
    document.getElementById("chart-title").innerText = title;

    const ctx = document.getElementById('analyticsChart').getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: labelName,
                data: data,
                borderColor: '#1d4ed8', // Sharp blue data trajectory matching image plot lines
                backgroundColor: '#1d4ed8',
                borderWidth: 2,
                pointBackgroundColor: '#1d4ed8',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5,
                pointRadius: 5,
                tension: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: '#000000', // Clear black values text over white background
                        font: { size: 12, family: 'sans-serif' }
                    },
                    grid: {
                        color: '#cccccc', // Structured chart matrix dividers
                        drawBorder: true
                    },
                    title: {
                        display: true,
                        text: labelName, // Automatically binds tracking context metrics title
                        color: '#000000',
                        font: { size: 13, weight: 'bold' }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        color: '#000000', // High contrast timeline labels
                        font: { size: 12, family: 'sans-serif' }
                    },
                    grid: {
                        color: '#cccccc',
                        drawOnChartArea: true
                    },
                    title: {
                        display: true,
                        text: 'Week',
                        color: '#000000',
                        font: { size: 13, weight: 'bold' }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

        function renderAdherenceChart() {
        if (!currentClient) return;
        fetch('/api/progress?name=' + encodeURIComponent(currentClient))
        .then(res => res.json())
        .then(data => {
        const history = data.progress || [];
        const weeks = history.map(h => h.week);
        const adherence = history.map(h => h.adherence);
        initChartContext("Weekly Adherence – " + currentClient, 'line', weeks, adherence, 'Adherence (%)', '#d4af37');
        });
        }
        function renderWeightChart() {
        if (!currentClient) return;
        fetch('/api/weight?name=' + encodeURIComponent(currentClient))
        .then(res => res.json())
        .then(data => {
        const history = data.weight_chart || [];
        const dates = history.map(h => h[0] || h.date);
        const weights = history.map(h => h[1] || h.weight);
        initChartContext("Weight Trend – " + currentClient, 'line', dates, weights, 'Weight (kg)', '#ff9800');
        });
        }
        function showBMIInfo() {
        if (!currentClient) return;
        fetch('/api/bmi?name=' + encodeURIComponent(currentClient))
        .then(res => res.json())
        .then(data => {
        alert(data["BMI Info"] || data.error);
        });
        }
