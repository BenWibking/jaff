const syncContentWidth = () => {
    const content_inner = document.querySelector(".md-content__inner");
    const path_inner = document.querySelector(".md-path__list");

    if (!content_inner || !path_inner) return;

    const inner_width = content_inner.getBoundingClientRect().width;
    path_inner.style.width = `${inner_width}px`;
    console.log("Updated width:", inner_width);
};

// Debounce function to avoid too many calls
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

const debouncedSync = debounce(syncContentWidth, 100);

// Run on initial load
window.addEventListener("load", syncContentWidth);
window.addEventListener("resize", debouncedSync);

// Material theme specific events
document.addEventListener("DOMContentLoaded", syncContentWidth);

// Watch for navigation changes in Material theme
const watchForNavigation = () => {
    // Material theme navigation events
    document.addEventListener("keyup", (e) => {
        // Catch navigation keyboard events
        if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
            setTimeout(syncContentWidth, 50);
        }
    });

    // Observe navigation container
    const nav = document.querySelector(".md-nav");
    if (nav) {
        const navObserver = new MutationObserver(() => {
            setTimeout(syncContentWidth, 50);
        });
        navObserver.observe(nav, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["class", "data-md-state"]
        });
    }
};

// Start watching after initial render
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watchForNavigation);
} else {
    watchForNavigation();
}

// More aggressive observation for content changes
const observeContent = () => {
    const content = document.querySelector(".md-content");
    const main = document.querySelector(".md-main");

    if (content) {
        const contentObserver = new MutationObserver(() => {
            debouncedSync();
        });

        contentObserver.observe(content, {
            childList: true,
            subtree: true,
            attributes: true,
            characterData: true
        });
    }

    if (main) {
        const mainObserver = new MutationObserver(() => {
            debouncedSync();
        });

        mainObserver.observe(main, {
            childList: true,
            subtree: true,
            attributes: true
        });
    }
};

// Run after each Material theme navigation
const setupSPAHandlers = () => {
    // Material theme uses this for navigation
    const locationObserver = new MutationObserver(() => {
        setTimeout(syncContentWidth, 100);
    });

    // Observe URL changes
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            setTimeout(syncContentWidth, 100);
        }
    }).observe(document, { subtree: true, childList: true });

    // Click handler for navigation links
    document.addEventListener("click", (e) => {
        const link = e.target.closest(".md-nav__link, .md-tabs__link, a[href^='#']");
        if (link) {
            setTimeout(syncContentWidth, 100);
        }
    });
};

// Initialize everything
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        observeContent();
        setupSPAHandlers();
        setTimeout(syncContentWidth, 200);
    });
} else {
    observeContent();
    setupSPAHandlers();
    setTimeout(syncContentWidth, 200);
}

// Additional Material theme specific events
document.addEventListener("scroll", debouncedSync, { passive: true });

// Force update after navigation completes
const forceUpdateAfterNavigation = () => {
    // Try multiple timings to catch the layout after navigation
    [50, 150, 300].forEach(delay => {
        setTimeout(syncContentWidth, delay);
    });
};

// Watch for drawer/toc changes
const sidebarElements = document.querySelectorAll(".md-sidebar");
sidebarElements.forEach(sidebar => {
    const sidebarObserver = new MutationObserver(() => {
        setTimeout(syncContentWidth, 50);
    });
    sidebarObserver.observe(sidebar, {
        attributes: true,
        attributeFilter: ["class", "data-md-state"]
    });
});
