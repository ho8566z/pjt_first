document.addEventListener("DOMContentLoaded", function () {
    const themeButton = document.querySelector("#theme_toggle_btn");

    const savedTheme = localStorage.getItem("systemTheme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    if (themeButton) {
        themeButton.textContent = savedTheme === "dark" ? "화이트 모드" : "다크 모드";

        themeButton.addEventListener("click", function () {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const nextTheme = currentTheme === "dark" ? "light" : "dark";

            document.documentElement.setAttribute("data-theme", nextTheme);
            localStorage.setItem("systemTheme", nextTheme);

            themeButton.textContent = nextTheme === "dark" ? "화이트 모드" : "다크 모드";
        });
    }
});