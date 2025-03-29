document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([24.0, 45.0], 6);
    let markers = {};
    let comparisonData = null;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    function initializeMultiSelects() {
        const multiSelects = document.querySelectorAll('select[multiple]');
        multiSelects.forEach(select => {
            select.setAttribute('size', '4');
            const helpText = document.createElement('small');
            helpText.className = 'form-text text-muted';
            helpText.textContent = 'Click to select/deselect. Select multiple without holding Ctrl.';
            select.parentNode.insertBefore(helpText, select.nextSibling);
            select.addEventListener('mousedown', function(e) {
                e.preventDefault();
                const option = e.target;
                if (option.tagName.toLowerCase() === 'option') {
                    option.selected = !option.selected;
                    const event = new Event('change', { bubbles: true });
                    this.dispatchEvent(event);
                }
            });
        });
    } 

    function populateStationSelects() {
        fetch('/get-station-names')
            .then(response => response.json())
            .then(data => {
                const stationSelect = document.getElementById('stationSelect');
                const predictionStation = document.getElementById('predictionStation');
                const compareStations = document.getElementById('compareStations');
                
                data.stations.forEach(station => {
                    [stationSelect, predictionStation, compareStations].forEach(select => {
                        const option = document.createElement('option');
                        option.value = station;
                        option.textContent = station;
                        select.appendChild(option);
                    });
                });

                if (data.stations.length > 0) {
                    stationSelect.value = data.stations[0];
                    loadStationDetails(data.stations[0]);
                    updatePredictionInputs(data.stations[0]);
                }
                
                initializeMultiSelects();
            });
    }

    function loadMapData() {
        fetch('/map-data')
            .then(response => response.json())
            .then(data => {
                data.forEach(station => {
                    const marker = L.marker([station.latitude, station.longitude], {
                        icon: L.icon({ iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png' })
                    })
                    .addTo(map)
                    .bindPopup(`<b>${station.station_name}</b>`);

                    marker.on('mouseover', () => {
                        marker.setIcon(L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png' }));
                    });
                    marker.on('mouseout', () => {
                        marker.setIcon(L.icon({ iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png' }));
                    });
                    marker.on('click', () => {
                        document.getElementById('stationSelect').value = station.station_name;
                        loadStationDetails(station.station_name);
                    });

                    markers[station.station_name] = marker;
                });
            });
    }

    function loadStationDetails(stationName) {
        fetch(`/station-details?station=${stationName}`)
            .then(response => response.json())
            .then(data => {
                const detailsDiv = document.getElementById('stationDetails');
                detailsDiv.innerHTML = `
                    <p><strong>Station:</strong> ${stationName}</p>
                    <p><strong>Latitude:</strong> ${data.details.latitude}</p>
                    <p><strong>Longitude:</strong> ${data.details.longitude}</p>
                `;

                const paramSelect = document.getElementById('parameterSelect');
                paramSelect.innerHTML = '';
                Object.keys(data.monthly_chart_data.data).forEach(param => {
                    const option = document.createElement('option');
                    option.value = param;
                    option.textContent = param;
                    paramSelect.appendChild(option);
                });
                
                if (paramSelect.options.length > 0) {
                    paramSelect.options[0].selected = true;
                }

                initializeMultiSelects();
                updateMonthlyChart(stationName);
            });
    }

    function updateMonthlyChart(stationName) {
        const selectedParams = Array.from(document.getElementById('parameterSelect').selectedOptions).map(opt => opt.value);
        const year = document.getElementById('mapViewYear')?.value || null;
        
        if (selectedParams.length === 0) {
            document.getElementById('monthlyChart').innerHTML = '<p>Please select at least one parameter</p>';
            return;
        }
        
        const queryParams = new URLSearchParams({
            station: stationName,
            year: year || ''
        });
        
        fetch(`/station-details?${queryParams}`)
            .then(response => response.json())
            .then(data => {
                const months = data.monthly_chart_data.months;
                const yearDisplay = year || new Date(data.details.date).getFullYear();
                
                const traces = selectedParams.map(param => ({
                    x: months,
                    y: data.monthly_chart_data.data[param],
                    type: 'bar',
                    name: param,
                    hoverinfo: 'x+y',
                    marker: {
                        line: {
                            width: 1
                        }
                    }
                }));

                const layout = {
                    title: `Monthly Data for ${stationName} (${yearDisplay})`,
                    barmode: 'group',
                    height: 500,
                    legend: { 
                        orientation: 'h', 
                        y: -0.2,
                        xanchor: 'center',
                        x: 0.5 
                    },
                    xaxis: { title: 'Month' },
                    yaxis: { title: 'Value' },
                    margin: { t: 50, b: 100 }
                };

                Plotly.newPlot('monthlyChart', traces, layout);
            })
            .catch(error => {
                console.error('Error updating monthly chart:', error);
                document.getElementById('monthlyChart').innerHTML = '<p>Error loading chart data</p>';
            });
    }

    function loadStationComparison() {
        const selectedStations = Array.from(document.getElementById('compareStations').selectedOptions).map(opt => opt.value);
        const selectedParams = Array.from(document.getElementById('compareParams').selectedOptions).map(opt => opt.value);
        const year = document.getElementById('comparisonYear')?.value || null;

        if (selectedStations.length === 0 || selectedParams.length === 0) {
            document.getElementById('comparisonCharts').innerHTML = '<p>Please select stations and parameters</p>';
            return;
        }

        fetch('/station-comparison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stations: selectedStations, params: selectedParams, year: year })
        })
        .then(response => response.json())
        .then(data => {
            comparisonData = data;
            const chartsDiv = document.getElementById('comparisonCharts');
            chartsDiv.innerHTML = '';

            selectedParams.forEach(param => {
                const traces = selectedStations.map(station => ({
                    x: data.dates[station],
                    y: data.values[station][param],
                    type: 'scatter',
                    mode: 'lines',
                    name: station
                }));

                const div = document.createElement('div');
                div.id = `chart-${param}`;
                chartsDiv.appendChild(div);

                Plotly.newPlot(`chart-${param}`, traces, {
                    title: `${param} Comparison Across Stations`,
                    xaxis: { title: 'Date' },
                    yaxis: { title: param }
                });
            });

            updateSummaryTable();
        });
    }

    function updateSummaryTable() {
        if (!comparisonData) return;
        
        const selectedStations = Array.from(document.getElementById('compareStations').selectedOptions).map(opt => opt.value);
        const summaryParam = document.getElementById('summaryParam').value;
        const statsTable = document.getElementById('summaryStats');
        
        let tableHtml = `<table class="summary-table"><thead><tr><th>Station</th><th>${summaryParam} Mean</th><th>${summaryParam} Min</th><th>${summaryParam} Max</th><th>${summaryParam} Std</th></tr></thead><tbody>`;

        selectedStations.forEach(station => {
            tableHtml += `<tr><td>${station}</td>`;
            ['mean', 'min', 'max', 'std'].forEach(stat => {
                const key = `${summaryParam}_${stat}`;
                const value = comparisonData.summary_stats[key]?.[station];
                tableHtml += `<td>${value !== undefined && value !== null ? value : 'N/A'}</td>`;
            });
            tableHtml += '</tr>';
        });

        tableHtml += '</tbody></table>';
        statsTable.innerHTML = tableHtml;
    }

    fetch('/data-analysis')
        .then(response => response.json())
        .then(data => {
            const paramSelect = document.getElementById('compareParams');
            const summaryParamSelect = document.getElementById('summaryParam');
            Object.keys(data.summary_stats).filter(key => key.endsWith('_mean')).forEach(key => {
                const param = key.replace('_mean', '');
                [paramSelect, summaryParamSelect].forEach(select => {
                    const option = document.createElement('option');
                    option.value = param;
                    option.textContent = param;
                    select.appendChild(option);
                });
            });
            
            if (paramSelect.options.length > 0) {
                paramSelect.options[0].selected = true;
            }
            if (summaryParamSelect.options.length > 0) {
                summaryParamSelect.options[0].selected = true;
            }
            
            initializeMultiSelects();
        });

    document.getElementById('predictionForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const predictionData = {
            'Station_Name': document.getElementById('predictionStation').value,
            'Air Temperature (C°)': document.getElementById('temperature').value,
            'Wind Speed at 3m (m/s)': document.getElementById('wind_speed').value,
            'DHI (Wh/m2)': document.getElementById('dhi').value,
            'DNI (Wh/m2)': document.getElementById('dni').value,
            'Relative Humidity (%)': document.getElementById('humidity').value,
            'Barometric Pressure (mB (hPa equiv))': document.getElementById('pressure').value
        };

        fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(predictionData)
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('predictionResult').innerHTML = data.prediction
                ? `<div class="alert alert-success">Predicted GHI: ${data.prediction.toFixed(2)} Wh/m²</div>`
                : `<div class="alert alert-danger">Prediction Error: ${data.error}</div>`;
        });
    });

    document.getElementById('stationSelect').addEventListener('change', (e) => loadStationDetails(e.target.value));
    document.getElementById('parameterSelect').addEventListener('change', () => updateMonthlyChart(document.getElementById('stationSelect').value));
    document.getElementById('mapViewYear').addEventListener('change', () => updateMonthlyChart(document.getElementById('stationSelect').value));
    document.getElementById('predictionStation').addEventListener('change', (e) => updatePredictionInputs(e.target.value));
    document.getElementById('compareStations').addEventListener('change', loadStationComparison);
    document.getElementById('compareParams').addEventListener('change', loadStationComparison);
    document.getElementById('comparisonYear').addEventListener('change', loadStationComparison);
    document.getElementById('summaryParam').addEventListener('change', updateSummaryTable);

    populateStationSelects();
    loadMapData();

    function updatePredictionInputs(stationName) {
        fetch(`/station-details?station=${stationName}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('temperature').value = data.mean_values['Air Temperature (C°)'];
                document.getElementById('wind_speed').value = data.mean_values['Wind Speed at 3m (m/s)'];
                document.getElementById('dhi').value = data.mean_values['DHI (Wh/m2)'];
                document.getElementById('dni').value = data.mean_values['DNI (Wh/m2)'];
                document.getElementById('humidity').value = data.mean_values['Relative Humidity (%)'];
                document.getElementById('pressure').value = data.mean_values['Barometric Pressure (mB (hPa equiv))'];
            });
    }
});