$(document).ready(function () {

    $('.unsign-button').click(function () {
        var packetData = $(this).get(0).dataset;
        var userData = $("#userInfo").val();
        swal({
            title: "Are you sure?",
            text: "Once you unsign a packet, you will need to sign it again.",
            icon: "warning",
            buttons: true,
            dangerMode: true,
        })
            .then((willSign) => {
                if (willSign) {
                    $.ajax({
                        url: "/api/v1/" + userData + "/unsign/" + packetData.freshman_uid,
                        method: "POST",
                        success: function (data) {
                            swal("Congratulations or I'm sorry\nYou've unsigned " + packetData.freshman_name + "'s packet.", {
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
