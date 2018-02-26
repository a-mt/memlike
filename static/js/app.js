/* global $ */
$(document).ready(function(){
  window.$_GET = param();
  Object.freeze(window.$_GET);

  if(window.$_URL) {
    Object.freeze(window.$_URL);
  }

  $('h2[toggle]').on('click', function(e){
    $($(this).attr('toggle')).toggleClass('hide');
  });

  if($('.courses-container').length) {
    courses();
    categories();
  }
});

/* Get the value of a parameters of the given url (current location if false)
 * Doesn't support array parameters
 */
function param(href) {
    if(typeof href == 'undefined' || href === false) {
        href = window.location.href;
    }
    var hash = href.indexOf('#');
    if(hash != -1) {
        href = href.substr(0, hash);
    }
    var vars = {};
    href.replace( 
        /[?&]+([^=&]+)=?([^&]*)?/gi, // regexp
        function( m, key, value ) { // callback
            vars[key] = value !== undefined ? value : '';
        }
    );
    return vars;
}

function courses() {
  var url      = window.location.href.replace(/[?#].*/, ''),
  current_page = parseInt(window.$_GET.page) || 1,
  has_next     = true;

  var content  = $("#content"),
      paging   = $("#content-loader").children();

  function query(page, pushState) {
    content.html('');
    paging.hide().filter('.paging-loader').show();

    $.ajax({
      url: '/ajax/courses',
      data: {
        lang: window.$_URL.currentLang,
        cat : window.$_URL.currentCat,
        q   : window.$_GET.q,
        page: page
      },
      success: function(data) {
        has_next     = data.has_next;
        current_page = page;

        if(data.content.trim() == "" && current_page == 1) {
          content.html('<div class="empty-box"><p>' + window.i18n.courses_none + '</p></div>');
        } else {
          content.html(data.content);
        }
        paging.hide();

        if(current_page == 1) {
          paging.filter('.prev').hide();
        } else {
          paging.filter('.prev').show()
                .attr('href', '?page=' + (current_page - 1))
                .find('.page').html(window.i18n.page.replace('%', current_page - 1));
        }

        if(has_next) {
          paging.filter('.next')
                .attr('href', '?page=' + (current_page + 1))
                .show().find('.page').html(window.i18n.page.replace('%', current_page + 1));
        } else {
          paging.filter('.next').hide();
        }

        if(pushState) {
          window.history.pushState({ page: current_page, has_next: has_next }, "", url + "?page=" + current_page);
        }
      },
      error: function(xhr) {
        console.error(xhr.status + " " + xhr.statusText);

        $('#content').html(window.i18n.error);
        paging.hide();
      }
    });
  }
  
  $(window).on('popstate', function(event) {
      var state = event.originalEvent.state;

      if(state && state.page) {
          query(state.page, false);
      }
  });

  paging.filter('.next').on('click', function(e){
    e.preventDefault();

    if(has_next) {
      query(current_page + 1, true);
    }
  });

  paging.filter('.prev').on('click', function(e){
    e.preventDefault();

    if(current_page > 1) {
      query(current_page - 1, true);
    }
  });

  query(current_page, true);
}

function categories() {
  if(window.$_URL.currentCatId) {
    $('.categories-list a.active')
      .parents('li[data-category-id]')
      .addClass('open');
  }
  $('.categories-list').on('click', 'li:has(> ul)', function(e){
    if($(e.target).is('a[data-category-leaf]')) {
      return;
    }

    e.preventDefault();
    e.stopPropagation();
    console.log(e);

    $(this).toggleClass('open');
  });
}