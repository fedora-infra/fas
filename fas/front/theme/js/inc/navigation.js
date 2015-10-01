/**
 * When body has class 'expanded', the navbar is big and reduce on scroll.
 * Only based on css3 via css class toggling
 */

'use strict';

/* global $ */
/* global document */

module.exports = function() {
    var expandedClassname = 'navbar-expanded',
        toggling = 50;

    function resizeNavbar() {
        if($(document).scrollTop() > toggling) {
            $('body').removeClass(expandedClassname);
            $('.navbar').addClass('navbar-inverse');
        }
        else {
            $('body').addClass(expandedClassname);
            $('.navbar').removeClass('navbar-inverse');
        }
    }

    $(document).scroll(function() {
        resizeNavbar();
    });

    resizeNavbar();
};
