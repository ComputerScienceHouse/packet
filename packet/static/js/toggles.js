$(document).ready(function () {
    var toggle = $("#evalToggle");

    toggle.change(function () {
        if (this.checked) {
            $("#eval-blocks").hide();
            $("#eval-table").show();
        } else {
            $("#eval-table").hide();
            $("#eval-blocks").show();
        }
    });

});
