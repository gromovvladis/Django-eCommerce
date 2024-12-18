const selectField = document.getElementById("id_type");
const formGroup = document.getElementById("form-group_id_option_group");
function toggleFormGroup() {
    console.log("toggleFormGroup")
    const selectedValue = selectField.value;
    if (selectedValue === "option" || selectedValue === "multi_option") {
        formGroup.classList.remove("d-none");
    } else {
        formGroup.classList.add("d-none");
    }
}

if (selectField){
  $(selectField).on("select2:select", function () {
      toggleFormGroup();
  });
  toggleFormGroup();
}