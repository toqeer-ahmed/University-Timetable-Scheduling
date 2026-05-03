document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const loader = document.querySelector('.loader');
    const btnText = document.querySelector('.btn-text');
    const resultsSection = document.getElementById('results-section');
    
    // Elements for metrics
    const metricHc = document.getElementById('metric-hc');
    const metricSp = document.getElementById('metric-sp');
    const metricFit = document.getElementById('metric-fit');

    // Filters and Table
    const viewSelect = document.getElementById('view-select');
    const entityLabel = document.getElementById('entity-label');
    const entitySelect = document.getElementById('entity-select');
    const colDynamic = document.getElementById('col-dynamic');
    const tbody = document.getElementById('timetable-body');

    let fullData = [];
    let currentView = 'group';

    generateBtn.addEventListener('click', async () => {
        const generations = document.getElementById('generations').value;
        const population = document.getElementById('population').value;

        // UI Loading State
        generateBtn.disabled = true;
        loader.classList.remove('hidden');
        btnText.textContent = "Running AI (may take ~10-30s)...";
        resultsSection.classList.add('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ generations, population })
            });

            const data = await response.json();
            
            if(data.status === 'success') {
                // Update Metrics
                metricHc.textContent = data.metrics.hard_conflicts;
                metricSp.textContent = data.metrics.soft_penalty;
                metricFit.textContent = data.metrics.fitness.toFixed(6);

                fullData = data.timetable;
                
                // Initialize View
                updateEntityDropdown();
                renderTable();

                // Show Results
                resultsSection.classList.remove('hidden');
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error generating timetable:', error);
            alert("An error occurred while generating the timetable.");
        } finally {
            generateBtn.disabled = false;
            loader.classList.add('hidden');
            btnText.textContent = "Generate Timetable";
        }
    });

    viewSelect.addEventListener('change', (e) => {
        currentView = e.target.value;
        
        if(currentView === 'group') {
            entityLabel.textContent = "Select Group:";
            colDynamic.textContent = "Teacher / Room";
        } else if(currentView === 'teacher') {
            entityLabel.textContent = "Select Teacher:";
            colDynamic.textContent = "Group / Room";
        } else {
            entityLabel.textContent = "Select Room:";
            colDynamic.textContent = "Group / Teacher";
        }
        
        updateEntityDropdown();
        renderTable();
    });

    entitySelect.addEventListener('change', renderTable);

    function updateEntityDropdown() {
        const uniqueEntities = new Set();
        
        fullData.forEach(row => {
            if(currentView === 'group') uniqueEntities.add(row.group);
            else if(currentView === 'teacher') {
                // teachers string might contain multiple separated by comma
                row.teachers.split(',').forEach(t => uniqueEntities.add(t.trim()));
            }
            else uniqueEntities.add(row.room);
        });

        const sorted = Array.from(uniqueEntities).sort();
        
        entitySelect.innerHTML = '';
        sorted.forEach(entity => {
            const option = document.createElement('option');
            option.value = entity;
            option.textContent = entity;
            entitySelect.appendChild(option);
        });
    }

    function renderTable() {
        const selectedEntity = entitySelect.value;
        if(!selectedEntity) return;

        let filteredData = fullData.filter(row => {
            if(currentView === 'group') return row.group === selectedEntity;
            if(currentView === 'teacher') return row.teachers.includes(selectedEntity);
            if(currentView === 'room') return row.room === selectedEntity;
            return false;
        });

        tbody.innerHTML = '';
        
        if(filteredData.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No sessions found.</td></tr>`;
            return;
        }

        filteredData.forEach(row => {
            const tr = document.createElement('tr');
            
            let dynamicCell = '';
            if(currentView === 'group') {
                dynamicCell = `<div style="font-size:0.9em;color:#93c5fd">${row.teachers}</div><div style="font-size:0.85em;color:#cbd5e1">${row.room}</div>`;
            } else if(currentView === 'teacher') {
                dynamicCell = `<div style="font-size:0.9em;color:#fcd34d">${row.group}</div><div style="font-size:0.85em;color:#cbd5e1">${row.room}</div>`;
            } else {
                dynamicCell = `<div style="font-size:0.9em;color:#fcd34d">${row.group}</div><div style="font-size:0.85em;color:#93c5fd">${row.teachers}</div>`;
            }

            const typeBadge = `<span class="badge ${row.type.toLowerCase()}">${row.type}</span>`;

            tr.innerHTML = `
                <td><strong>${row.day}</strong></td>
                <td style="color:#cbd5e1">${row.start_time} - ${row.end_time}</td>
                <td style="font-weight:600">${row.course}</td>
                <td>${typeBadge}</td>
                <td>${dynamicCell}</td>
            `;
            tbody.appendChild(tr);
        });
    }
});
