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

    var hash = document.location.hash;
    var prefix = "tab_";
    if (hash) {
        $('.nav-tabs a[href='+hash.replace(prefix,"")+']').tab('show');
    }

    $('.nav-tabs a').on('shown', function (e) {
        window.location.hash = e.target.hash.replace("#", "#" + prefix);
    });
});
