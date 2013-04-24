$(function() {
    // This is just a bunch of ugly styling hacks until we decide what to do
    // wrt moving the login form out of python-fedora.

    $('input[name=user_name]').closest('form').addClass('form-horizontal');

    $('input[type=submit]').addClass('btn btn-primary pull-right').wrap('<div class="control-group" />').wrap('<div class=controls" />');

    $('label').unwrap('.field');
    $('label[for=user_name], input[name=user_name]').wrapAll('<div class="control-group" />');
    $('label[for=password], input[name=password]').wrapAll('<div class="control-group" />');
    $('label').addClass('control-label');
    $('input[name=password], input[name=user_name]').wrap('<div class="controls" />');


    //$('input[name=user_name]').attr('placeholder', 'Username').addClass('col-span-7').wrap('<div class="control-group" />').wrap('<div class="controls" />');
    //$('input[name=password]').attr('placeholder', 'Password').addClass('col-span-7').wrap('<div class="control-group" />').wrap('<div class="controls" />');

    ul = $('.fas-login ul');
    ul.children().each(function(i,li) {
        ul.prepend(li);
    });

    $('input[name=user_name]').focus();
});
