/**
 * Hansard Tales - Main JavaScript
 * Handles mobile navigation and interactive features
 */

(function () {
    'use strict';

    /**
     * Initialize mobile navigation toggle
     */
    function initMobileNav() {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');

        if (!navToggle || !navMenu) {
            return;
        }

        // Toggle mobile menu
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('hidden');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (event) {
            const isClickInside = navToggle.contains(event.target) || navMenu.contains(event.target);
            if (!isClickInside && !navMenu.classList.contains('hidden')) {
                navMenu.classList.add('hidden');
            }
        });

        // Close menu on escape key
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !navMenu.classList.contains('hidden')) {
                navMenu.classList.add('hidden');
            }
        });

        // Close menu when window is resized to desktop size
        window.addEventListener('resize', function () {
            if (window.innerWidth >= 1024) {
                navMenu.classList.add('hidden');
            }
        });
    }

    /**
     * Initialize smooth scroll for anchor links
     */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Initialize all features when DOM is ready
     */
    function init() {
        initMobileNav();
        initSmoothScroll();
    }

    // Run initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
