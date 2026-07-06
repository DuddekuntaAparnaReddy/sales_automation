async function loadDashboardStats() {
    try {
        const response = await fetch("http://127.0.0.1:8000/dashboard-stats");
        const data = await response.json();

        document.getElementById("total-leads").innerText = data.leads;
        document.getElementById("total-campaigns").innerText = data.campaigns;
        document.getElementById("total-users").innerText = data.users;

        if (document.getElementById("hot-leads")) {
            document.getElementById("hot-leads").innerText = data.hot_leads || 0;
        }
        if (document.getElementById("warm-leads")) {
            document.getElementById("warm-leads").innerText = data.warm_leads || 0;
        }
        if (document.getElementById("cold-leads")) {
            document.getElementById("cold-leads").innerText = data.cold_leads || 0;
        }
    } catch(error) {
        console.log(error);
    }
}

loadDashboardStats();