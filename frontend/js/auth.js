// frontend/js/auth.js
// Authentication state management
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

function saveUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function isLoggedIn() {
    return !!getToken();
}

function logout() {
    removeToken();
    window.location.href = '/login.html';
}

// Auto-redirect if not logged in on dashboard
if (window.location.pathname.includes('dashboard') && !isLoggedIn()) {
    window.location.href = '/login.html';
}