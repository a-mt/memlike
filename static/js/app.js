/* global $ */
$(document).ready(function(){
  window.$_GET = param();
  Object.freeze(window.i18n);
  Object.freeze(window.$_GET);

  if(window.$_URL) {
    Object.freeze(window.$_URL);
  }

  // Slide up/down elements
  $('h2[toggle]').on('click', function(e){
    $($(this).attr('toggle')).toggleClass('hide');
  });

  // Page /courses events
  if($('#courses-container').length) {
    courses();
    categories();
  }

  // Audio tag toggle play/pause
  if($('#course-container, #learn-container').length) {
    audioPlayer.init();
    imgZoom.init();
  }

  // Page /user event
  if($('#user-container').length) {
    user_mempals();
    user_courses();
  }

  // Dashboard
  if($('#dashboard').length) {
    Dashboard.init();
  }
});

//+--------------------------------------------------------
//| Get the value of a parameters of the given url (current location if false)
//| Doesn't support array parameters
//+--------------------------------------------------------
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

//+--------------------------------------------------------
//| Browse courses using AJAX
//+--------------------------------------------------------
function courses() {
  var content  = $("#courses-container"),
      paging   = $("#content-loader").children();

  _paginate('/ajax/courses', {
      lang: window.$_URL.currentLang,
      cat : window.$_URL.currentCat,
      q   : window.$_GET.q
  }, content, paging, function(data, current_page) {
    if(data.content.trim() == "" && current_page == 1) {
      return '<div class="empty-box"><p>' + window.i18n.courses_none + '</p></div>';
    } else {
      return data.content;
    }
  });
}

/**
 * @param string ajax_url
 * @param Object data          - POST parameters
 * @param JqueryObject content - container
 * @param JqueryObject paging  - pagination
 * @param function tpl         - callback to format response to HTML
 */
function _paginate(ajax_url, data, content, paging, tpl) {
  var url      = window.location.href.replace(/[?#].*/, ''),
  current_page = parseInt(window.$_GET.page) || 1,
  has_next     = true;

  function query(page, pushState) {
    content.html('');
    paging.hide().filter('.paging-loader').show();

    data.page = page;
    $.ajax({
      url: ajax_url,
      data: data,
      success: function(data) {
        var lastpage = data.lastpage || 0;

        has_next     = data.has_next;
        current_page = page;

        content.html(tpl(data, current_page));
        paging.hide();

        if(current_page == 1) {
          paging.filter('.prev').hide();
        } else {
          if(lastpage && current_page > 2) {
            paging.filter('.first').show()
                .attr('href', '?page=' + 1)
                .find('.page').html(window.i18n.page.replace('%', 1));
          }
          paging.filter('.prev').show()
                .attr('href', '?page=' + (current_page - 1))
                .find('.page').html(window.i18n.page.replace('%', current_page - 1));
        }

        if(has_next) {
          if(lastpage && current_page + 1 < lastpage) {
            paging.filter('.last').show()
                .attr('href', '?page=' + lastpage)
                .find('.page').html(window.i18n.page.replace('%', lastpage));
          }
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

        content.html(window.i18n.error);
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

//+--------------------------------------------------------
//| Show/hide child categories
//+--------------------------------------------------------
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

//+--------------------------------------------------------
//| Play/pause audio tag
//+--------------------------------------------------------
var audioPlayer = {
  target: false,
  isPlaying: false,

  reset: function() {
    if(audioPlayer.isPlaying) {
      audioPlayer.target.pause();
      audioPlayer.target.classList.remove("active");
    }
    audioPlayer.target    = false;
    audioPlayer.isPlaying = false;
  },

  init: function(){
    audioPlayer.reset();

    $('main').on('click', '.audio-player', audioPlayer.play);
  },

  // Play the target (this) audio element
  play: function() {

    // Toggle play/pause
    if(audioPlayer.target === this) {
      if(audioPlayer.isPlaying) {
        this.pause();
        this.classList.remove("active");
      } else {
        this.play();
        this.classList.add("active");
      }
      audioPlayer.isPlaying = !audioPlayer.isPlaying;

    // Pause any other player and play current target
    } else {
      if(audioPlayer.isPlaying) {
        audioPlayer.target.pause();
        audioPlayer.target.classList.remove("active");
      }
      this.play();
      this.classList.add("active");
      audioPlayer.target    = this;
      audioPlayer.isPlaying = true;
    }
  }
};

//+--------------------------------------------------------
//| View image full size
//+--------------------------------------------------------
var imgZoom = {
  container: false,
  n: 0,
  i: 0,

  reset: function() {
    imgZoom.n = $('main .text-image').each(function(i){
      $(this).attr('id', 'imgZoom-' + i)
             .data('i', i);
    }).length;
  },
  init: function() {
    imgZoom.reset();
    $('main').on('click', '.text-image', imgZoom.open);
  },
  createContainer: function() {
    var div = $('<div id="imgZoom" style="display: none">').appendTo(document.body);

    // Backgroud=nd
    $('<div class="backdrop">')
      .appendTo(div)
      .on('click', imgZoom.close);

    // Modal
    $('<div class="modal">')
      .appendTo(div)

      // Handle prev/next events
      .on('click', '.slideshow-trigger', function(){
        var i = ($(this).hasClass('prev') ? imgZoom.i - 1 : imgZoom.i + 1);
        imgZoom.open.call(document.getElementById('imgZoom-' + i));
      });

    imgZoom.container = div;
  },
  open: function() {
    if(!imgZoom.container) {
      imgZoom.createContainer();
    }

    // Img & legend
    var legend = $(this).closest('.thing').find('.text').html(),
          html = `<figure>
            <img class="zoom" src="${this.getAttribute('src')}">
            ${legend ? `<figcaption>${legend}</figcaption>` : ""}
          </figure>`;

    // Prev & next
    imgZoom.i = $(this).data('i');
    if(imgZoom.i > 0) {
      html += '<div class="slideshow-trigger prev"></div>';
    }
    if(imgZoom.i + 1 < imgZoom.n) {
      html += '<div class="slideshow-trigger next"></div>';
    }

    // Render
    $('.modal', imgZoom.container).html(html);
    imgZoom.container.show();
  },
  close: function() {
    imgZoom.container && imgZoom.container.hide();
  }
};

//+--------------------------------------------------------
//| Browse followers/following users using AJAX
//+--------------------------------------------------------
function user_mempals() {
  var content  = $("#mempals-container");
  if(!content.length) {
    return;
  }
  var paging = $("#content-loader").children(),
      tab    = content.data('tab'),
      url    = '/ajax/user/' + window.$_URL.username + '/' + tab;

  _paginate(url, {}, content, paging, function(data){
    if(!data.users.length) {
      var msg = window.i18n[tab + '_none'].replace('%', '<span class="grey">' + window.$_URL.username + '</span>');
      return '<div class="empty-box"><p>' + msg + '</p></div>';
    }

    var html = '';
    for(var i=0; i<data.users.length; i++) {
      html += '<a class="user-box" href="/user/' + data.users[i].name + '">' +
                (data.users[i].photo ? `<div class="small-photo"><img src="${data.users[i].photo}" alt></div>` : "") +
                '<span title="' + data.users[i].name + '">' + data.users[i].name + '</span>'
              + '</a>';
    }
    html += '<span class="user-box is-empty"></span>';
    html += '<span class="user-box is-empty"></span>';
    html += '<span class="user-box is-empty"></span>';
    return html;
  });
}

//+--------------------------------------------------------
//| Browse user's courses using AJAX
//+--------------------------------------------------------
function user_courses() {
  var content  = $("#usercourses-container");
  if(!content.length) {
    return;
  }
  var paging = $("#content-loader").children(),
      tab    = content.data('tab'),
      url    = '/ajax/user/' + window.$_URL.username + '/' + tab;

  _paginate(url, {}, content, paging, function(data){
    if(data.content.length == 0) {
      return '<div class="empty-box"><p>' + window.i18n.courses_none + '</p></div>';
    }
    return data.content.join('')
          + '<div class="course-box is-empty"></div>'
          + '<div class="course-box is-empty"></div>'
          + '<div class="course-box is-empty"></div>';
  });
}

//+--------------------------------------------------------
//| Dashboard
//+--------------------------------------------------------

var Dashboard = {
  container: false,
  sort: "i",

  init: function() {
    Dashboard.container = $('#dashboard');
    Dashboard.sort      = $('#dashboard-sort');
    Dashboard.getCourses();

    $('select', Dashboard.sort).on('change', function(){
      var sort = this.value;

      if(sort != Dashboard.sort) {
        var option = $("option:selected", this);

        Dashboard.sort = sort;
        Dashboard.sortCourses(sort, option.attr('data-numeric'), option.attr('data-desc'));
      }
    });
  },

  sortCourses: function(sort, isNumeric, desc) {
    var courses = Dashboard.container.children();

    if(isNumeric) {
      courses.sort(function(a, b){
        if(desc) {
          [b,a] = [a,b];
        }
        return parseFloat(a.getAttribute('data-' + sort)) - parseFloat(b.getAttribute('data-' + sort));
      });
    } else {
      courses.sort(function(a, b){
        if(desc) {
          [b,a] = [a,b];
        }
        return a.getAttribute('data-' + sort).localeCompare(b.getAttribute('data-' + sort));
      });
    }
    Dashboard.container.append(courses);
  },

  getCourses: function() {
    var offsetResponse = 0;

    /* global $ */
    var runner = $.ajax({
        url: '/ajax/dashboard',
        data: {},
        processData: false,
        xhrFields: {
            // Getting on progress streaming response
            onprogress: function(e) {
                var response = e.target.response;

                if(response.substr(response.length-1, 1) == '}') {
                  try {
                    var data = JSON.parse(response.substring(offsetResponse));
                    offsetResponse = response.length;
                    Dashboard.container.append(data.content);
                  } catch(e) { }
                }
            }
        }
    });

    // Ajax done running
    runner.done(function(data) {
     if(data == '{"content": "\\n"}') {
       Dashboard.container.html('<div class="empty-box"><p>' + window.i18n.empty_dashboard + '</p><a class="link" href="/fr/courses">' + window.i18n.browse_courses + '</a></div>');
     } else {
       Dashboard.sort.show();
     }
    });
    runner.always(function(data) {
     $('#content-loader').remove();
    });
    runner.fail(function(xhr){
      if(xhr.readyState == 0 || xhr.status == 0) { // request has been canceled (change page)
        return;
      }
      Dashboard.container.html(window.i18n.error);
      console.log('Error: ', xhr);
    });
  }
};