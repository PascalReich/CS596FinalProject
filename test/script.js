// script.js

// CloudFront JSON endpoint for data
const API_DATA = 'https://d9qj1hm6ouyqd.cloudfront.net/api/data';
const historyBody = document.getElementById('history-body');

// format "YYYY-MM-DD HH:mm" to string
function formatTS(ts) {
    return new Date(ts.replace(' ', 'T')).toLocaleString();
}

// fetches latest measured & forecasted and prepends to history table
async function fetchWeather() {
    try {
        const res = await fetch(API_DATA);
        if (!res.ok) throw new Error(res.statusText);
        const { measured: m, forecasted: f } = await res.json();

        historyBody.insertAdjacentHTML('afterbegin', `
      <tr>
        <td>${formatTS(m.time)}</td>
        <td>${m.temperature.toFixed(1)}°</td>
        <td>${m.humidity.toFixed(1)}%</td>
        <td>${formatTS(f.time)}</td>
        <td>${f.temperature.toFixed(1)}°</td>
        <td>${f.humidity.toFixed(1)}%</td>
      </tr>
    `);
    } catch (err) {
        console.error('Weather fetch error:', err);
    }
}

//initial load, refreshes every 5 minutes
fetchWeather();
setInterval(fetchWeather, 5 * 60 * 1000);
