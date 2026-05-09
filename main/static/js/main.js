/* DriveMatch — main.js */

// Shared toggle function
window._dmToggleTheme = function() {
    var isDark = document.body.classList.toggle('dark-mode');
    var theme  = isDark ? 'dark' : 'light';
    localStorage.setItem('dm_theme', theme);
    _dmUpdateIcons(isDark);
};

function _dmUpdateIcons(isDark) {
    // Icon glyph is rendered via CSS ::before on .dm-theme-toggle.
    // We just clear the inline <span> so it doesn't double-render.
    var icon1 = document.getElementById('themeIcon');
    if (icon1) icon1.textContent = '';
    var icon3 = document.getElementById('themeIconSidebar');
    if (icon3) icon3.innerHTML = isDark
        ? '<i class="fa-solid fa-sun"></i> Light mode'
        : '<i class="fa-solid fa-moon"></i> Dark mode';
}

// Inject theme toggle into driver sidebar if it exists and no navbar toggle is visible
function _injectSidebarToggle() {
    var sidebar = document.querySelector('.dm-sidebar');
    var navbarToggle = document.getElementById('themeToggle');
    if (sidebar && (!navbarToggle || !navbarToggle.offsetParent)) {
        if (!document.getElementById('sidebarThemeToggle')) {
            var btn = document.createElement('button');
            btn.id = 'sidebarThemeToggle';
            btn.onclick = window._dmToggleTheme;
            var isDark = document.body.classList.contains('dark-mode');
            btn.innerHTML = '<span id="themeIconSidebar">' +
                (isDark ? '<i class="fa-solid fa-sun"></i> Light mode'
                        : '<i class="fa-solid fa-moon"></i> Dark mode') + '</span>';
            btn.style.cssText = [
                'display:flex', 'align-items:center', 'gap:8px',
                'width:calc(100% - 24px)', 'margin:8px 12px',
                'background:transparent',
                'border:1px solid var(--dm-border)',
                'border-radius:8px', 'padding:8px 12px', 'font-size:12.5px',
                'cursor:pointer', 'color:var(--dm-text-2)',
                'text-align:left', 'font-weight:500',
                'font-family:inherit'
            ].join(';');
            var logo = sidebar.querySelector('.sidebar-logo');
            if (logo) {
                logo.parentNode.insertBefore(btn, logo.nextSibling);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {

    // ── APPLY SAVED THEME ─────────────────────────────────────
    var saved = localStorage.getItem('dm_theme') || 'light';
    if (saved === 'dark') {
        document.body.classList.add('dark-mode');
        _dmUpdateIcons(true);
    } else {
        _dmUpdateIcons(false);
    }

    // Inject sidebar toggle for driver pages
    _injectSidebarToggle();

    // ── NAVBAR TOGGLE ─────────────────────────────────────────
    var navBtn = document.getElementById('themeToggle');
    if (navBtn) {
        navBtn.addEventListener('click', window._dmToggleTheme);
    }

    // ── AUTO-DISMISS FLASH MESSAGES ───────────────────────────
    document.querySelectorAll('.dm-messages .alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity   = '0';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
    });

    // ── BOOKING PRICE CALCULATOR ──────────────────────────────
    var monthRadios    = document.querySelectorAll('input[name="subscription_months"]');
    var totalDisplay   = document.getElementById('total-price');
    var monthlyPriceEl = document.getElementById('monthly-price-value');

    if (monthRadios.length && totalDisplay && monthlyPriceEl) {
        var monthlyPrice = parseFloat(monthlyPriceEl.dataset.price || 0);
        monthRadios.forEach(function(radio) {
            radio.addEventListener('change', function() {
                var months = parseInt(this.value);
                totalDisplay.textContent = (monthlyPrice * months).toFixed(2) + ' SAR';
            });
        });
    }

    // ── STAR RATING HOVER ─────────────────────────────────────
    document.querySelectorAll('.star-rating input[type="radio"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var val    = parseInt(this.value);
            var labels = document.querySelectorAll('.star-rating label');
            labels.forEach(function(lbl, idx) {
                lbl.style.color = idx < val ? 'var(--dm-text)' : 'var(--dm-border-2)';
            });
        });
    });

    // ── ADD .auto-icon TO SIDEBAR LINKS ───────────────────────
    // Adds the class so CSS ::before icons render. Skips links that already have a manual <i>.
    document.querySelectorAll('.dm-sidebar .sidebar-link').forEach(function(link) {
        if (!link.querySelector('i')) {
            link.classList.add('auto-icon');
        }
    });

});
