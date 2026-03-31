/* ==================== HEADER NAVIGATION ==================== */

document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-link');

    // Hamburger toggle
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }

    // Close menu when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            hamburger?.classList.remove('active');
            navMenu?.classList.remove('active');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        const isClickInsideNav = hamburger?.contains(event.target) || navMenu?.contains(event.target);
        if (!isClickInsideNav && navMenu && navMenu.classList.contains('active')) {
            hamburger?.classList.remove('active');
            navMenu.classList.remove('active');
        }
    });
});
