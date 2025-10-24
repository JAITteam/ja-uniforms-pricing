/* ============================================
   MODERN NAVBAR JAVASCRIPT
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== USER MENU DROPDOWN =====
    const userMenuButton = document.getElementById('userMenuButton');
    const userMenu = userMenuButton?.closest('.user-menu');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenuButton && userMenu) {
        // Toggle dropdown on button click
        userMenuButton.addEventListener('click', function(e) {
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (userMenu && !userMenu.contains(e.target)) {
                userMenu.classList.remove('active');
            }
        });
        
        // Close dropdown when clicking on a menu item
        if (userDropdown) {
            const dropdownItems = userDropdown.querySelectorAll('.dropdown-item');
            dropdownItems.forEach(item => {
                item.addEventListener('click', function() {
                    userMenu.classList.remove('active');
                });
            });
        }
    }
    
    // ===== MOBILE MENU =====
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    
    // Open mobile menu
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenuOverlay?.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        });
    }
    
    // Close mobile menu
    function closeMobileMenu() {
        mobileMenuOverlay?.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }
    
    if (mobileMenuClose) {
        mobileMenuClose.addEventListener('click', closeMobileMenu);
    }
    
    // Close when clicking overlay
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function(e) {
            if (e.target === mobileMenuOverlay) {
                closeMobileMenu();
            }
        });
    }
    
    // Close mobile menu when clicking on a menu item
    const mobileMenuItems = document.querySelectorAll('.mobile-menu-item');
    mobileMenuItems.forEach(item => {
        item.addEventListener('click', closeMobileMenu);
    });
    
    // ===== ACTIVE PAGE HIGHLIGHT =====
    // Get current path
    const currentPath = window.location.pathname;
    
    // Highlight active nav link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        
        // Exact match for home
        if (currentPath === '/' && linkPath === '/') {
            link.classList.add('active');
        }
        // Partial match for other pages
        else if (currentPath !== '/' && currentPath.startsWith(linkPath) && linkPath !== '/') {
            link.classList.add('active');
        }
    });
    
    // ===== SMOOTH SCROLL TO TOP =====
    const logoLink = document.querySelector('.navbar-logo');
    if (logoLink) {
        logoLink.addEventListener('click', function(e) {
            if (window.location.pathname === '/') {
                e.preventDefault();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
        });
    }
    
    // ===== NAVBAR SHADOW ON SCROLL =====
    const navbar = document.querySelector('.modern-navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.08)';
            }
        });
    }
    
    // ===== KEYBOARD NAVIGATION =====
    // Close dropdowns on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close user menu
            if (userMenu) {
                userMenu.classList.remove('active');
            }
            // Close mobile menu
            if (mobileMenuOverlay?.classList.contains('active')) {
                closeMobileMenu();
            }
        }
    });
    
    console.log('✅ Modern navbar initialized');
});

// ===== PREVENT LOGOUT CONFIRMATION (Optional) =====
// Uncomment if you want to add a confirmation dialog for logout
/*
document.addEventListener('DOMContentLoaded', function() {
    const logoutLinks = document.querySelectorAll('a[href="/logout"]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });
});
*/