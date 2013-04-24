$(function() {
    $('#locale').change(function() {
        $(this).closest('form').trigger('submit');
    });

    $(".chzn-select").chosen();

    $('.hovercard>.trigger').popover({
        html: true,
        placement: 'right',
        title: function() {
            return $(this).parent().find('.head').html();
        },
        content: function() {
            return $(this).parent().find('.content').html();
        }
    });
});
