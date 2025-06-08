function volver() {
    window.history.back(); 
}
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".sidebar h2").forEach((h2, index) => {
        const submenu = h2.nextElementSibling;
        const isOpen = localStorage.getItem(`menu_open_${index}`) === "true";

        if (isOpen) {
            submenu.style.display = "block";
            h2.classList.add("open");
        }

        h2.addEventListener("click", function () {
            const currentlyOpen = submenu.style.display === "block";
            submenu.style.display = currentlyOpen ? "none" : "block";
            h2.classList.toggle("open");

            
            localStorage.setItem(`menu_open_${index}`, !currentlyOpen);
        });
    });
});