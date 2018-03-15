/** @jsx h */
'use strict';

var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

const { h, Component, render } = window.preact;

/* global $ */
$(document).ready(function () {
  Object.freeze(window.course);
  render(h(Learn, { level: window.$_URL.lvl, type: window.$_URL.type, thing: window.$_URL.thing, usesession: window.$_URL.usesession }), document.getElementById('learn-container'));
});

//+--------------------------------------------------------
//| Helper functions
//+--------------------------------------------------------

$.fn.random = function () {
  var randomIndex = Math.floor(Math.random() * this.length);
  return $(this[randomIndex]);
};
Array.prototype.random = function () {
  var randomIndex = Math.floor(Math.random() * this.length);
  return this[randomIndex];
};

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

//+--------------------------------------------------------
//| Render game
//+--------------------------------------------------------

class Learn extends Component {

  //+--------------------------------------------------------
  //| LIFECYCLE
  //+--------------------------------------------------------

  // Constructor
  constructor(props) {
    super(props);

    this.state = { i: 0, n: 0, data: false, error: false, screen: false, recap: {}, level: 1, maxlevel: 1, level_type: 1 };
    if (typeof this.props.level == "string" && this.props.level.indexOf('-')) {
      var range = this.props.level.split('-');
      this.state.level = parseInt(range[0]);
      this.state.maxlevel = parseInt(range[1]);
    } else {
      this.state.level = parseInt(this.props.level);
      this.state.maxlevel = parseInt(this.props.level);
    }

    this.setMultipleChoices = this.setMultipleChoices.bind(this);
  }

  // Initialization: retrieve datas via AJAX then bind events
  componentDidMount() {
    this.getData(this.state.level, function () {

      window.onbeforeunload = this.warnbeforeunload.bind(this);

      // User clicks on a multiple choice answer
      $('main').on('click', '.choice-box', function (e) {
        this.multiple_choice(e.currentTarget.getAttribute('accesskey'));
      }.bind(this));

      // Listen to keyboard inputs: next screen, multiple choice
      $(window).on('keyup', this.keyup.bind(this));
    }.bind(this));
  }

  // Every time screen gets updated
  componentDidUpdate(prevProps, prevState) {
    if (!this.init) {
      this.init = true;
    }

    // Reset image zoom and audio player
    window.imgZoom && window.imgZoom.reset();
    window.audioPlayer && window.audioPlayer.reset();

    // Automatically play first audio
    $('.autoplay .audio-player').random().trigger("click");

    // Update level title
    if (!prevState.data || prevState.level != this.state.level) {
      document.getElementById('level-title').innerHTML = this.state.level + " - " + window.course.levels[this.state.level].name;
    }
  }

  // Retrieve the current level datas
  getData(level, callback) {
    var level_type = window.course.levels[level].type;
    $.ajax({
      url: '/ajax' + window.course.url + level + '/' + (level_type == 2 ? "media" : this.props.type),
      data: {
        session: this.props.usesession
      },
      success: function (data) {
        callback && callback();

        this.setState({
          recap: {},
          screen: false,
          error: false,
          level: level,
          level_type: level_type,

          data: data,
          i: 0,
          n: data.boxes ? data.boxes.length : 1
        });
      }.bind(this),

      error: function (xhr) {
        if (xhr.status == 403) {
          this.setState({ error: 403 });
        } else {
          console.error(xhr.status + " " + xhr.statusText);
          this.setState({ error: 500 });
        }
      }.bind(this)
    });
  }

  //+--------------------------------------------------------
  //| EVENTS
  //+--------------------------------------------------------

  // Trigger warning when user closes tab
  warnbeforeunload(e) {
    if (this.state.recap || this.state.error) return;
    var msg = 'Your changes will be lost.';

    e = e || window.event;
    if (e) {
      // IE, Firefox < 4
      e.returnValue = msg;
    }
    return msg;
  }

  // Listen to keyboard inputs: next screen, multiple choice answer
  keyup(e) {
    var key = e.which;

    // Press enter
    if (key == 13) {
      if (!this.expectChoice) {
        this.getNext();
      }

      // Press a number
    } else if (this.expectChoice && key >= 96 && key <= 105) {
      var char = parseInt(fromKeyCode(key));

      if (char <= this.choices.possible.length) {
        this.multiple_choice(char);
      }
    }
  }

  //+--------------------------------------------------------
  //| GAME COMPUTATIONS
  //+--------------------------------------------------------

  // Multiple choice: User chooses a answer
  multiple_choice(i) {
    var correct = false;

    // Check if we got the right answer
    var chosen = this.choices.possible[parseInt(i) - 1];

    for (let j = 0; j < this.choices.right.length; j++) {
      if (chosen == this.choices.right[j]) {
        correct = true;
        break;
      }
    }
    // getNormalPoints, getSpeedPoints
    this.choice_feedback(chosen, correct, correct ? 1 : 0);
  }

  // Answer has been submitted and checked: give feedback
  choice_feedback(text, correct, score) {

    // Count right and wrong answers
    var recap = Object.assign({}, this.state.recap),
        id = this.state.data.boxes[this.state.i].learnable_id;
    if (!recap[id]) {
      recap[id] = { count: 0, right: 0, pos: Object.keys(recap).length };
    }
    recap[id].count++;
    if (correct) {
      recap[id].right++;
    }

    // Display correction
    this.setState({
      recap: recap,
      screen: "correction",
      correct: correct ? false : { value: text, kind: this.choices.type }
    });
    this.expectChoice = false;
    this.choices = false;
  }

  // Display next screen
  getNext() {

    // Next item
    if (this.state.i + 1 < this.state.n) {
      this.setState({
        i: this.state.i + 1,
        screen: false
      });

      // Next level or go back to course's page
    } else if (this.state.screen == "recap" || this.state.level_type == 2) {
      if (this.state.level < this.state.maxlevel) {
        if (this.state.data) {
          this.setState({
            data: false
          });
          this.getData(this.state.level + 1);
        }
      } else {
        window.location.href = window.$_URL.urlFrom;
      }

      // Recap
    } else {
      this.setState({
        i: this.state.n,
        screen: "recap"
      }, function () {
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  //+--------------------------------------------------------
  //| RENDERING
  //+--------------------------------------------------------

  setMultipleChoices(choices) {
    this.expectChoice = "numeric";
    this.choices = choices; // {right, possible}
  }

  render(props, state) {
    if (state.error) {
      if (state.error == 403) {
        return h(
          'p',
          null,
          window.i18n._403,
          ' ',
          h(
            'a',
            { href: '/login', 'class': 'link' },
            window.i18n.login
          )
        );
      } else {
        return h(
          'p',
          null,
          window.i18n.error
        );
      }
    }
    if (!this.state.data) {
      return h('div', { 'class': 'loading-spinner' });
    }
    if (this.props.thing) {
      return this.render_presentation(this.props.thing);
    }
    if (this.state.level_type == 2) {
      return this.markdown();
    }
    var recap = this.state.screen == "recap",
        item = recap ? false : this.state.data.boxes[this.state.i],
        percent = state.n ? Math.ceil(state.i / state.n * 100) : 100,
        tpl = item.template,
        correct;

    if (this.state.screen == "correction") {
      tpl = "presentation";
      correct = this.state.correct || true;
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
    var item = this.state.data.screens[id].multiple_choice;

    return h(Sentinel, { item: item, setChoices: this.setMultipleChoices });
  }
  render_presentation(id, correct) {
    var item = this.state.data.screens[id].presentation;

    return h(Presentation, { item: item, correct: correct });
  }
  recap() {
    var items = [];

    if (this.props.type == "preview") {
      for (var i = 0; i < this.state.data.boxes.length; i++) {
        var id = this.state.data.boxes[i].learnable_id;

        items.push(this.state.data.screens[id].presentation);
      }
    } else {
      for (var id in this.state.recap) {
        var item = this.state.recap[id];

        items[item.pos] = _extends({}, item, this.state.data.screens[id].presentation);
      }
    }
    return h(Recap, { items: Object.values(items), type: this.props.type });
  }
  markdown() {
    var data = window.markdown.decode(eval(this.state.data));
    return h('div', { 'class': 'nicebox', dangerouslySetInnerHTML: { __html: data } });
  }
}

const Value = function (props) {
  var content = props.content;

  if (props.single) {
    switch (props.type) {
      case "text":
        return h(
          'span',
          null,
          content
        );
      case "image":
        return h('img', { src: content, 'class': 'text-image' });
      case "audio":
        return h('audio', { src: content, 'class': 'audio-player ico ico-l ico-audio' });
    }
  } else {
    switch (props.type) {
      case "text":
        return h(
          'div',
          { 'class': 'text' },
          content
        );
      case "image":
        return h(
          'div',
          { 'class': 'image' },
          h(
            'div',
            { 'class': 'media-list' },
            content.map(media => h('img', { src: media, 'class': 'text-image' }))
          )
        );
      case "audio":
        return h(
          'div',
          { 'class': 'audio' },
          h(
            'div',
            { 'class': 'media-list' },
            content.map(media => h('audio', { src: media.normal, 'class': 'audio-player ico ico-l ico-audio' }))
          )
        );
    }
  }
};

const Presentation = function (props) {
  var item = props.item,
      correct = props.correct;

  return h(
    'div',
    null,
    correct && (typeof correct == "boolean" ? h(
      'div',
      { 'class': 'alert alert-success' },
      window.i18n.correct_answer,
      '!'
    ) : h(
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
          h(Value, { content: correct.value, type: correct.kind, single: '1' })
        )
      )
    )),
    h(
      'table',
      { 'class': "learn nicebox big thing" + (correct ? "" : " autoplay") },
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
          h(Value, { content: item.item.value, type: item.item.kind }),
          item.item.alternatives.map(txt => h(
            'div',
            { 'class': 'alt' },
            txt
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
          h(Value, { content: item.definition.value, type: item.definition.kind }),
          item.definition.alternatives.map(txt => h(
            'div',
            { 'class': 'alt' },
            txt
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
          h(Value, { content: item.audio.value, type: 'audio' })
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
          h(Value, { content: it.value, type: it.kind })
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
          h(Value, { content: it.value, type: it.kind })
        )
      )),
      item.attributes.map(it => h(
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
          h(
            'span',
            { 'class': 'badge' },
            h(Value, { content: it.value, type: 'text', single: '1' })
          )
        )
      ))
    )
  );
};

const Sentinel = function (props) {
  var item = props.item,
      itemType = "text",
      answerType = item.answer.kind;

  if (item.prompt.img) itemType = "image";else if (item.prompt.audio) itemType = "audio";else if (item.prompt.video) itemType = "video";

  // Randomize choices order
  var n = item.choices.length,
      choicesRnd = randomize([...item.choices]);

  // Display 9 choices max
  if (n > 9) {
    n = 9;
    choicesRnd = choicesRnd.slice(0, n);
  }

  // Place the right answer somewhere in it
  var rnd = Math.random() * n - 1 | 0;

  if ($.isArray(item.answer.value)) {
    var choice = item.answer.value.random();
    choicesRnd[rnd] = choice.normal || choice;
  } else {
    choicesRnd[rnd] = item.answer.value;
  }

  var rightAnswers = [...item.answer.alternatives];
  switch (answerType) {
    case "text":
      rightAnswers.push(item.answer.value);break;
    case "audio":
      item.answer.value.forEach(it => {
        rightAnswers.push(it.normal);
      });break;
    case "image":
      item.answer.value.forEach(it => {
        rightAnswers.push(it);
      });break;
  }
  props.setChoices({ possible: choicesRnd, right: rightAnswers, type: answerType });

  return h(
    'div',
    { 'class': 'nicebox' },
    h(
      'div',
      { 'class': 'big choice autoplay' },
      h(Value, { content: item.prompt[itemType].value, type: itemType })
    ),
    h(
      'div',
      { 'class': 'medium choices' },
      choicesRnd.map((it, i) => {
        return h(
          'div',
          { accesskey: i + 1, 'class': 'choice-box nicebox', id: "choice-" + (i + 1) },
          h(
            'span',
            { 'class': 'choice-index' },
            i + 1,
            '.'
          ),
          h(Value, { content: it, type: answerType, single: '1' })
        );
      })
    )
  );
};

const Recap = function (props) {
  var items = props.items,
      type = props.type;

  return h(
    'table',
    { 'class': 'learn nicebox recap' },
    items.map(item => {
      var rate = "";

      // Compute success rate
      if (type != "preview") {
        var successRate = item.right / item.count * 100,
            className = successRate == 100 ? "neverMissed" : successRate < 20 ? "oftenMissed" : successRate > 80 ? "rarelyMissed" : "sometimesMissed",
            rate = h(
          'span',
          { 'class': className },
          item.right,
          '/',
          item.count
        );
      }

      // Render item
      return h(
        'tr',
        { 'class': 'thing' },
        h(
          'td',
          null,
          h(Value, { content: item.item.value, type: item.item.kind })
        ),
        h(
          'td',
          null,
          h(Value, { content: item.definition.value, type: item.definition.kind })
        ),
        rate && h(
          'td',
          null,
          rate
        )
      );
    })
  );
};
//# sourceMappingURL=learn.js.map