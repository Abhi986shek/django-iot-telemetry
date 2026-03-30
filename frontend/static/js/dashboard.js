async function loadMachineTable() {
    const tbody = document.getElementById('machine-table-body');
    if (!tbody) return;

    try {
        const response = await fetch('/api/machines/');
        const data = await response.json();

        if (!data.machines || data.machines.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No machines registered yet.</td></tr>';
            return;
        }

        tbody.innerHTML = data.machines.map(machine => `
            <tr>
                <td><strong>${machine.machine_id}</strong></td>
                <td>${machine.location}</td>
                <td>${new Date(machine.registered_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-secondary"
                        onclick="loadTelemetryChart('${machine.machine_id}')">
                        View Data
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4">Failed to load machine list.</td></tr>`;
        console.error('Machine list error:', err);
    }
}

async function loadTelemetryChart(machineId) {
    const section = document.getElementById('telemetry-section');
    const label = document.getElementById('selected-machine-label');
    if (!section || !label) return;

    label.textContent = machineId;
    section.style.display = 'block';

    try {
        const response = await fetch(`/api/telemetry/${machineId}/?limit=100`);
        const data = await response.json();

        if (!data.records || data.records.length === 0) {
            document.getElementById('telemetry-chart').getContext('2d').clearRect(0, 0, 9999, 9999);
            return;
        }

        renderChart(data.records);
    } catch (err) {
        console.error('Telemetry fetch error:', err);
    }
}

function renderChart(records) {
    const canvas = document.getElementById('telemetry-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = records.map((_, i) => i + 1);
    const rpmData = records.map(r => r.rpm || 0);
    const vibData = records.map(r => r.vibration || 0);

    const width = canvas.clientWidth || 800;
    const height = canvas.clientHeight || 200;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);

    const maxVal = Math.max(...rpmData, ...vibData, 1);
    const padX = 40, padY = 20;
    const plotW = width - padX * 2;
    const plotH = height - padY * 2;

    function toX(i) { return padX + (i / (labels.length - 1)) * plotW; }
    function toY(val) { return padY + plotH - (val / maxVal) * plotH; }

    function drawLine(dataset, color) {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        dataset.forEach((val, i) => {
            if (i === 0) ctx.moveTo(toX(i), toY(val));
            else ctx.lineTo(toX(i), toY(val));
        });
        ctx.stroke();
    }

    drawLine(rpmData, '#4f6ef7');
    drawLine(vibData, '#22c55e');

    // Legend
    ctx.font = '12px Inter, sans-serif';
    ctx.fillStyle = '#4f6ef7';
    ctx.fillRect(padX, 4, 12, 12);
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText('RPM', padX + 16, 14);
    ctx.fillStyle = '#22c55e';
    ctx.fillRect(padX + 60, 4, 12, 12);
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText('Vibration', padX + 76, 14);
}
