const selectField = document.getElementById("id_type");
const formGroup = document.getElementById("form-group_id_option_group");
function toggleFormGroup() {
    const selectedValue = selectField.value;
    if (selectedValue === "option" || selectedValue === "multi_option" || selectedValue === "multi_select" || selectedValue === "checkbox") {
        formGroup.classList.remove("d-none");
    } else {
        formGroup.classList.add("d-none");
    }
}

if (selectField) {
    $(selectField).on("select2:select", function () {
        toggleFormGroup();
    });
    toggleFormGroup();
}