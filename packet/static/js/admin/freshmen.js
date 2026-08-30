$(document).ready(function () {

    // let openPacketsTable = $('#open_packets_table');
    // openPacketsTable.DataTable({
    //     "searching": true,
    //     "order": [],
    //     "scrollX": false,
    //     "paging": true,
    //     "info": false,
    //     "columnDefs": [
    //         {
    //             "targets": 0,
    //             "max-width": "50%",
    //         },
    //         {
    //             "type": "num-fmt",
    //             "targets": 1,
    //             "visible": true,
    //             "max-width": "15%",
    //         }
    //     ]
    // });

    $('#all_freshmen_table').dataTable({
        "searching": true,
        "order": [],
        "scrollX": false,
        "paging": true,
        "info": false,
    });

    // $("#create-packets").click(() => {
    //     makePackets();
    // });

    $("#sync-freshmen").click(() => {
        syncFreshmen();
    })

    // $("#sync-ldap").click(() => {
    //     syncLdap();
    // })

});

let syncFreshmen = () => {
    let freshmen = [];
    let fileUpload = document.getElementById("currentFroshFile");
    let regex = /^([a-zA-Z0-9\s_\\.\-:])+(.csv|.txt)$/;
    if (regex.test(fileUpload.value.toLowerCase())) {
        if (typeof (FileReader) != "undefined") {
            let reader = new FileReader();
            reader.onload = (e) => {
                let rows = e.target.result.split("\n");
                for (let i = 0; i < rows.length; i++) {
                    let cells = rows[i].split(",");
                    if (cells.length > 1) {
                        freshmen.push({
                            rit_username: cells[3],
                            name: cells[0],
                            onfloor: cells[1]
                        });
                    }
                }
                if (freshmen.length >= 1) {
                    $("#sync-freshmen").append("&nbsp;<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span>");
                    $("#sync-freshmen").attr('disabled', true);
                    fetch('/api/v1/freshmen',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(freshmen)
                        }
                    ).then(response => {
                        if (response.status < 300) {
                            $('#sync-freshmen-modal').modal('hide');
                            location.reload();
                        } else {
                            alert("There was an error syncing freshmen")
                        }
                    })
                }
            }
            reader.readAsText(fileUpload.files[0]);
        }
    }
}