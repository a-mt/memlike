/* global $ */
$(document).ready(function(){
  window.$_GET = param();
  Object.freeze(window.i18n);
  Object.freeze(window.$_GET);

  if(window.$_URL) {
    Object.freeze(window.$_URL);
  }

  if(window.markdown) {
    window.markdown.decode = function(value) {
      return window.markdown.toHTML(value.replace(/img:(https?:\/\/[^\s<>\{\}\(\)\|'\[\]^,~`]+)/g, '![]($1)'))
              .replace(/([^:>"])(https?:\/\/[^\s<>\{\}\(\)\|'\[\]^,~`]+)/g, '$1<a href="$2" class="link">$2</a>')
              .replace(/embed:(https?:\/\/[^\s<>\{\}\(\)\|'\[\]^,~`]+)/g, '<a href="$1" class="embed link">$1</a>');
    };
  } else {
    window.markdown = {decode: function(value) { return value; }};
  }

  // Show/hide elements
  $('h2[data-toggle]').on('click', function(e){
    $($(this).attr('data-toggle')).toggleClass('hide');
  });
  $('button[data-toggle]').on('click', function(e){
    $($(this).attr('data-toggle')).fadeIn();
  });
  $('#mode-selector').on('click', '.mode-selector-close', function(e){
    $(e.delegateTarget).fadeOut();
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
    multimedia.init();
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

  // Sync
  $('.ajax[data-href]').on('click', function(){
    if(this.classList.contains('loading-spinner-before')) {
      return;
    }
    var btn = this;
    btn.classList.add('loading-spinner-before');

    $.ajax({
      url: btn.getAttribute('data-href'),
      complete: function(){
        btn.classList.remove('loading-spinner-before');
        window.location.reload();
      }
    });
  });
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
  }, (window.$_GET.q ? "?q=" + encodeURIComponent(window.$_GET.q) : ""), content, paging, function(data, current_page) {
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
 * @parma string q             - query string to keep when changing page
 * @param JqueryObject content - container
 * @param JqueryObject paging  - pagination
 * @param function tpl         - callback to format response to HTML
 */
function _paginate(ajax_url, data, q, content, paging, tpl) {
  var url      = window.location.href.replace(/[?#].*/, ''),
  current_page = parseInt(window.$_GET.page) || 1,
  has_next     = true;

  if(q) {
    q += "&";
  } else {
    q = "?";
  }
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
                .attr('href', q + 'page=' + 1)
                .find('.page').html(window.i18n.page.replace('%', 1));
          }
          paging.filter('.prev').show()
                .attr('href', q + 'page=' + (current_page - 1))
                .find('.page').html(window.i18n.page.replace('%', current_page - 1));
        }

        if(has_next) {
          if(lastpage && current_page + 1 < lastpage) {
            paging.filter('.last').show()
                .attr('href', q + 'page=' + lastpage)
                .find('.page').html(window.i18n.page.replace('%', lastpage));
          }
          paging.filter('.next')
                .attr('href', q + 'page=' + (current_page + 1))
                .show().find('.page').html(window.i18n.page.replace('%', current_page + 1));
        } else {
          paging.filter('.next').hide();
        }

        if(pushState) {
          window.history.pushState({ page: current_page, has_next: has_next }, "", url + q + "page=" + current_page);
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
  isInit: false,
  target: false,
  isPlaying: false,

  reset: function() {

    // Detect when audio has stopped playing
    if(!audioPlayer.isInit) {
      audioPlayer.isInit = true;

       document.body.addEventListener('ended', function(e){
        if(e.target == audioPlayer.target) {
          audioPlayer.target.isPlaying = false;
          audioPlayer.target.classList.remove("active");
        }
      }, true);
    }

    // Reset audioPlayer state
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
  play: function(e, force) {

    // Toggle play/pause
    if(audioPlayer.target === this) {
      if(force) {
        if(!audioPlayer.isPlaying) {
          this.play();
          audioPlayer.isPlaying = true;
        }
        return;
      }
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
  },

  // Pause the current audio
  pause: function() {
    if(audioPlayer.isPlaying) {
      audioPlayer.target.pause();
      audioPlayer.target.classList.remove("active");
      audioPlayer.isPlaying = false;
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
//| Render markdown content
//+--------------------------------------------------------

var multimedia = {
  init: function() {
    $('.multimedia-wrapper').each(function(){
      var varname = this.getAttribute("data-var");

      if(window[varname]) {
        $(this).html(window.markdown.decode(window[varname]));
      }
      $(this).removeClass('loading-spinner');
    });
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

  _paginate(url, {}, "", content, paging, function(data){
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

  _paginate(url, {}, "", content, paging, function(data){
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
     $('.loading-spinner').remove();
    });
    runner.fail(function(xhr){
      if(xhr.readyState == 0 || xhr.status == 0) { // request has been canceled (change page)
        return;
      }
      if(xhr.status == 403) {
        Dashboard.container.html('<div style="width: 100%">' + window.i18n._403 + ' <a class="link" href="/login">' + window.i18n.login + '</a></div>');
      } else {
        Dashboard.container.html('<div style="width: 100%">' + window.i18n.error + '</div>');
        console.log('Error: ', xhr);
      }
    });
  }
};

//+--------------------------------------------------------
//| Text To Speech
//+--------------------------------------------------------
var TTS = {
  host: "https://google-tts-api.herokuapp.com/",
  langs: {
    "af": "Afrikaans",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "hy": "Armenian",
    "az": "Azeerbaijani",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "co": "Corsican",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "ht": "Haitian Creole",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "iw": "Hebrew",
    "hi": "Hindi",
    "hmn": "Hmong",
    "hu": "Hungarian",
    "is": "Icelandic",
    "ig": "Igbo",
    "id": "Indonesian",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "km": "Khmer",
    "ko": "Korean",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "lo": "Lao",
    "la": "Latin",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "mi": "Maori",
    "mr": "Marathi",
    "mn": "Mongolian",
    "my": "Myanmar (Burmese)",
    "ne": "Nepali",
    "no": "Norwegian",
    "ny": "Nyanja (Chichewa)",
    "ps": "Pashto",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese (Portugal, Brazil)",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "sm": "Samoan",
    "gd": "Scots Gaelic",
    "sr": "Serbian",
    "st": "Sesotho",
    "sn": "Shona",
    "sd": "Sindhi",
    "si": "Sinhala (Sinhalese)",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog (Filipino)",
    "tg": "Tajik",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zu": "Zulu"
  },
  get_audio(text, lang) {
    if(!TTS.langs[lang] || text.length >= 200) {
      return;
    }
    return TTS.host + '?q=' + encodeURIComponent(text) + '&tl=' + lang + '&ttspeed=1&download';
  }
};