// frontend/js/auth.js
function getToken() { return localStorage.getItem('token'); }
function setToken(token) { localStorage.setItem('token', token); }
function removeToken() { localStorage.removeItem('token'); localStorage.removeItem('user'); }
function saveUser(user) { localStorage.setItem('user', JSON.stringify(user)); }
function getUser() { return JSON.parse(localStorage.getItem('user') || 'null'); }
function isLoggedIn() { return !!getToken(); }
function logout() { removeToken(); window.location.href = '/login.html'; }
if (window.location.pathname.includes('dashboard') && !isLoggedIn()) {
    window.location.href = '/login.html';
}