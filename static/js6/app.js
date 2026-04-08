var process = process || {};
process.env = process.env || {};

const build = {
  status: process.env.VAR,
  date: process.env.BUILD_DATE,
};

/* global $, window, document, console, setTimeout */
window.GlobalEventEmitter = {
  _events: {},
  dispatch: function (eventName, data) {
      if (!this._events[eventName]) return;
      for (var i = 0; i < this._events[eventName].length; i++)
          this._events[eventName][i](data);
  },
  subscribe: function (eventName, callback) {
    if (!this._events[eventName]) this._events[eventName] = [];
    this._events[eventName].push(callback);
  }
}

$(document).ready(function(){
  window.$_GET = param();
  Object.freeze(window.I18N);
  Object.freeze(window.$_GET);

  if(window.MEMLIKE.page) {
    Object.freeze(window.MEMLIKE.page);
  }

  if(window.markdown) {
    window.markdown.decode = function(value) {
      var STATIC_URL   = 'https://static.memrise.com/',
          allowed_tags = 'p,strong,em,pre,code';

      value = value.replace(/img:http:\/\/www.memrise.com\/static\//g, 'img:' + STATIC_URL)
                   .replace(/img:http:\/\/memrise.com\/static\//g, 'img:' + STATIC_URL)
                   .replace(/img:\/static\//g, 'img:' + STATIC_URL)
                   .replace(/img:([^\s<]+)/g, '`img:$1`');
      value = window.markdown.toHTML(value);

      var res = $('<div>').html(value);
      res.find('*').each(function(){
        $(this).is(allowed_tags) || $(this).remove();
      });

      value = res.html().trim()
                .replace(/img:\s*([^\s<]+)/g, "<img class='img-tag' src='$1' />")
                .replace(/embed:\s*([^\s<]+)/g, "<a class='embed' href='$1' target='_blank'>$1</a>");

      // Header img + return carriage
      value = value.replace(/<code>(<img class='img-tag' src='https:\/\/dummyimage.com\/600x\d+\/([0-9A-Fa-f]{6}))/g, function(match, img, background){
        return '<code style="background: #' + background + '" class="header">' + img;
      })
      .replace(/\u2003+\n/g, '<br>\n');
      return value;

    };
  } else {
    window.markdown = {decode: function(value) { return value; }};
  }

  // Show/hide elements
  $('h2[data-toggle]').on('click', function(e){
    $($(this).attr('data-toggle')).toggleClass('hide');
  });
  $('button[data-toggle]').on('click', function(e){
    var $target = $($(this).attr('data-toggle')).fadeIn();

    // Give focus to the target
    if ($target.prop('nodeName') == 'FORM') {
      $target.get(0).originToggle = this;

      $('button', $target).first().focus();
    }
  });
  $('#mode-selector').on('click', '.mode-selector-close', function(e){
    var $target = $(e.delegateTarget).fadeOut();

    var originToggle = $target.get(0).originToggle;
    if (originToggle) {
      $(originToggle).focus();
    }
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
    user_progress_things();
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
  var content  = $('#courses-container'),
      paging   = $('#content-loader').children();

  _paginate('/ajax/courses', {
      lang: window.MEMLIKE.page.currentLang,
      cat : window.MEMLIKE.page.currentCat,
      q   : window.$_GET.q
  }, (window.$_GET.q ? '?q=' + encodeURIComponent(window.$_GET.q) : ''), content, paging, function(data, current_page) {
    if(data.content.trim() == '' && current_page == 1) {
      return '<div class="empty-box"><p>' + window.I18N.courses_none + '</p></div>';
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
    q += '&';
  } else {
    q = '?';
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
                .find('.page').html(window.I18N.page.replace('%', 1));
          }
          paging.filter('.prev').show()
                .attr('href', q + 'page=' + (current_page - 1))
                .find('.page').html(window.I18N.page.replace('%', current_page - 1));
        }

        if(has_next) {
          if(lastpage && current_page + 1 < lastpage) {
            paging.filter('.last').show()
                .attr('href', q + 'page=' + lastpage)
                .find('.page').html(window.I18N.page.replace('%', lastpage));
          }
          paging.filter('.next')
                .attr('href', q + 'page=' + (current_page + 1))
                .show().find('.page').html(window.I18N.page.replace('%', current_page + 1));
        } else {
          paging.filter('.next').hide();
        }

        if(pushState) {
          window.history.pushState({ page: current_page, has_next: has_next }, '', url + q + 'page=' + current_page);
        }
      },
      error: function(xhr) {
        console.error(xhr.status + ' ' + xhr.statusText);

        content.html(window.I18N.error);
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
  if(window.MEMLIKE.page.currentCatId) {
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
          audioPlayer.isPlaying = false;
          audioPlayer.target.button.classList.remove('active');
          audioPlayer.target = false;
        }
      }, true);
    }

    // Reset audioPlayer state
    if(audioPlayer.isPlaying) {
      audioPlayer.target.pause();
      audioPlayer.target.button.classList.remove('active');
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
    e.preventDefault();
    e.stopPropagation();

    let audioBtn = this; // the .audio-player element (button/a)
    let audioElement = this; // the audio element (if it exists)

    if (audioBtn.nodeName == 'A' && audioBtn.classList.contains('url')) {
      window.open(audioElement.getAttribute('src'), '_blank');
      return;
    }

    if (audioBtn.dataset && 'id' in audioBtn.dataset) {
      audioElement = document.getElementById(audioBtn.dataset.id);
      if(!audioElement) {
        console.error('Element with ID ' + audioBtn.dataset.id + ' doesnt exist');
      }
    }
    if (audioElement.nodeName != 'AUDIO') {
      console.error('Expected an audio element, instead of:', audioElement);
      return;
    }
    audioElement.button = audioBtn;

    // Toggle play/pause
    if(audioPlayer.target === audioElement) {
      if(force) {
        if(!audioPlayer.isPlaying) {
          audioElement.play();
          audioPlayer.isPlaying = true;
        }
        return;
      }
      if(audioPlayer.isPlaying) {
        audioElement.pause();
        audioElement.button.classList.remove('active');
      } else {
        audioElement.play();
        audioElement.button.classList.add('active');
      }
      audioPlayer.isPlaying = !audioPlayer.isPlaying;

    // Pause any other player and play current target
    } else {
      if(audioPlayer.isPlaying) {
        audioPlayer.target.pause();
        audioPlayer.target.classList.remove('active');
      }
      audioElement.play();
      audioElement.button.classList.add('active');
      audioPlayer.target    = audioElement;
      audioPlayer.isPlaying = true;
    }
  },

  // Pause the current audio
  pause: function() {
    if(audioPlayer.isPlaying) {
      audioPlayer.target.pause();
      audioPlayer.target.button.classList.remove('active');
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
    // for each images that have the text-image class: add the imgZoom attribute
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
      })
      // Handle close btn
      .on('click', '.modal-close-link', imgZoom.close);

    imgZoom.container = div;
  },
  open: function() {
    if(!imgZoom.container) {
      imgZoom.createContainer();
    }
    var html = `<button type="button" class="modal-close-link">${window.I18N.close}</button>`;

    // Img & legend
    var legend = $(this).closest('.thing').find('.text').text();

    html += `<figure>
            <img class="zoom" src="${this.getAttribute('src')}">
            ${legend ? `<figcaption>${legend}</figcaption>` : ''}
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
//| Modal
//+--------------------------------------------------------
var modal = {
  $container: false,
  close_callback: {},

  createContainer: function() {
    var div = $('<div id="modal" style="display: none">').appendTo(document.body);

    // Background
    $('<div class="backdrop">')
      .appendTo(div)
      .on('click', modal.close);

    // Modal
    $('<div class="modal">').appendTo(div);
    modal.$container = div;
  },
  getContainer: function() {
    if(!modal.$container) {
      modal.createContainer();
    }
    return modal.$container;
  },
  open: function(html) {
    if(!modal.$container) {
      modal.createContainer();
    }
    $('.modal', modal.$container).html(html);
    modal.reopen();
  },
  reopen() {
    modal.$container.show();
  },
  onclose: function(k, callback){
    if(!callback) {
      delete modal.close_callback[k];

    } else if(typeof callback == 'function') {
      modal.close_callback[k] = callback;
    }
  },
  close: function() {
    modal.$container && modal.$container.hide();

    for(var k in modal.close_callback) {
      modal.close_callback[k].call(modal, k);
    }
  }
};

//+--------------------------------------------------------
//| Render markdown content
//+--------------------------------------------------------

var multimedia = {
  init: function() {
    $('.multimedia-wrapper').each(function(){
      var varname = this.getAttribute('data-var');

      if(window[varname]) {
        $(this).html(window.markdown.decode(window[varname]));
      }
      $(this).removeClass('loading-spinner');
    });
  }
};

//+--------------------------------------------------------
//| User profile
//+--------------------------------------------------------

// Browse followers/following users using AJAX
function user_mempals() {
  var content  = $('#mempals-container');
  if(!content.length) {
    return;
  }
  var paging = $('#content-loader').children(),
      tab    = content.data('tab'),
      url    = '/ajax/user/' + window.MEMLIKE.page.username + '/' + tab;

  _paginate(url, {}, '', content, paging, function(data){
    if(!data.users.length) {
      var msg = window.I18N[tab + '_none'].replace('%', '<span class="grey">' + window.MEMLIKE.page.username + '</span>');
      return '<div class="empty-box"><p>' + msg + '</p></div>';
    }

    var html = '';
    for(var i=0; i<data.users.length; i++) {
      html += '<a class="user-box" href="/user/' + data.users[i].name + '">' +
                (data.users[i].photo ? `<div class="small-photo"><img src="${data.users[i].photo}" alt></div>` : '') +
                '<span title="' + data.users[i].name + '">' + data.users[i].name + '</span>'
              + '</a>';
    }
    html += '<span class="user-box is-empty"></span>';
    html += '<span class="user-box is-empty"></span>';
    html += '<span class="user-box is-empty"></span>';
    return html;
  });
}

// Browse user's courses using AJA
function user_courses() {
  var content  = $('#usercourses-container');
  if(!content.length) {
    return;
  }
  var paging = $('#content-loader').children(),
      tab    = content.data('tab'),
      url    = '/ajax/user/' + window.MEMLIKE.page.username + '/' + tab;

  _paginate(url, {}, '', content, paging, function(data){
    if(data.content.length == 0) {
      return '<div class="empty-box"><p>' + window.I18N.courses_none + '</p></div>';
    }
    return data.content.join('')
          + '<div class="course-box is-empty"></div>'
          + '<div class="course-box is-empty"></div>'
          + '<div class="course-box is-empty"></div>';
  });
}

function user_progress_things() {
  var content  = $('#things-progress-container');
  if(!content.length) {
    return;
  }
  $.ajax({
    url: '/ajax/progress',
    success: function(rendered) {
      let div = $('.ContributionCalendar', '<div>' + rendered + '</div>');
      console.log(div);
      if (div.length) {
        content.html(div);
      }
    },
    error: function(xhr) {
      console.error(xhr.status + ' ' + xhr.statusText);

      content.html(window.I18N.error);
    }
  });
}

//+--------------------------------------------------------
//| Dashboard
//+--------------------------------------------------------

var Dashboard = {
  container: false,
  sort: 'i',
  sortOptions: {},
  offset: 0,
  content: '',

  init: function() {
    Dashboard.container   = $('#dashboard');
    Dashboard.sortActions = $('#dashboard-sort');
    Dashboard.loadNext    = $('#content-next');
    Dashboard.getCourses();

    $(Dashboard.loadNext).on('click', '.btn', function(){
      Dashboard.loadMore();
    });

    $('select', Dashboard.sortActions).on('change', function(){
      var sort = this.value;

      if(sort != Dashboard.sort) {
        var option = $('option:selected', this);
        var sortOptions = {numeric: option.attr('data-numeric'), desc: option.attr('data-desc')};

        Dashboard.sort = sort;
        Dashboard.sortOptions = sortOptions;
        Dashboard.sortCourses(sort, sortOptions.numeric || false, sortOptions.desc || false);
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

  loadMore: function() {
    Dashboard.loadNext.empty();
    Dashboard.loadNext.after('<div id="content-loader" class="loading-spinner"></div>');
    Dashboard.getCourses();
  },

  getCourses: function() {
    const requestOffset = Dashboard.offset;
    if (!requestOffset) {
      Dashboard.content = '';
    }

    /* global $ */
    var offsetStream = 0;
    var runner = $.ajax({
        url: '/ajax/dashboard?offset=' + requestOffset + '&_=' + new Date().getTime(),
        data: {},
        processData: false,
        xhrFields: {
            // Getting on progress streaming response
            onprogress: function(e) {
                var response = e.target.response;

                if(response.substr(response.length-1, 1) == '$') {
                  try {
                    var r = response.substring(offsetStream);
                    offsetStream = response.length;

                    var parts = r.split('}$'),
                        n     = parts.length - 1;
                    parts.pop();

                    for(var i=0; i<=n; i++) {
                      var part = parts[i];
                      if(!part || part[0] != '{') {
                        continue;
                      }
                      var data = JSON.parse(part.replace('\n', '\\n') + '}');

                      if (data.content) {
                        Dashboard.container.append(data.content);
                        Dashboard.content += '.';

                      } else if(data.next_offset) {
                        Dashboard.offset = data.next_offset;
                        Dashboard.loadNext.html('<button class="btn">' + window.I18N.load_more +'</button>');
                      }
                    }
                  } catch(e) {
                    console.error(e);
                  }
                }
            }
        }
    });

    // Ajax done running
    runner.done(function(data) {
      if(!Dashboard.content) {
        Dashboard.container.html('<div class="empty-box"><p>' + window.I18N.empty_dashboard + '</p><a class="link" href="/community/courses">' + window.I18N.browse_courses + '</a></div>');
        return;
      }

      Dashboard.sortActions.show();
      try {
        requestOffset && setTimeout(function(){
          console.info('Resorting...');

          if(Dashboard.sort != 'i' || Dashboard.sortOptions.desc) {
            Dashboard.sortCourses(
              Dashboard.sort,
              Dashboard.sortOptions.numeric || false,
              Dashboard.sortOptions.desc || false,
            );
          }
        });
      } catch(e) {
        console.error(e);
      }
    });
    runner.always(function(data) {
      setTimeout(function(){
        $('.loading-spinner').remove();
      }, 0);
    });
    runner.fail(function(xhr){
      if(xhr.readyState == 0 || xhr.status == 0) { // request has been canceled (change page)
        return;
      }
      if(xhr.status == 403) {
        Dashboard.container.html('<div style="width: 100%">' + window.I18N._403 + ' <a class="link" href="/login">' + window.I18N.login + '</a></div>');
      } else {
        Dashboard.container.html('<div style="width: 100%">' + window.I18N.error + '</div>');
        console.log('Error: ', xhr);
      }
    });
  }
};

//+--------------------------------------------------------
//| Text To Speech
//+--------------------------------------------------------

// https://docs.cloud.google.com/translate/docs/languages?hl=de
var TTS = {
  host: 'https://google-tts-api.herokuapp.com/',
  langs: {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azeerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'iw': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'ko': 'Korean',
    'ku': 'Kurdish',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'ny': 'Nyanja (Chichewa)',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese (Portugal, Brazil)',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala (Sinhalese)',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tl': 'Tagalog (Filipino)',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu'
  },
  get_audio(text, lang) {
    if(!TTS.langs[lang] || text.length >= 200) {
      return;
    }
    const tk = Math.floor(Math.random() * 1000000);
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${lang}&client=tw-ob&q=${encodeURIComponent(text)}&tk=${tk}&ttsspeed=1`;
    return 'https://cors-anywhere.99901dev.workers.dev/?q=' + encodeURIComponent(url);

    // return TTS.host + '?q=' + encodeURIComponent(text) + '&tl=' + lang + '&ttspeed=1&download';
  }
};

//+--------------------------------------------------------
//| File download
//+--------------------------------------------------------

/**
 * Trigger a file download of the given mimeType
 * ex: download(csvContent, 'dowload.csv', 'text/csv;encoding:utf-8');
 *
 * @param string content
 * @param string fileName
 * @param mimeType
 */
var download = function(content, fileName, mimeType) {
  var a = document.createElement('a');
  mimeType = mimeType || 'application/octet-stream';

  // IE10
  if(navigator.msSaveBlob) {
    navigator.msSaveBlob(new Blob([content], {
      type: mimeType
    }), fileName);

  //html5 A[download]
  } else if (URL && 'download' in a) {
    a.href = URL.createObjectURL(new Blob([content], {
      type: mimeType
    }));
    a.setAttribute('download', fileName);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

  } else {
    window.location.href = 'data:application/octet-stream,' + encodeURIComponent(content); // only this mime type is supported
  }
};

var getCookies = function() {
  let cookie = {};
  document.cookie.split(';').forEach(function(el) {
    let [k,v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie;
}
