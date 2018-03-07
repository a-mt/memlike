/** @jsx h */
'use strict';

const { h, Component, render } = window.preact;

/* global $ */
$(document).ready(function () {
  render(h(Learn, { idCourse: window.$_URL.idCourse, level: window.$_URL.lvl, type: window.$_URL.type, thing: window.$_URL.thing }), document.getElementById('learn-container'));
});

$.fn.random = function () {
  var randomIndex = Math.floor(Math.random() * this.length);
  return $(this[randomIndex]);
};

function range(start, stop, step = 1) {
  var arr = [start],
      i = start;

  while (i < stop) {
    i += step;
    arr.push(i);
  }
  return arr;
}

function randomize(arr) {
  var c = arr.length,
      rnd;

  while (c) {
    rnd = Math.random() * c-- | 0;
    [arr[c], arr[rnd]] = [arr[rnd], arr[c]];
  }
  return arr;
}

function fromKeyCode(key) {
  return String.fromCharCode(96 <= key && key <= 105 ? key - 48 : key);
}

class Learn extends Component {
  constructor(...args) {
    var _temp;

    return _temp = super(...args), this.state = { i: 0, n: 0, data: false, error: false, screen: false, recap: {}, level: 1, maxlevel: 1 }, _temp;
  }

  componentDidMount() {
    if (typeof this.props.level == "string" && this.props.level.indexOf('-')) {
      var range = this.props.level.split('-');
      this.state.level = parseInt(range[0]);
      this.state.maxlevel = parseInt(range[1]);
    } else {
      this.state.level = parseInt(this.props.level);
      this.state.maxlevel = parseInt(this.props.level);
    }
    this.getData(this.state.level);
    window.warnbeforeunload = true;
  }
  componentDidUpdate(prevProps, prevState) {
    if (!this.init) {
      this.init = true;
    }
    window.imgZoom && window.imgZoom.reset();
    window.audioPlayer && window.audioPlayer.reset();

    // Automatically play first audio
    $('.autoplay .audio-player').random().trigger("click");

    if (!prevState.data || prevState.level != this.state.level) {
      document.getElementById('level-title').innerHTML = this.state.level + " - " + this.state.data.session.level.title;
    }
  }
  getData(level) {
    $.ajax({
      url: '/ajax/course/' + this.props.idCourse + '/' + level + '/' + this.props.type,
      success: function (data) {
        if (!this.init) {
          this.bindEvents();
        }

        this.setState({
          recap: {},
          screen: false,
          error: false,
          level: level,

          data: data,
          i: 0,
          n: data.boxes.length
        });
      }.bind(this),
      error: function (xhr) {
        console.error(xhr.status + " " + xhr.statusText);
        this.setState({ error: window.i18n.error });
      }.bind(this)
    });
  }
  bindEvents() {
    $(window).on('keyup', function (e) {
      var key = e.which;

      // Press enter
      if (key == 13) {
        if (!this.expectChoice) {
          this.getNext();
        }

        // Press a choice number
      } else if (this.expectChoice && key >= 96 && key <= 105) {
        var char = parseInt(fromKeyCode(key));

        if (char < this.choices.length) {
          this.choose(char);
        }
      }
    }.bind(this));

    $('main').on('click', '.choice-box', function (e) {
      this.choose(e.currentTarget.getAttribute('accesskey'));
    }.bind(this));

    window.onbeforeunload = function (e) {
      if (!window.warnbeforeunload || this.state.recap) return;

      e = e || window.event;
      if (e) e.returnValue = 'Your changes will be lost.'; // IE, Firefox<4

      return 'Your changes will be lost.';
    }.bind(this);
  }

  choose(i) {
    var correct = this.expectChoice == i;

    // Keep track of right/wrong answers
    var recap = Object.assign({}, this.state.recap),
        id = this.state.data.boxes[this.state.i].learnable_id;
    if (!recap[id]) {
      recap[id] = { count: 0, ok: 0 };
    }
    recap[id].count++;
    if (correct) {
      recap[id].ok++;
    }

    // Display correction
    this.setState({
      recap: recap,
      screen: "correction",
      correction: correct ? false : this.choices[parseInt(i) - 1],
      kind: this.kind
    });
    this.expectChoice = false;
  }
  getNext() {

    // Display next item
    if (this.state.i + 1 < this.state.n) {
      this.setState({
        i: this.state.i + 1,
        screen: false
      });

      // Display next level or go back to course's page
    } else if (this.state.screen == "recap") {
      if (this.state.level < this.state.maxlevel) {
        if (this.state.data) {
          this.setState({
            data: false
          });
          this.getData(this.state.level + 1);
        }
      } else {
        window.warnbeforeunload = false;
        window.location.href = window.$_URL.url;
      }

      // Display recap
    } else {
      this.setState({
        i: this.state.n,
        screen: "recap"
      }, function () {
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  render(props, state) {
    var percent = state.n ? Math.ceil(state.i / state.n * 100) : 100;

    if (state.error) {
      return h(
        'div',
        null,
        state.error
      );
    }
    if (!this.state.data) {
      return h('div', { 'class': 'loading-spinner' });
    }
    if (this.props.thing) {
      return this.render_presentation(this.props.thing);
    }
    var recap = this.state.screen == "recap",
        item = recap ? false : this.state.data.boxes[this.state.i],
        tpl = item.template,
        correct;

    if (this.state.screen == "correction") {
      tpl = "presentation";
      correct = this.state.correction || true;
    }

    return h(
      'div',
      null,
      h(
        'div',
        { 'class': 'progress-bar', role: 'progressbar', 'aria-valuenow': state.i, 'aria-valuemin': '0', 'aria-valuemax': state.i },
        h(
          'div',
          { 'class': 'counter' },
          state.i,
          ' / ',
          state.n
        ),
        h(
          'div',
          { 'class': 'progress-bar-active', style: { 'clip-path': 'polygon(0 0, ' + percent + '% 0, ' + percent + '% 100%, 0 100%)' } },
          h(
            'div',
            { 'class': 'counter' },
            state.i,
            ' / ',
            state.n
          )
        )
      ),
      item && this['render_' + tpl](item.learnable_id, correct),
      recap && this.recap()
    );
  }
  render_sentinel(id) {
    var item = this.state.data.screens[id].multiple_choice,
        inputKind = item.prompt.text ? "text" : item.prompt.img ? "img" : item.prompt.audio ? "audio" : "video",
        outputKind = item.answer.kind;

    this.kind = outputKind;

    // Randomize choices order
    var n = item.choices.length,
        choicesRnd = randomize([...item.choices]);

    // Display 9 choices max
    if (n > 9) {
      n = 9;
      choicesRnd = choicesRnd.slice(0, n);
    }
    this.choices = choicesRnd;

    // Place the right answer somewhere in it
    var rnd = Math.random() * n - 1 | 0;

    return h(
      'div',
      { 'class': 'nicebox' },
      h(
        'div',
        { 'class': 'big choice autoplay' },
        this._thing(item.prompt[inputKind], inputKind)
      ),
      h(
        'div',
        { 'class': 'medium choices' },
        choicesRnd.map((it, i) => {
          if (i == rnd) {
            this.expectChoice = i + 1;
            it = item.answer.value;
          }
          return h(
            'div',
            { accesskey: i + 1, 'class': 'choice-box nicebox', id: "choice-" + (i + 1) },
            h(
              'span',
              { 'class': 'choice-index' },
              i + 1,
              '.'
            ),
            this._thingValue(it, outputKind)
          );
        })
      )
    );
  }
  displayCorrection(correction) {
    if (typeof correction == "boolean") {
      return h(
        'div',
        { 'class': 'alert alert-success' },
        window.i18n.correct_answer,
        '!'
      );
    } else {
      return h(
        'div',
        { 'class': 'alert alert-danger' },
        window.i18n.wrong_answer,
        '!\xA0',
        h(
          'span',
          null,
          window.i18n.your_answer_was,
          ': ',
          h(
            'strong',
            null,
            this._thingValue(correction, this.kind)
          )
        )
      );
    }
  }
  render_presentation(id, correction) {
    var item = this.state.data.screens[id].presentation;

    return h(
      'div',
      null,
      correction && this.displayCorrection(correction),
      h(
        'table',
        { 'class': "learn nicebox big thing" + (correction ? "" : " autoplay") },
        h(
          'tr',
          null,
          h(
            'td',
            { 'class': 'label' },
            item.item.label
          ),
          h(
            'td',
            { 'class': 'item' },
            this._thing(item.item),
            item.item.alternatives.map(alt => h(
              'div',
              { 'class': 'alt' },
              alt
            ))
          )
        ),
        h(
          'tr',
          null,
          h(
            'td',
            { 'class': 'label' },
            item.definition.label
          ),
          h(
            'td',
            { 'class': 'definition' },
            this._thing(item.definition),
            item.definition.alternatives.map(alt => h(
              'div',
              { 'class': 'alt' },
              alt
            ))
          )
        ),
        h(
          'tr',
          { 'class': 'sep' },
          h('td', { colspan: '2' })
        ),
        item.audio && h(
          'tr',
          null,
          h(
            'td',
            { 'class': 'label' },
            item.audio.label
          ),
          h(
            'td',
            { 'class': 'audio' },
            this._thing(item.audio, "audio")
          )
        ),
        item.visible_info.map(it => h(
          'tr',
          null,
          h(
            'td',
            { 'class': 'label' },
            it.label
          ),
          h(
            'td',
            { 'class': 'more' },
            this._thing(it)
          )
        )),
        item.hidden_info.map(it => h(
          'tr',
          null,
          h(
            'td',
            { 'class': 'label' },
            it.label
          ),
          h(
            'td',
            { 'class': 'more' },
            this._thing(it)
          )
        ))
      )
    );
  }
  _thingValue(it, kind) {
    return h(
      'span',
      null,
      kind == "text" ? it : kind == "image" ? h('img', { src: it, 'class': 'text-image' }) : kind == "audio" ? h('audio', { src: it, 'class': 'audio-player ico ico-l ico-audio' }) : ""
    );
  }
  _thing(it, kind) {
    kind = kind || it.kind;
    return h(
      'div',
      { 'class': kind },
      kind == "text" ? it.value : kind == "image" ? h(
        'div',
        { 'class': 'media-list' },
        it.value.map(media => h('img', { src: media, 'class': 'text-image' }))
      ) : kind == "audio" ? h(
        'div',
        { 'class': 'media-list' },
        it.value.map(media => h('audio', { src: media.normal, 'class': 'audio-player ico ico-l ico-audio' }))
      ) : ""
    );
  }
  recap() {
    var ids = {},
        tr = [];
    this.state.data.boxes.forEach(box => {
      var id = box.learnable_id;
      if (ids[id]) return;

      var item = this.state.data.screens[id].presentation;
      ids[id] = 1;

      tr.push(h(
        'tr',
        { 'class': 'thing' },
        h(
          'td',
          null,
          this._thing(item.item)
        ),
        h(
          'td',
          null,
          this._thing(item.definition)
        ),
        this.props.type != "preview" && h(
          'td',
          null,
          this.displayScore(this.state.recap[id])
        )
      ));
    });
    return h(
      'table',
      { 'class': 'learn nicebox recap' },
      tr
    );
  }
  displayScore(recap) {
    if (!recap) {
      return h(
        'span',
        null,
        '0/0'
      );
    }
    var err = recap.ok / recap.count * 100,
        className = "";
    if (err == 0) {
      className = "neverMissed";
    } else if (err > 80) {
      className = "oftenMissed";
    } else if (err < 20) {
      className = "rarelyMissed";
    } else {
      className = "sometimesMissed";
    }
    console.log(err);

    return h(
      'span',
      { 'class': className },
      recap.ok,
      '/',
      recap.count
    );
  }
}
//# sourceMappingURL=learn.js.map