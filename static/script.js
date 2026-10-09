// ==========================================
// ATTENDX - JAVASCRIPT
// Student Search + Dark/Light Theme
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    // --------------------------------------
    // 1. STUDENT SEARCH
    // --------------------------------------

    const searchInput = document.getElementById("searchInput");
    const studentTable = document.getElementById("studentTable");
    const noSearchResults = document.getElementById("noSearchResults");

    if (searchInput && studentTable) {

        const studentRows = studentTable.querySelectorAll(".student-row");

        searchInput.addEventListener("input", function () {

            const searchText = searchInput.value
                .trim()
                .toLowerCase();

            let visibleCount = 0;

            studentRows.forEach(function (row) {

                const studentName = row
                    .querySelector(".name-cell")
                    .textContent
                    .trim()
                    .toLowerCase();

                const rollNumber = row
                    .querySelector(".roll-cell")
                    .textContent
                    .trim()
                    .toLowerCase();

                const matches =
                    studentName.includes(searchText) ||
                    rollNumber.includes(searchText);

                row.style.display = matches ? "" : "none";

                if (matches) {
                    visibleCount++;
                }
            });

            if (noSearchResults) {
                noSearchResults.hidden =
                    searchText.length === 0 || visibleCount > 0;
            }
        });
    }

    // --------------------------------------
    // 2. DARK / LIGHT THEME
    // --------------------------------------

    const themeToggle = document.getElementById("themeToggle");
    const body = document.body;

    // Load the previously selected theme.
    const savedTheme = localStorage.getItem("attendx-theme");

    if (savedTheme === "light") {
        body.classList.add("light-theme");
    }

    // Update the button text to match the theme.
    function updateThemeButton() {

        if (!themeToggle) {
            return;
        }

        if (body.classList.contains("light-theme")) {
            themeToggle.textContent = "🌙 Dark Mode";
            themeToggle.setAttribute(
                "aria-label",
                "Switch to dark mode"
            );
        } else {
            themeToggle.textContent = "☀️ Light Mode";
            themeToggle.setAttribute(
                "aria-label",
                "Switch to light mode"
            );
        }
    }

    updateThemeButton();

    // Switch themes when the button is clicked.
    if (themeToggle) {

        themeToggle.addEventListener("click", function () {

            body.classList.toggle("light-theme");

            const selectedTheme =
                body.classList.contains("light-theme")
                    ? "light"
                    : "dark";

            localStorage.setItem("attendx-theme", selectedTheme);

            updateThemeButton();
        });
    }

});