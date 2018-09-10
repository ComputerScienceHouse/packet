$(document).ready(function () {

    $('#active_packets_table').DataTable({
        "searching": true,
        "order": [],
        "paging": false,
        "info": false,
        "columnDefs": [
            {
                "type": "num-fmt", "targets": 1
            }
        ]
    });

});
