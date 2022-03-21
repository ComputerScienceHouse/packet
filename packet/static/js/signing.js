$(document).ready(function () {

    const dialogs = Swal.mixin({
        customClass: {
            confirmButton: 'btn m-1 btn-primary',
            cancelButton: 'btn btn-light'
        },
        buttonsStyling: false,
    });

    $('.sign-button').click(function () {
        var packetData = $(this).get(0).dataset;
        var userData = $("#userInfo").val();
        dialogs.fire({
            title: "Are you sure?",
            text: "Once " + packetData.freshman_name + "'s packet is signed it can only be unsigned from request to the Evals Director",
            type: "warning",
            confirmButtonText: 'Sign',
            showCancelButton: true,
            reverseButtons: true
        })
            .then((willSign) => {
                if (willSign.value) {
                    $.ajax({
                        url: "/api/v1/sign/" + packetData.packet_id + "/",
                        method: "POST",
                        success: function (data) {
                            dialogs.fire({
                                title: "Packet Signed",
                                text: "You've signed " + packetData.freshman_name + "'s packet",
                                type: "success",
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
