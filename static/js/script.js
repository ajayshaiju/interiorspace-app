// Mobile menu
document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector(".menu-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (!menuToggle || !navLinks) {
        return;
    }

    function closeMobileMenu() {
        navLinks.classList.remove("active");
        menuToggle.classList.remove("active");
        menuToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("menu-open");
    }

    function openMobileMenu() {
        navLinks.classList.add("active");
        menuToggle.classList.add("active");
        menuToggle.setAttribute("aria-expanded", "true");
        document.body.classList.add("menu-open");
    }

    menuToggle.addEventListener("click", (event) => {
        event.stopPropagation();

        if (navLinks.classList.contains("active")) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    });

    navLinks.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", closeMobileMenu);
    });

   document.addEventListener("click", (event) => {
    const clickedMenu = navLinks.contains(event.target);
    const clickedButton = menuToggle.contains(event.target);

    if (!clickedMenu && !clickedButton) {
        closeMobileMenu();
    }
}, true);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMobileMenu();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 768) {
            closeMobileMenu();
        }
    });

    window.addEventListener("pageshow", closeMobileMenu);
});


// Show Password
const showPassword = document.getElementById("showPassword");
const password = document.getElementById("password");

if (showPassword && password) {
    showPassword.addEventListener("change", function () {
        password.type = this.checked ? "text" : "password";
    });
}

// Show Confirm Password
const showConfirmPassword = document.getElementById("showConfirmPassword");
const confirmPassword = document.getElementById("confirm_password");

if (showConfirmPassword && confirmPassword) {
    showConfirmPassword.addEventListener("change", function () {
        confirmPassword.type = this.checked ? "text" : "password";
    });
}