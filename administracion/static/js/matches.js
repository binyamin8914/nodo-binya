document.addEventListener("DOMContentLoaded", function() {
    let expandedRows = JSON.parse(localStorage.getItem("expandedRows")) || [];

    document.querySelectorAll(".toggle-row").forEach(button => {
        let row = button.closest("tr");
        let detailsRow = row.nextElementSibling;
        let rowId = row.dataset.id;

        if (expandedRows.includes(rowId)) {
            detailsRow.classList.add("expanded");
            button.textContent = "−";
        }

        button.addEventListener("click", function() {
            detailsRow.classList.toggle("expanded");
            let isExpanded = detailsRow.classList.contains("expanded");
            button.textContent = isExpanded ? "−" : "+";
            
            if (isExpanded) {
                expandedRows.push(rowId);
            } else {
                expandedRows = expandedRows.filter(id => id !== rowId);
            }
            localStorage.setItem("expandedRows", JSON.stringify(expandedRows));
        });
    });
});