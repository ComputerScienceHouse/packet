$(document).ready(function () {

    $('.sign-button').click(function () {
        var packetData = $(this).get(0).dataset;
        var userData = $("#userInfo").val();
        swal({
            title: "Are you sure?",
            text: "Once a packet is signed it can only be unsigned from request to the Evals Director",
            icon: "warning",
            buttons: true,
            dangerMode: true,
        })
            .then((willSign) => {
                if (willSign) {
                    $.ajax({
                        url: "/api/v1/" + userData + "/sign/" + packetData.freshman_uid,
                        method: "POST",
                        success: function (data) {
                            swal("Congratulations or I'm sorry\nYou've signed " + packetData.freshman_name + "'s packet.", {
                                icon: "success",
                            })
                                .then(() => {
                                    location.reload();
                                });
                        }
                    });
                }
            });
    });

});
