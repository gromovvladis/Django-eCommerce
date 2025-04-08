
let $files_list;
let $photo_input;
let $checkbox;
let $thumbnail_name = $('input[name="name"]').val();

$(document).ready(function () {
    $photo_input = $('.photo-input');
    $files_list = $photo_input.find('.input-file-list');
    let file = $photo_input.find('.current-file')[0];
    if (file) {
        let new_file_input = '<a data-original="' + file.href + '" href="#" class="input-file-list-item sub-image">' +
            '<img alt="' + $thumbnail_name + '" class="input-file-list-img" src="' + file.href + '">' +
            '<span class="input-file-list-name">' + file.innerText + '</span>' +
            '<span onclick="deleteFile(); return false;" class="input-file-list-remove"></span>' +
            '</a>';
        $files_list.append(new_file_input);
        dashboard.thumbnails.init();
        $checkbox = $($photo_input).find('input[type="checkbox"]')
        if ($checkbox.length > 0) {
            $checkbox.prop('checked', false);
        }
    }
});


var dt = new DataTransfer();

$('#id_image').on('change', function () {

    let file = this.files.item(0);

    dt = new DataTransfer();
    dt.items.add(file);

    let reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function () {
        let new_file_input = '<a data-original="' + reader.result + '" href="#" class="input-file-list-item sub-image">' +
            '<img alt="' + $thumbnail_name + '" class="input-file-list-img" src="' + reader.result + '">' +
            '<span class="input-file-list-name">' + file.name + '</span>' +
            '<span onclick="removeFilesItem(this); return false;" class="input-file-list-remove"></span>' +
            '</a>';
        $files_list.empty();
        $files_list.append(new_file_input);
        dashboard.thumbnails.init();
    }

    this.files = dt.files;

    $checkbox = $($photo_input).find('input[type="checkbox"]')
    if ($checkbox.length > 0) {
        $checkbox.prop('checked', false);
    }
});


function deleteFile() {
    $checkbox.prop('checked', true);
    $files_list.empty();
}


function removeFilesItem(target) {
    let name = $(target).prev().text();
    let input = $('#id_image');
    $(target).closest('.input-file-list-item').remove();

    for (let i = 0; i < dt.items.length; i++) {
        if (name === dt.items[i].getAsFile().name) {
            dt.items.remove(i);
        }
    }
    input[0].files = dt.files;
}
