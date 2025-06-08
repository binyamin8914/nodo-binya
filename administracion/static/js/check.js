document.addEventListener("DOMContentLoaded", function () {
    
    const checkboxes = document.querySelectorAll(".checkbox-trigger");
    const saveButton = document.getElementById("saveChangesBtn");

    
    let cambios = false;

    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            cambios = true;
            if (cambios) {
                saveButton.style.display = "block";
            }
        });
    });
});

