$('input[type="submit"]').attr('disabled','disabled');
$('input[id="form1"]').on('keyup',function() {
    if($(this).val() != '') {
        $('input[id="form2"]').val('');
        $("#file1").val('');
        $('input[type="submit"]').removeAttr('disabled');
    }
    else {
            $('input[type="submit"]').attr('disabled','disabled');
        }
    
    
});


$('input[id="form2"]').on('keyup',function() {
    if($(this).val() != '') {
        $('input[id="form1"]').val('');
        $("#file1").val('');
        $('input[type="submit"]').removeAttr('disabled');

    }
    else {
            $('input[type="submit"]').attr('disabled','disabled');
        }
});

$("#file1").on('change',function() {
    if($(this).val() != '') {
        $('input[id="form1"]').val('');
        $('input[id="form2"]').val('');
        $('input[type="submit"]').removeAttr('disabled');

        
    }
    else {
            $('input[type="submit"]').attr('disabled','disabled');
        }
});
