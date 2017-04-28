$(window).bind("pageshow", function() {
    var form = $('#configform');
    // let the browser natively reset defaults
    form[0].reset();
});


$('input[id="form1"]').attr('disabled','disabled');





$('input[id="form0"]').on('input',function() {
    if($(this).val() != '') {
        $("#file1").val('');
        $('input[id="form1"]').removeAttr('disabled');


    }
    else {
            $('input[id="form1"]').attr('disabled','disabled');
            $('input[id="form1"]').val('');
        }
    
    
})



$("#file1").on('change',function() {
    if($(this).val() != '') {
            $('input[id="form0"]').val('');
            $('input[id="form1"]').attr('disabled','disabled');
            $('input[id="form1"]').val('');
    }
})
