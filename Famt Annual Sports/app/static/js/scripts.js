// Real-time updates for rankings
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('rankingsChart')) {
        const socket = io();
        socket.on('rankings_updated', (data) => {
            updateChart(data);  // Custom function to refresh chart
        });
    }
});

// Game card click handler
document.querySelectorAll('.game-card').forEach(card => {
    card.addEventListener('click', (e) => {
        if (!e.target.closest('a')) {
            window.location = card.dataset.url;
        }
    });
});