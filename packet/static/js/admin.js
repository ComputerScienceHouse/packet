$(document).ready(function () {

    let openPacketsTable = $('#open_packets_table');
    openPacketsTable.DataTable({
        "searching": true,
        "order": [],
        "scrollX": false,
        "paging": true,
        "info": false,
        "columnDefs": [
            {
                "targets": 0,
                "max-width": "50%",
            },
            {
                "type": "num-fmt",
                "targets": 1,
                "visible": true,
                "max-width": "15%",
            }
        ]
    });

    let allFreshmenTable = $('#all_freshmen_table');
    allFreshmenTable.DataTable({
        "searching": true,
        "order": [],
        "scrollX": false,
        "paging": true,
        "info": false,
    });

    $("#create-packets").click(() => {
        makePackets();
    });

    $("#sync-freshmen").click(() => {
        syncFreshmen();
    })

    $("#sync-ldap").click(() => {
        syncLdap();
    })

});

// Is this gross, yes. Do I feel like cleaning it up yet, no.

let makePackets = () => {
    let freshmen = [];
    let fileUpload = document.getElementById("newPacketsFile");
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
                const payload = {start_date: $('#packet-start-date').val(), freshmen: freshmen}
                if (freshmen.length >= 1) {
                    $("#create-packets").append("&nbsp;<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span>");
                    $("#create-packets").attr('disabled', true);
                    fetch('/api/v1/packets',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload)
                        }
                    ).then(response => {
                        if (response.status < 300) {
                            $('#new-packets-modal').modal('hide');
                            location.reload();
                        } else {
                            alert("There was an error creating packets")
                        }
                    })
                }
            }
            reader.readAsText(fileUpload.files[0]);
        }
    }
}


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

let syncLdap = () => {
    $("#sync-ldap").append("&nbsp;<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span>");
    $("#sync-ldap").attr('disabled', true);
    fetch('/api/v1/sync',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(response => {
        if (response.status < 300) {
            location.reload();
        } else {
            alert("There was an error syncing with ldap")
        }
    })
}
