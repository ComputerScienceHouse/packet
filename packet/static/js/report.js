const dialogs = Swal.mixin({
    customClass: {
        confirmButton: 'btn m-1 btn-primary',
        cancelButton: 'btn btn-light',
        input: 'form-control'
    },
    buttonsStyling: false,
    confirmButtonText: 'Next &rarr;',
    showCancelButton: true,
});

$("#freshman-report").click(function () {
    dialogs.queue([
        {
            title: 'Who are you reporting?',
            input: 'text',
            text: 'Please give a full name to report'
        },
        {
            title: 'What happened?',
            input: 'textarea',
            text: 'What would you like to report?'
        }
    ]).then((result) => {
        if (result.value) {
            dialogs.fire({
                title: 'Thank you for reaching out!',
                html:
                    'Person: <pre><code>' +
                    result.value[0] +
                    '</code></pre>' +
                    'Report: <pre><code>' +
                    result.value[1] +
                    '</code></pre>',
                confirmButtonText: 'All Done',
                showCancelButton: false,
                preConfirm: () => {
                    $.ajax({
                        url: "/api/v1/report/",
                        method: "POST",
                        data: {
                            "person": result.value[0],
                            "report": result.value[1]
                        }
                    });
                }
            })
        }
    })
});