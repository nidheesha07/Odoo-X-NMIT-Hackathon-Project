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