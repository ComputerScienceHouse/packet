$(document).ready(function () {

    $('#active_packets_table').DataTable({
        "searching": true,
        "order": [],
        "scrollX": true,
        "paging": false,
        "info": false,
        "autoWidth": false,
        "columnDefs": [
            {
                "targets": 0,
                "width": "50%",
            },
            {
                "type": "num-fmt",
                "targets": 1,
                "visible": false,
                "width": "15%",
            },
            {
                "type": "num-fmt",
                "targets": 2,
                "visible": false,
                "width": "15%",
            },
            {
                "type": "num-fmt",
                "targets": 3,
                "width": "15%",
            }
        ]
    });

    var table = $('#active_packets_table');

    $("#sig-filter").on('change', function () {
        if ($(this).val() === 'Total') {
            table.DataTable().column(1).visible(false);
            table.DataTable().column(2).visible(false);
            table.DataTable().column(3).visible(true);
        } else if ($(this).val() === 'Upperclassmen') {
            table.DataTable().column(1).visible(true);
            table.DataTable().column(2).visible(false);
            table.DataTable().column(3).visible(false);
        } else if ($(this).val() === 'Freshmen') {
            table.DataTable().column(1).visible(false);
            table.DataTable().column(2).visible(true);
            table.DataTable().column(3).visible(false);
        }
        
        // Prevent table shifting by adjusting columns
        table.DataTable().columns.adjust();
    });

});
