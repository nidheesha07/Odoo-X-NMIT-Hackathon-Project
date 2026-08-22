//comment
// Automatically hides the yellow flash-message box a few seconds after page load,
// so old messages don't stay on screen forever.
document.addEventListener("DOMContentLoaded", function () {
    var flashBox = document.querySelector(".flash-box");
    if (flashBox) {
        setTimeout(function () {
            flashBox.style.transition = "opacity 0.5s ease";
            flashBox.style.opacity = "0";
            setTimeout(function () {
                flashBox.remove();
            }, 500);
        }, 4000);
    }
});

// ============================================================
// DARK / LIGHT MODE
// ============================================================

const themeToggle = document.getElementById("theme-toggle");

// Get saved theme
const savedTheme = localStorage.getItem("theme");

// Apply saved theme
if (savedTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
}

// Update button text
function updateThemeButton() {
    if (!themeToggle) return;

    const currentTheme =
        document.documentElement.getAttribute("data-theme");

    if (currentTheme === "dark") {
        themeToggle.textContent = "☀️ Light";
    } else {
        themeToggle.textContent = "🌙 Dark";
    }
}

// Toggle theme
if (themeToggle) {
    themeToggle.addEventListener("click", function () {

        const currentTheme =
            document.documentElement.getAttribute("data-theme");

        if (currentTheme === "dark") {

            // Switch to light
            document.documentElement.removeAttribute("data-theme");

            localStorage.setItem("theme", "light");

        } else {

            // Switch to dark
            document.documentElement.setAttribute(
                "data-theme",
                "dark"
            );

            localStorage.setItem("theme", "dark");
        }

        updateThemeButton();
    });
}

// Set correct button text when page loads
updateThemeButton();