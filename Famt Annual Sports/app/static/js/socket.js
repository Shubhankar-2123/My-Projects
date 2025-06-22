document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    socket.on('rankings_updated', (data) => {
        // Update your UI here
        document.getElementById('leaderboard').innerHTML = 
            data.map(team => `<li>${team.name}: ${team.points}</li>`).join('');
    });
    
    // Example of emitting from client
    document.getElementById('refresh-btn').addEventListener('click', () => {
        socket.emit('request_update');
    });
});