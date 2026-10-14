/**
 * 護國 評論集 - Interactive EBook Web Reader
 * Author: 杜信龍 (Tō͘ Sìn-Liông)
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.book-section');
    const content = document.getElementById('main-content');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const menuToggle = document.getElementById('menu-toggle');
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const catTabs = document.querySelectorAll('.cat-tab');
    const progressBar = document.getElementById('read-progress-bar');
    const backToTopBtn = document.getElementById('back-to-top');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const fontIncBtn = document.getElementById('font-increase-btn');
    const fontDecBtn = document.getElementById('font-decrease-btn');

    let currentCategory = 'all';
    let currentSearchTerm = '';
    let currentSectionId = 'section-0';

    // -------------------------------------------------------------
    // Section Activation Logic
    // -------------------------------------------------------------
    window.activateSection = function(targetId) {
        if (!targetId) return;
        const targetSection = document.getElementById(targetId);
        if (!targetSection) return;

        // Update active section
        sections.forEach(sec => sec.classList.remove('active'));
        targetSection.classList.add('active');
        currentSectionId = targetId;

        // Update active nav item
        navItems.forEach(item => item.classList.remove('active'));
        const targetNav = document.querySelector(`.nav-item[data-target="${targetId}"]`);
        if (targetNav) {
            targetNav.classList.add('active');
            // Scroll nav item into view inside sidebar
            targetNav.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }

        // Scroll content container to top
        if (content) {
            content.scrollTop = 0;
        }

        // Update URL hash safely without reload
        if (window.location.hash !== `#${targetId}`) {
            history.pushState(null, null, `#${targetId}`);
        }

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            closeSidebar();
        }
    };

    // Nav Item Click Listeners
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.getAttribute('data-target');
            activateSection(targetId);
        });
    });

    // Hash Change Listener (Back / Forward Navigation)
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '');
        if (hash) {
            activateSection(hash);
        }
    });

    // -------------------------------------------------------------
    // Mobile Sidebar Drawer
    // -------------------------------------------------------------
    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (menuToggle) menuToggle.addEventListener('click', openSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // -------------------------------------------------------------
    // Search & Category Filtering
    // -------------------------------------------------------------
    function filterNavItems() {
        const term = currentSearchTerm.trim().toLowerCase();

        navItems.forEach(item => {
            const itemCat = item.getAttribute('data-category');
            const searchData = item.getAttribute('data-search') || '';

            const matchesCat = (currentCategory === 'all') || (itemCat === currentCategory);
            const matchesSearch = (term === '') || (searchData.includes(term));

            if (matchesCat && matchesSearch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearchTerm = e.target.value;
            if (searchClearBtn) {
                searchClearBtn.style.display = currentSearchTerm ? 'block' : 'none';
            }
            filterNavItems();
        });
    }

    if (searchClearBtn) {
        searchClearBtn.addEventListener('click', () => {
            searchInput.value = '';
            currentSearchTerm = '';
            searchClearBtn.style.display = 'none';
            filterNavItems();
            searchInput.focus();
        });
    }

    catTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            catTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.getAttribute('data-cat');
            filterNavItems();
        });
    });

    // -------------------------------------------------------------
    // Reading Progress & Back to Top
    // -------------------------------------------------------------
    if (content) {
        content.addEventListener('scroll', () => {
            const scrollTop = content.scrollTop;
            const scrollHeight = content.scrollHeight - content.clientHeight;
            const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
            
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }

            if (backToTopBtn) {
                if (scrollTop > 350) {
                    backToTopBtn.style.display = 'flex';
                } else {
                    backToTopBtn.style.display = 'none';
                }
            }
        });
    }

    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', () => {
            if (content) {
                content.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // -------------------------------------------------------------
    // Dark / Light Mode Toggle
    // -------------------------------------------------------------
    const savedTheme = localStorage.getItem('ebook_hok_kok_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-mode');
        if (themeToggleBtn) themeToggleBtn.textContent = '🌙';
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-mode');
            themeToggleBtn.textContent = isDark ? '☀️' : '🌙';
            localStorage.setItem('ebook_hok_kok_theme', isDark ? 'dark' : 'light');
        });
    }

    // -------------------------------------------------------------
    // Font Size Adjuster
    // -------------------------------------------------------------
    let currentFontSize = parseFloat(localStorage.getItem('ebook_font_size')) || 1.125;
    document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);

    if (fontIncBtn) {
        fontIncBtn.addEventListener('click', () => {
            if (currentFontSize < 1.45) {
                currentFontSize += 0.05;
                document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);
                localStorage.setItem('ebook_font_size', currentFontSize);
            }
        });
    }

    if (fontDecBtn) {
        fontDecBtn.addEventListener('click', () => {
            if (currentFontSize > 0.95) {
                currentFontSize -= 0.05;
                document.documentElement.style.setProperty('--reader-font-size', `${currentFontSize}rem`);
                localStorage.setItem('ebook_font_size', currentFontSize);
            }
        });
    }

    // -------------------------------------------------------------
    // Keyboard Navigation
    // -------------------------------------------------------------
    document.addEventListener('keydown', (e) => {
        // Don't trigger if user is typing in search input
        if (document.activeElement === searchInput) return;

        if (e.key === 'Escape') {
            closeSidebar();
        } else if (e.key === 'ArrowRight') {
            // Next section
            const activeSec = document.querySelector('.book-section.active');
            if (activeSec) {
                const nextBtn = activeSec.querySelector('.next-btn');
                if (nextBtn) nextBtn.click();
            }
        } else if (e.key === 'ArrowLeft') {
            // Prev section
            const activeSec = document.querySelector('.book-section.active');
            if (activeSec) {
                const prevBtn = activeSec.querySelector('.prev-btn');
                if (prevBtn) prevBtn.click();
            }
        }
    });

    // -------------------------------------------------------------
    // Initialize Start Section
    // -------------------------------------------------------------
    const initialHash = window.location.hash.replace('#', '');
    if (initialHash && document.getElementById(initialHash)) {
        activateSection(initialHash);
    } else {
        activateSection('section-0');
    }
});
