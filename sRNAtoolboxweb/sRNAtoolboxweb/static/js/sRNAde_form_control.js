alert("heeeeeo");

$(window).bind("pageshow", function() {
    var form = $('form')[1];
    // let the browser natively reset defaults
    form.reset();
});


$('input[id="id_matDescription"]').attr('disabled','disabled');



$('input[id="id_listofIDs"]').on('input',function() {
    if($(this).val() != '') {
        $("#id_ifile").val('');
        $('input[id="id_matDescription"]').removeAttr('disabled');


    }
    else {
            $('input[id="id_matDescription"]').attr('disabled','disabled');
            $('input[id="id_matDescription"]').val('');
        }
    
    
});



$("#id_ifile").on('change',function() {
    if($(this).val() != '') {
            $('input[id="id_listofIDs"]').val('');
            $('input[id="id_matDescription"]').removeAttr('disabled');
            $('input[id="id_matDescription"]').val('');
    }
});
