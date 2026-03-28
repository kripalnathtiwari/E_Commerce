// some scripts

// jquery ready start
$(document).ready(function () {
    // jQuery code


    /* ///////////////////////////////////////

    THESE FOLLOWING SCRIPTS ONLY FOR BASIC USAGE, 
    For sliders, interactions and other

    */ ///////////////////////////////////////


    //////////////////////// Prevent closing from click inside dropdown
    $(document).on('click', '.dropdown-menu', function (e) {
        e.stopPropagation();
    });


    $('.js-check :radio').change(function () {
        var check_attr_name = $(this).attr('name');
        if ($(this).is(':checked')) {
            $('input[name=' + check_attr_name + ']').closest('.js-check').removeClass('active');
            $(this).closest('.js-check').addClass('active');
            // item.find('.radio').find('span').text('Add');

        } else {
            item.removeClass('active');
            // item.find('.radio').find('span').text('Unselect');
        }
    });


    $('.js-check :checkbox').change(function () {
        var check_attr_name = $(this).attr('name');
        if ($(this).is(':checked')) {
            $(this).closest('.js-check').addClass('active');
            // item.find('.radio').find('span').text('Add');
        } else {
            $(this).closest('.js-check').removeClass('active');
            // item.find('.radio').find('span').text('Unselect');
        }
    });



    //////////////////////// Bootstrap tooltip
    if ($('[data-toggle="tooltip"]').length > 0) {  // check if element exists
        $('[data-toggle="tooltip"]').tooltip()
    } // end if




    // AJAX for Add to Cart
    $(document).on('submit', '.ajax-cart-form', function (e) {
        var form = $(this);
        var button = form.find('button[type="submit"]:focus');

        // If Buy Now button was clicked, don't use AJAX
        if (button.val() == 'true' && button.attr('name') == 'buy_now') {
            return true;
        }

        e.preventDefault();

        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            success: function (response) {
                if (response.status === 'success') {
                    // Update cart count
                    var cartCountBadge = $('#cart-count');
                    if (cartCountBadge.length > 0) {
                        cartCountBadge.text(response.cart_count);
                        cartCountBadge.show();
                    }

                    // Show success message
                    alert(response.message);
                } else {
                    alert(response.message);
                }
            },
            error: function () {
                alert('Something went wrong. Please try again.');
            }
        });
    });
});
// jquery end

