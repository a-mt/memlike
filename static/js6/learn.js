/** @jsx h */
'use strict';
const {h, Component, render} = window.preact;

/* global $ */
$(document).ready(function(){
  if(window.$_URL.lvl == "") {
    window.course.levels[1] = {"name": "", "type": 1};
  }
  Object.freeze(window.course);
  render(<Learn
            level={window.$_URL.lvl} type={window.$_URL.type}
            thing={window.$_URL.thing}
            sendresults={window.$_URL.sendresults} session={window.$_URL.session} />, document.getElementById('learn-container'));
});

//+--------------------------------------------------------
//| Helper functions
//+--------------------------------------------------------

$.fn.random = function() {
  var randomIndex = Math.floor(Math.random() * this.length);
  return $(this[randomIndex]);
};
Array.prototype.random = function(){
  var randomIndex = Math.floor(Math.random() * this.length);
  return this[randomIndex];
};

function randomize(arr){
 var c = arr.length, rnd;

 while(c){
  rnd = Math.random() * c-- | 0;
  [arr[c], arr[rnd]] = [arr[rnd], arr[c]];
 }
 return arr;
}

function fromKeyCode(key) {
  return String.fromCharCode((96 <= key && key <= 105)? key-48 : key);
}

//+--------------------------------------------------------
//| Speed review timer
//+--------------------------------------------------------

var Timer = {
  maxTime: 6e3,
  remainingTime: 0,
  lastUpdate: null,
  target: null,
  interval: null,
  callback: null,

  stop: function(){
    var time = Date.now();

    Timer.interval && clearInterval(Timer.interval);
    Timer.remainingTime -= (time - Timer.lastUpdate);
    Timer.lastUpdate     = time;
  },
  start: function(callback){
    Timer.callback      = callback;
    Timer.remainingTime = Timer.maxTime;
    Timer.lastUpdate    = Date.now();
    Timer.interval      = setInterval(Timer.tick.bind(this), 150);
  },
  get_time: function(){
    return Timer.maxTime - Timer.remainingTime;
  },
  tick: function(){
    var time = Date.now();

    Timer.remainingTime -= (time - Timer.lastUpdate);
    Timer.lastUpdate     = time;

    if(Timer.remainingTime <= 0) {
      clearInterval(Timer.interval);
      $('#speed_review-timer').css("height", '100%');

      Timer.callback && Timer.callback();
    } else {
      var percent = 1 - (Timer.remainingTime / Timer.maxTime);
      $('#speed_review-timer').css("height", (percent * 100) + '%');
    }
  }
};

//+--------------------------------------------------------
//| Render game
//+--------------------------------------------------------

class Learn extends Component {
  state = {
    i: 0, n: 0,
    data: false,
    error: false,
    screen: false,
    recap: {}, num_scheduled_correct: 0, num_scheduled: 0,
    points: 0, hearts: 3, speed_bonus: 0,
    level: 1, maxlevel: 1, level_type: 1,
    get_all: false
  };

  //+--------------------------------------------------------
  //| LIFECYCLE
  //+--------------------------------------------------------

  // Constructor
  constructor(props) {
    super(props);

    if(typeof this.props.level =="string") { // all
      this.levels         = this.props.level.split(',').map((i) => parseInt(i));

      this.state.level    = this.levels[0] || 1;
      this.state.maxlevel = this.levels[this.levels.length-1] || 1;
      this.state.get_all  = true;
    } else {
      this.state.level    = parseInt(this.props.level);
      this.state.maxlevel = parseInt(this.props.level);
    }

    this.setChoices = this.setChoices.bind(this);
  }

  // Initialization: retrieve datas via AJAX then bind events
  componentDidMount() {

    document.body.addEventListener('load', function(e){
      if(e.target.tagName == 'IMG' && e.target.classList.contains('loading')){
        e.target.classList.remove('loading');
        e.target.parentNode.style.minHeight = e.target.height + 'px';
      }
    }, true); // <-- useCapture

    // Submit
    $('main').on('click', '.submit', function(e){
      this.handle_submit(e);
    }.bind(this));

    // Typing
    $('main').on('click', '.typing .button', function(){
      this.parentNode.previousElementSibling.value += this.innerHTML;
    });

    // Tapping
    $('main').on('click', '.tapping .button', function(){
      var parent = this.parentNode;

      if(parent.className == "keyboard") {
        parent.previousElementSibling.innerHTML += '<button class="button" data-id="' + this.getAttribute('id') + '">' + this.innerHTML + '</button>';
        this.classList.add('disabled');

      } else {
        var id = this.getAttribute('data-id');
        document.getElementById(id).classList.remove('disabled');
        parent.removeChild(this);
      }
    });

    // Multiple choice
    $('main').on('click', '.choice-box', function(e){
      this.multiple_choice(e.currentTarget.getAttribute('accesskey'));
    }.bind(this));

    $('main').on('mouseover focus', '.choice-box.audio', function(e){
      window.audioPlayer && window.audioPlayer.play.call(this.lastElementChild, e, true);

    }).on('mouseleave', '.choice-box.audio', function(){
      window.audioPlayer && window.audioPlayer.pause.call(this.lastElementChild);
    });

    // Retrieve data
    this.getData(this.state.level, function(data){
      if(!this.props.thing) {
        window.onbeforeunload = this.warnbeforeunload.bind(this);
      }

      if(data.session) {
        this.langSource = data.session.course.source.language_code;
        this.langTarget = data.session.course.target.language_code;
      }

      // Listen to keyboard inputs: next screen, multiple choice
      $(window).on('keyup', this.keyup.bind(this));

    }.bind(this));
  }

  // Every time screen gets updated
  componentDidUpdate(prevProps, prevState) {
    if(!this.init) {
      this.init = true;
    }
    $('input[autofocus]').focus();

    // Reset image zoom and audio player
    window.imgZoom     && window.imgZoom.reset();
    window.audioPlayer && window.audioPlayer.reset();

    // Automatically play first audio
    $('.autoplay .audio .audio-player').random().trigger("click");

    // Add text To Speech
    if(window.TTS) {
      $('.text[lang]').each(function(){
        var src = window.TTS.get_audio(this.innerText, this.getAttribute('lang'));

        if(src) {
          if(this.firstElementChild && this.firstElementChild.nodeName == "AUDIO") {
            this.firstElementChild.src = src;

          } else {
            var audio = document.createElement('audio');
            audio.src = src;
            audio.className = "audio-player ico ico-audio";

            this.appendChild(audio);
          }
        }
      });
    }

    // Update level title
    if(!this.state.get_all) {
      if(!prevState.data || prevState.level != this.state.level) {
        var name = window.course.levels[this.state.level].name;
        document.getElementById('level-title').innerHTML = this.state.level + (name ? " - " + name : "");
      }
    } else if(this.props.type == "speed_review"){
      Timer.start(this.time_over.bind(this));
    }

    // Debug screen
    $('#debug-screen').on('click', 'li', function(e){
      if(e.target.classList.contains("disabled")) return;

      this.setState({
        debug_screen: e.target.innerHTML == "default" ? false : e.target.innerHTML
      });
    }.bind(this));
  }

  // Retrieve the current level datas
  getData(level, callback) {
    var level_type = window.course.levels[level].type;
    $.ajax({
      url: '/ajax' + window.course.url
                   + (this.state.get_all ? 'all' : level) + '/'
                   + (level_type == 2 ? "media" : this.props.type),
      data: { session: this.props.session },
      success: function(data){
        callback && callback(data);

        this.setState({
          recap: {},
          screen: false,
          error: false,
          level: level,
          level_type : level_type,

          data : data,
          i    : 0,
          n    : (data.boxes ? data.boxes.length : 1)
        });
      }.bind(this),

      error: function(xhr) {
        if(xhr.status == 403) {
          this.setState({error: 403 });
        } else {
          console.error(xhr.status + " " + xhr.statusText);
          this.setState({error: 500 });
        }
      }.bind(this)
    });
  }

  //+--------------------------------------------------------
  //| EVENTS
  //+--------------------------------------------------------

  // Trigger warning when user closes tab
  warnbeforeunload(e) {
    if(this.state.screen == "recap" || this.state.error) return;
    var msg = 'Your changes will be lost.';

    e = e || window.event;
    if (e) { // IE, Firefox < 4
      e.returnValue = msg;
    }
    return msg;
  }

  // Listen to keyboard inputs: next screen, multiple choice answer
  keyup(e) {
    var key = e.which;

    // Press enter
    if(key == 13) {
      if(e.target.classList.contains("button") || e.target.classList.contains("choice-box")) {
        if(!e.target.classList.contains("disabled")) {
          e.target.click();
        }
        return;
      }
      this.handle_submit(e);

    // Multiplice choice: press a number
    } else if(this.expectChoice == "numeric" && key > 96 && key <= 105) {
      var char = parseInt(fromKeyCode(key));

      if(char <= this.choices.length) {
        this.multiple_choice(char);
      }
    }
  }

  handle_submit(e) {

    // Presentation
    if(!this.expectChoice) {
      this.getNext();

    // Typing
    } else if(this.expectChoice == "text") {
      this.choice($('.typing input').val() || "");

    // Tapping
    } else if(this.expectChoice == "tapping") {
      var chosen = [];
      $('.tapping .input button').each(function(){
        chosen.push(this.innerHTML);
      });
      this.tapping_choice(chosen);
    }
  }

  //+--------------------------------------------------------
  //| GAME COMPUTATIONS
  //+--------------------------------------------------------

  // Multiple choice: User chooses a answer
  multiple_choice(i) {
    if(this.state.screen == "lost") {
      return;
    }
    Timer.stop();

    // Check if we got the right answer
    var idx    = parseInt(i)-1,
        choice = this.choices[idx].attributes;

    // getNormalPoints, getSpeedPoints
    this.choice_feedback({
      value: choice.value,
      score: choice.isValid ? 1 : 0,
      kind : choice.answerType,
      i    : idx
    });
  }

  time_over() {
    this.choice_feedback({
      value: "",
      score: 0,
      kind : ""
    });
  }

  // Text entry: User submit its answer
  choice(text) {

    var score      = 0,
        testText   = sanitizeTyping(text, this.is_strict).toLowerCase(),
        refText    = "";

    // Text input
    for(let i=0; i<this.choices.length; i++) {
      var choice = this.choices[i].toLowerCase(),
          s      = get_score(testText, choice);

      if(s && s > score) {
        score   = s;
        refText = choice;
      }
    }

    this.choice_feedback({
      value: testText,
      ref  : refText,
      score: score,
      kind : "text"
    });
  }

  // Tapping: User order words
  tapping_choice(entry) {
    var isValid = 0;
    entry = entry.join(" ");

    for(var i=0; i<this.choices.length; i++) {
      if(entry == this.choices[i].join(" ")) {
        isValid = 1;
        break;
      }
    }

    this.choice_feedback({
      value: entry,
      score: isValid ? 1 : 0,
      kind : "text"
    });
  }

  // Answer has been submitted and checked: give feedback
  choice_feedback(data) {
    var points      = 0,
        speed_bonus = 0,
        time_spent  = 0,
        id          = this.state.data.boxes[this.state.i].learnable_id;

    // Score
    switch(this.props.type){
      case "learn":
        points = calculate_points_learn(data.score);
        break;

      case "classic_review":
        var thing  = this.state.data.thingusers.find((item) => item.learnable_id == id),
            streak = 0;

        if(thing) {
          streak = thing.current_streak;

          if(data.score == 1) {
            thing.current_streak++;
          }
        }

        points = calculate_points_learn(data.score);
        if(streak) {
          points = calculate_points_review(points, streak);
        }
        if(data.score == 1 && time_spent) {
          speed_bonus = calculate_speed_bonus(time_spent, this.template);
        }
        break;

      case "speed_review":
        time_spent = Timer.get_time();

        if(data.score == 1) {
          points = calculate_points_speed(time_spent);

        } else if(this.state.hearts) {
          this.state.hearts -= 1;
        }
        break;
    }
    this.props.sendresults && this.register(data, id, points, data.score, time_spent);

    // Count right and wrong answers
    var recap = Object.assign({}, this.state.recap);
    if(!recap[id]) {
      recap[id] = {count: 0, right: 0, pos: Object.keys(recap).length};
    }
    recap[id].count++;
    if(data.score == 1) {
      recap[id].right++;
    }

    // Display correction
    if(this.props.type == "speed_review") {
      this.show_correct(data);

      if(this.state.hearts == 0) {
        this.state.screen = "lost";
        this.state.error  = 1;

        $(document.body).append(`<div class="overlay">
          <div class="no-heart"></div>
          <p class="overlay-text">${window.i18n.no_more_hearts} !</p>
          <div class="btn-group">
            <a href="${window.$_URL.urlFrom}">${window.i18n.return}</a>
            <a href="${window.location.href}">${window.i18n.replay}</a>
          </div>
        </div>`);

        return;
      }

      this.expectChoice = false;
      this.choices      = false;
      this.state.recap  = recap;
      this.state.points += points;
      this.state.num_scheduled += 1;
      if(data.score == 1) {
        this.state.num_scheduled_correct += 1;
      }

      setTimeout(function(){
        $(".choice-box").removeClass("correct").removeClass("incorrect");
        this.getNext();
      }.bind(this), 500);

    } else {
      this.setState({
        recap: recap,
        screen: "correction",
        correct: data,
        debug_screen: false,
        points: this.state.points + points,
        speed_bonus: this.state.speed_bonus + speed_bonus,
        num_scheduled: this.state.num_scheduled + 1,
        num_scheduled_correct: this.state.num_scheduled_correct + (data.score == 1 ? 1 : 0)
      });
      this.expectChoice  = false;
      this.choices       = false;
    }
  }
  show_correct(data) {
    if("i" in data) {
      $("#choice-" + (data.i+1)).addClass(data.score == 1 ? "correct" : "incorrect");
    }
    if(data.score != 1) {
      for(var j=0; j<this.choices.length; j++) {
        if(this.choices[j].attributes.isValid) {
          $("#choice-" + (j+1)).addClass("correct");
          break;
        }
      }
    }
  }

  // Send progress to memrise
  register(data, learnable_id, points, score, time_spent) {
    $.ajax({
      url: "/ajax/register",
      method: "POST",
      headers: {
        "X-CSRFToken": this.state.data.csrftoken,
        "X-Referer"  : this.state.data.referer
      },
      data: {
        box_template: this.template,
        course_id   : window.course.id,
        fully_grow  : false,
        given_answer: data.value,
        learnable_id: learnable_id,
        points      : points,
        score       : score,
        time_spent  : time_spent
      }
    });
  }
  session_end() {
    $.ajax({
      url: "/ajax/sync/" + window.course.id
    });

    $.ajax({
      url: "/ajax/session_end",
      method: "POST",
      headers: {
        "X-CSRFToken": this.state.data.csrftoken,
        "X-Referer"  : this.state.data.referer
      },
      data: {
        bonus_points : this.state.speed_bonus + calculate_accuracy_bonus(this.state.num_scheduled_correct / this.state.num_scheduled * 100, this.state.num_scheduled),
        course_id    : window.course.id,
        learnable_ids: '["' + Object.keys(this.state.recap).join('","') + '"]',
        session_type : (this.props.type == "classic_review" ? "review" : this.props.type),
        total_points : this.state.points
      }
    });
  }

  // Display next screen
  getNext() {

    // Next item
    if(this.state.i + 1 < this.state.n) {
      this.setState({
        i: this.state.i + 1,
        screen: false
      });

    // Next level or go back to course's page
    } else if(this.state.screen == "recap" || this.state.level_type == 2){
      if(!this.state.get_all && this.state.level < this.state.maxlevel) {
        if(this.state.data) {
          this.setState({
            data: false
          });
          this.getData(this.levels[this.levels.indexOf(this.state.level) + 1]);
        }
      } else {
        this.state.error = 1; // prevent warning
        window.location.href = window.$_URL.urlFrom;
      }

    // Recap
    } else {
      this.props.sendresults && this.session_end();

      this.setState({
        i: this.state.n,
        screen: "recap"
      }, function(){
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  //+--------------------------------------------------------
  //| RENDERING
  //+--------------------------------------------------------

  setChoices(choices, type, is_strict) {
    this.expectChoice = type; // numeric | text
    this.choices      = choices;
    this.is_strict    = is_strict || 1;
  }

  render() {

    // Something went wrong
    if(this.state.error) {
      if(this.state.error == 403) {
        return <p>{window.i18n._403} <a href="/login" class="link">{window.i18n.login}</a></p>;
      } else {
        return <p>{window.i18n.error}</p>;
      }
    }

    // Loading data
    if(!this.state.data) {
      return <div class="loading-spinner"></div>;
    }

    // Preview thing
    if(this.props.thing) {
      if(this.state.debug_screen) {
        return this.screen();
      } else {
        return <div>{/*this.addBoxDebugMenu()*/}{this.render_presentation(false)}</div>;
      }
    }

    // Media level
    if(this.state.level_type == 2) {
      return this.markdown();
    }

    // Recap
    if(this.state.screen == "recap") {
      return <div>{this.addStats()}{this.screen()}</div>;
    }

    // Default
    return <div>
      {/*this.addBoxDebugMenu()*/}

      {/* POINTS, HEARTS, PROGRESS BAR */}
      {this.addStats()}

      {/* SCREEN */}
      {this.props.type == "speed_review"
        ? <div class="speed_review"><div id="speed_review-timer" key={Date.now()}></div>{this.screen()}</div>
        : this.screen()}

      <span class="btn submit" tabindex="0">{window.i18n.next}</span>
    </div>;
  }

  addStats() {
    var percent = (this.state.n ? Math.ceil(this.state.i / this.state.n * 100) : 100);

    return <div class="progress-stats">
      {this.props.type == "speed_review" &&
        <div class="hearts-wrapper">{[1,2,3].map((i) => <span class={"heart " + (i <= this.state.hearts ? "full" : "empty")}></span>)}</div>}
      <div class="points-num">{this.state.points}</div>

      <div class="progress-bar" role="progressbar" aria-valuenow={this.state.i} aria-valuemin="0" aria-valuemax={this.state.i}>
        <div class="counter">{this.state.i} / {this.state.n}</div>
        <div class="progress-bar-active" style={{'clip-path': 'polygon(0 0, '+percent+'% 0, '+percent+'% 100%, 0 100%)'}}>
          <div class="counter">{this.state.i} / {this.state.n}</div>
        </div>
      </div>
    </div>;
  }

  addBoxDebugMenu() {
    var item    = this.state.data.boxes[this.state.i],
        screen  = this.state.data.screens[item.learnable_id],
        current = this.state.debug_screen;

    return <ul id="debug-screen">
      <li class={current ? "" : "active"}>default</li>
      <li class={("multiple_choice" in screen && screen.multiple_choice ? "" : "disabled")
              + (current == "multiple_choice" ? " active" : "")}>
        multiple_choice
      </li>
      <li class={("typing" in screen && screen.typing ? "" : "disabled")
              + (current == "typing" ? " active" : "")}>
        typing
      </li>
      <li class={("reversed_multiple_choice" in screen && screen.reversed_multiple_choice ? "" : "disabled")
              + (current == "reversed_multiple_choice" ? " active" : "")}>
        reversed_multiple_choice
      </li>
      <li class={("audio_multiple_choice" in screen && screen.audio_multiple_choice ? "" : "disabled")
              + (current == "audio_multiple_choice" ? " active" : "")}>
        audio_multiple_choice
      </li>
      <li class={("tapping" in screen && screen.tapping ? "" : "disabled")
              + (current == "tapping" ? " active" : "")}>
        tapping
      </li>
      <li class={("typing" in screen && screen.typing ? "" : "disabled")
              + (current == "copytyping" ? " active" : "")}>
        copytyping
      </li>
      <li class={("typing" in screen && screen.typing.audio ? "" : "disabled")
              + (current == "audio_typing" ? " active" : "")}>
        audio_typing
      </li>
      <li class={("reversed_multiple_choice" in screen && screen.reversed_multiple_choice.prompt.video ? "" : "disabled")
              + (current == "reversed_multiple_choice_prompt_video" ? " active" : "")}>
        reversed_multiple_choice_prompt_video
      </li>
      <li class={("multiple_choice" in screen && screen.multiple_choice.prompt.video ? "" : "disabled")
              + (current == "video-pre-presentation" ? " active" : "")}>
        video-pre-presentation
      </li>
      <li class={(screen.presentation ? "" : "disabled")
              + (current == "presentation" ? " active" : "")}>
        presentation
      </li>
    </ul>;
  }

  screen() {
    if(this.state.debug_screen) {
      switch(this.state.debug_screen) {
        case "multiple_choice"         : return this.render_tpl({ template: "multiple_choice" });
        case "typing"                  : return this.render_tpl({ template: "typing" });
        case "reversed_multiple_choice": return this.render_tpl({ template: "reversed_multiple_choice" });
        case "audio_multiple_choice"   : return this.render_tpl({ template: "audio_multiple_choice" });
        case "tapping"                 : return this.render_tpl({ template: "tapping" });
        case "copytyping"              : return this.render_tpl({ template: "copytyping" });
        case "audio_typing"            : return this.render_tpl({ template: "typing", promptWith: "audio" });
        case "reversed_multiple_choice_prompt_video": return this.render_tpl({ template: "reversed_multiple_choice", promptWith: "video" });
        case "video-pre-presentation"  : return this.render_tpl({ template: "multiple_choice", promptWith: "video" });
        case "presentation"            : return this.render_tpl({ template: "presentation" });
      }
    }

    if(this.state.screen == "recap") {
      return this.recap();
    }
    if(this.state.screen == "correction") {
      return this.render_presentation(this.state.correct || true);
    }

    var item   = this.state.data.boxes[this.state.i],
        screen = this.state.data.screens[item.learnable_id];

    if(item.learn_session_level) {
      switch(item.learn_session_level) {
        case 1:
            return this.render_tpl({
              template: "multiple_choice",
              num_choices: 4
            });

        case 2:
          if(screen.multiple_choice.video) {
            return this.render_tpl({
              template: "reversed_multiple_choice",
              num_choices: 4,
              promptWith: "video"
            });
          }
          if(screen.audio_multiple_choice && Math.random() > .5) {
            return this.render_tpl({
              template: "audio_multiple_choice"
            });
          }
          if(screen.tapping) {
            return this.render_tpl({
              template: "tapping",
              difficulty: 0
            });
          }
          return this.render_tpl({
            template: "reversed_multiple_choice",
            num_choices: 4
          });

        case 3:
          if(screen.tapping) {
            return this.render_tpl({
              template: "tapping",
              difficulty: .5
            });
          }
          if(screen.typing) {
            return this.render_tpl({
              template: "typing"
            });
          }
          return this.render_tpl({
            template: "multiple_choice",
            num_choices: 8
          });

        case 4:
          if(screen.multiple_choice.video) {
            return this.render_tpl({
              template: "reversed_multiple_choice",
              num_choices: 4,
              promptWith: "video"
            });
          }
          if(Math.random() > .5) {
            var s = [];
            if(screen.typing.audio) {
              s.push({
                template: "typing",
                promptWith: "audio"
              });
            }
            if(screen.reversed_multiple_choice.audio) {
              s.push({
                template: "reversed_multiple_choice",
                num_choices: 4,
                promptWith: "audio"
              });
            }
            if(s.length > 0) {
              return this.render_tpl(s.random());
            }
          }
          return this.render_tpl({
            template: "reversed_multiple_choice",
            num_choices: [4, 6].random()
          });

        case 5:
          if(screen.taping) {
            return this.render_tpl({
              template: "tapping",
              difficulty: .5
            });
          }
          return this.render_tpl({
            template: "multiple_choice",
            num_choices: [6, 8].random()
          });

        default:
          if(screen.typing) {
            return this.render_tpl({
              template: "typing"
            });
          }
          return {
            template: "multiple_choice",
            num_choices: 8
          };
      }
    }

    if(this.props.type == "speed_review") {
      return this.render_tpl({
        template: "multiple_choice",
        num_choices: 4
      });
    }
    if(item.template == "sentinel") {
      if(screen.typing) {
        return this.render_tpl({
          template: "typing"
        });
      }
      if(screen.audio_multiple_choice && Math.random() > .5) {
        return this.render_tpl({
          template: "audio_multiple_choice"
        });
      }
      return this.render_tpl({
          template: "multiple_choice",
          num_choices: 8
      });
    }

    return this.render_tpl({ template: item.template });
  }
  render_tpl(setting) {
    this.template = setting.template;

    switch(setting.template) {
      case "multiple_choice": return this.render_multiple_choice(setting);
      case "typing": return this.render_typing(setting);
      case "reversed_multiple_choice": return this.render_reversed_multiple_choice(setting);
      case "audio_multiple_choice": return this.render_audio_multiple_choice(setting);
      case "tapping": return this.render_tapping(setting);
      case "copytyping": return this.render_copytyping(setting);
      case "presentation":
        return this.render_presentation();
      default:
        console.error(setting.template + " doesn't exist");
    }
  }
  get_screen(tpl) {
    var id = this.props.thing || this.state.data.boxes[this.state.i].learnable_id;
    return this.state.data.screens[id][tpl];
  }

  render_audio_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen("audio_multiple_choice")}
              nChoice={setting.nChoice || 4}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_reversed_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen("reversed_multiple_choice")}
              nChoice={setting.nChoice || 4}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen("multiple_choice")}
              nChoice={setting.nChoice || (this.props.type == "speed_review" ? 4 : 9)}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_typing(setting) {
    return <Typing item={this.get_screen("typing")} setChoices={this.setChoices} promptWith={setting.promptWith} />;
  }
  render_tapping(setting) {
    return <Tapping item={this.get_screen("tapping")} difficulty={setting.difficulty || 1} setChoices={this.setChoices} />;
  }
  render_copytyping(){
    var prompt = this.get_screen("typing");
    this.setChoices(prompt.correct, "text", prompt.is_strict);

    return <Presentation item={this.get_screen("presentation")} prompt={prompt} />;
  }
  render_presentation(correct) {
    return <Presentation item={this.get_screen("presentation")} correct={correct} langTarget={this.langTarget} />;
  }
  recap() {
    var items = [];

    if(this.props.type == "preview") {
      for(var i=0; i<this.state.data.boxes.length; i++) {
        var id = this.state.data.boxes[i].learnable_id;

        items.push(this.state.data.screens[id].presentation);
      }
    } else {
      for(var id in this.state.recap) {
        var item = this.state.recap[id];

        items[item.pos] = {...item, ...this.state.data.screens[id].presentation};
      }
    }
    return <Recap items={Object.values(items)} type={this.props.type} />;
  }
  markdown() {
    var data = window.markdown.decode(eval(this.state.data));
    return <div class="nicebox" dangerouslySetInnerHTML={{__html: data}} />;
  }
}

const Value = function(props) {
  var content = props.content,
      attrs   = {};
  if(props.lang) {
    attrs.lang = props.lang;
  }
  var k = Date.now(),
      i = 0;

  if(props.single) {
    switch(props.type) {
      case "text" : return <span>{content}</span>;
      case "image": return <img key={k} src={content} class="text-image" />;
      case "audio": return <audio key={k} src={content} class="audio-player ico ico-l ico-audio"></audio>;
      case "video": return <video key={k} src={content} class="video-player" controls autoplay>Your browser does not support the video tag.</video>;
    }
  } else {
    switch(props.type) {
      case "text" : return <div class="text" {...attrs}>{content}</div>;
      case "image": return <div class="image"><div class="media-list">{content.map(media => <img key={k + i++} src={media} class="text-image loading" />)}</div></div>;
      case "audio": return <div class="audio"><div class="media-list">{content.map(media => <audio key={k + i++} src={media.normal} class="audio-player ico ico-l ico-audio"></audio>)}</div></div>;
      case "video": return <div class="video"><div class="media-list"><video key={k + i++} src={content.random()} class="video-player" controls autoplay>Your browser does not support the video tag.</video></div></div>;
    }
  }
};

const Correction = function(props) {
  var data = props.data;

  if(data.score == 1) {
    return <div class="alert alert-success">{window.i18n.correct_answer}!</div>;

  } else if(data.score == 0) {
    return <div class="alert alert-danger">
      {window.i18n.wrong_answer}!&nbsp;
      {data.value
        ? <span>{window.i18n.your_answer_was}: <strong><Value content={data.value} type={data.kind} single="1" /></strong></span>
        : <span>{window.i18n.your_answer_was_empty}</span>}
    </div>;

  } else {
    return <div class="alert alert-warning">
      {window.i18n.near_answer}!&nbsp;
      <span>{window.i18n.your_answer_was}: <strong>
        {data.kind == "text"
          ? <span>{data.value} <small class="correction" dangerouslySetInnerHTML={{__html: "(" + diff(data.value, data.ref) + ")"}} /></span>
          : <Value content={data.value} type={data.kind} single="1" />}
      </strong></span>
    </div>;
  }
};

const Presentation = function(props){
  var item = props.item, correct = props.correct,
      k    = Date.now(), i = 0;
	return <div>

    {/*-- Correction --*/}
    {correct && <Correction data={correct} />}

    {/*-- Content --*/}
    <table class={"learn nicebox big thing" + (correct ? "": " autoplay")}>

        {/*-- Item --*/}
        <tr>
          <td class="label">{item.item.label}</td>
          <td class="item">
            <Value content={item.item.value} type={item.item.kind} lang={this.props.langTarget} />
            {item.item.alternatives.map(txt =>
              <div class="alt">{txt}</div>
            )}
          </td>
        </tr>

        {/*-- Definition --*/}
        <tr>
          <td class="label">{item.definition.label}</td>
          <td class="definition">
            <Value content={item.definition.value} type={item.definition.kind} />
            {item.definition.alternatives.map(txt =>
              <div class="alt">{txt}</div>
            )}
          </td>
        </tr>
        <tr class="sep"><td colspan="2"></td></tr>

        {/*-- Audio --*/}
        {item.audio && <tr key={k + i++}>
          <td class="label">{item.audio.label}</td>
          <td class="audio"><Value content={item.audio.value} type="audio" /></td>
        </tr>}

        {/*-- Additional content --*/}
        {item.visible_info.map(it => <tr key={k + i++}>
          <td class="label">{it.label}</td>
          <td class="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {item.hidden_info.map(it => <tr key={k + i++}>
          <td class="label">{it.label}</td>
          <td class="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {/*-- Attributs --*/}
        {item.attributes.map(it => <tr key={k + i++}>
          <td class="label">{it.label}</td>
          <td class="more"><span class="badge"><Value content={it.value} type="text" single="1" /></span></td>
        </tr>)}
      </table>

      {/*-- Copytyping --*/}
      {props.prompt && <div class="typing-container" key={k + i++}>
          <div class="typing">
            <input type="text" autocomplete="off" spellcheck="false" value="" placeholder={props.prompt.answer.value} tabindex="1" autoFocus="autofocus" />
            <ul class="keyboard">{props.prompt.choices.map((letter, i) =>
              <li class="button" tabindex={i+2}>{letter}</li>
            )}</ul>
          </div>
        </div>}
    </div>;
};

function get_prompt_type(item) {
  if(item.prompt.text) return "text";
  if(item.prompt.image) return "image";
  if(item.prompt.audio) return "audio";
  if(item.prompt.video) return "video";
}

const MultipleChoice = function(props) {
  var item       = props.item,
      itemType   = props.promptWith || get_prompt_type(item),
      answerType = item.answer.kind;

  // Randomize choices order
  var n          = item.choices.length,
      choicesRnd = randomize([...item.choices]);

  // Display 9 choices max
  if(n > props.nChoice) {
    n = props.nChoice;
    choicesRnd = choicesRnd.slice(0, n);
  }

  // Place the right answer somewhere in it
  var rnd    = Math.random() * n - 1 | 0,
     isArr   = $.isArray(item.answer.value);

  if(isArr) {
    var choice = item.answer.value.random();
    choicesRnd[rnd] = choice.normal || choice;
  } else {
    choicesRnd[rnd] = item.answer.value;
  }

  // Get the list of answers that are acceptable
  var rightAnswers = [];
  if(isArr) {
    for(var i=0; i<item.answer.value.length; i++) {
      choice = item.answer.value[i];
      rightAnswers.push(choice.normal || choice);
    }
  } else {
    choicesRnd[rnd] = item.answer.value;
    rightAnswers.push(item.answer.value);
  }
  rightAnswers.push(...item.answer.alternatives);

  // Display our boxes
  var choices = choicesRnd.map((value, i) => {
    return <ChoiceBox key={i} i={i+1} value={value} answerType={answerType} isValid={rightAnswers.includes(value)} />;
  });
  props.setChoices(choices, "numeric");

  return <div class="nicebox">

    {/*-- Item --*/}
    <div class="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />
    </div>

    {/*-- Choices --*/}
    <div class={"medium choices n" + props.nChoice}>{choices}</div>
  </div>;
};

class ChoiceBox extends Component {
  render(props) {
    return <div accesskey={props.i} class={"choice-box nicebox " + props.answerType} id={"choice-" + props.i} tabindex={props.i}>
      <span class="choice-index">{props.i}.</span>
      <Value content={props.value} type={props.answerType} single="1" />
    </div>;
  }
}

const Typing = function(props) {
  var item     = props.item,
      itemType = props.promptWith || get_prompt_type(item);

  props.setChoices(item.correct, "text", item.is_strict);

  return <div class="nicebox">
    <div class="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />
    </div>
    <div class="typing-container">
      <div class="typing" key={Date.now()}>
        <input type="text" autocomplete="off" spellcheck="false" value="" tabindex="1" autoFocus="autofocus" />
        <ul class="keyboard">{item.choices.map((letter, i) =>
          <li class="button" tabindex={i+2}>{letter}</li>
        )}</ul>
      </div>
    </div>
  </div>;
};

const Tapping = function(props) {
  var item     = props.item,
      itemType = get_prompt_type(item);

  props.setChoices(item.correct, "tapping", item.is_strict);

  var n       = item.correct.length,
      choices = item.correct[0].slice(),
      remains = item.choices.filter((it) => !choices.includes(it)),
      extra   = 0;

  if(props.difficulty == 0) {
    extra = 0;
  } else if(n < 5){
    extra = 6 - n;
  } else {
    extra = Math.min(Math.max(0, 15 - n), Math.ceil(props.difficulty * n));
  }

  for(var i=0; i<extra; i++) {
    if(!remains.length) {
      break;
    }
    var rnd = Math.floor(Math.random() * remains.length),
        it  = remains.splice(rnd,1);
    choices.push(...it);
  }

  return <div class="nicebox">
    <div class="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />
    </div>
    <div class="tapping-container">
      <div class="tapping" key={Date.now()}>
        <div class="input"></div>
        <ul class="keyboard">{randomize(choices).map((word, i) =>
          <li class="button" tabindex={i+1} id={"btn-" + i}>{word}</li>
        )}</ul>
      </div>
    </div>
  </div>;
};

const Recap = function(props) {
  var items = props.items,
      type  = props.type;

  return <table class="learn nicebox recap">
  {items.map((item) => {
    var rate = "";

    // Compute success rate
    if(type != "preview") {
      var successRate = item.right / item.count * 100,
          className   = (successRate == 100 ? "neverMissed" : (successRate < 20 ? "oftenMissed" : (successRate > 80 ? "rarelyMissed" : "sometimesMissed"))),
          rate        = <span class={className}>{item.right}/{item.count}</span>;
    }

    // Render item
    return <tr class="thing">
      <td><Value content={item.item.value} type={item.item.kind} /></td>
      <td><Value content={item.definition.value} type={item.definition.kind} /></td>
      {rate && <td>{rate}</td>}
    </tr>})}
  </table>;
};

//+--------------------------------------------------------
//| SCORING SYSTEM
//+--------------------------------------------------------

function get_score(response, answer) {
 var FIRST_LETTER_WEIGHT = .1,
     DISTANCE_WEIGHT = .9;

  if(!response) {
    return 0;
  }
  var both_are_numeric = function() {
    return $.isNumeric(parseInt(response, 10)) && $.isNumeric(parseInt(answer, 10));
  },
  get_tolerance = function() {
    var t = answer.length > 18 ? .5 : answer.length < 3 ? 1 : -1 * answer.length / 33 + 1.1;
    return t, answer.length * t;
  },
  get_numeric_score = function() {
    return (parseInt(response, 10) === parseInt(answer, 10) ? 1 : 0);
  },
  get_string_score = function() {
    var tolerance = get_tolerance(),
        n = distance(response, answer);
    if (n >= tolerance) return 0;

    var r = answer.charAt(0) === response.charAt(0) ? 1 : 0,
        i = (tolerance - n) / tolerance,
        s = FIRST_LETTER_WEIGHT * r + DISTANCE_WEIGHT * i;

    return s < .5 && (s = 0), s;
  };
  return both_are_numeric() ? get_numeric_score() : get_string_score();
}

function distance(a, b) {
  var calculate_distance_matrix = function() {
    var get_item_at;

    if($.isArray(a)) {
      get_item_at = function(arr, i) { return arr[i] };
    } else {
      get_item_at = function(arr, i) { return arr.charAt(i) };
    }

    // Create matrix
    var matrix = [];
    for (var i = 0; i <= a.length; i += 1) matrix[i] = [], matrix[i][0] = i;
    for (var j = 0; j <= b.length; j += 1) matrix[0][j] = j;

    // Calculate distance
    for (var i = 1; i <= a.length; i += 1) {
      for (var j = 1; j <= b.length; j += 1) {
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j - 1] + (get_item_at(a, i - 1) === get_item_at(b, j - 1) ? 0 : 1)
        );
      }
    }
    return matrix;
  };

  var matrix = calculate_distance_matrix();
  return matrix[a.length][b.length];
}

// https://cdnjs.cloudflare.com/ajax/libs/xregexp/3.1.1/xregexp-all.js
var RegexUnicode = {
  'C': '\0-\x1F\x7F-\x9F\xAD\u0378\u0379\u0380-\u0383\u038B\u038D\u03A2\u0530\u0557\u0558\u0560\u0588\u058B\u058C\u0590\u05C8-\u05CF\u05EB-\u05EF\u05F5-\u0605\u061C\u061D\u06DD\u070E\u070F\u074B\u074C\u07B2-\u07BF\u07FB-\u07FF\u082E\u082F\u083F\u085C\u085D\u085F-\u089F\u08B5-\u08E2\u0984\u098D\u098E\u0991\u0992\u09A9\u09B1\u09B3-\u09B5\u09BA\u09BB\u09C5\u09C6\u09C9\u09CA\u09CF-\u09D6\u09D8-\u09DB\u09DE\u09E4\u09E5\u09FC-\u0A00\u0A04\u0A0B-\u0A0E\u0A11\u0A12\u0A29\u0A31\u0A34\u0A37\u0A3A\u0A3B\u0A3D\u0A43-\u0A46\u0A49\u0A4A\u0A4E-\u0A50\u0A52-\u0A58\u0A5D\u0A5F-\u0A65\u0A76-\u0A80\u0A84\u0A8E\u0A92\u0AA9\u0AB1\u0AB4\u0ABA\u0ABB\u0AC6\u0ACA\u0ACE\u0ACF\u0AD1-\u0ADF\u0AE4\u0AE5\u0AF2-\u0AF8\u0AFA-\u0B00\u0B04\u0B0D\u0B0E\u0B11\u0B12\u0B29\u0B31\u0B34\u0B3A\u0B3B\u0B45\u0B46\u0B49\u0B4A\u0B4E-\u0B55\u0B58-\u0B5B\u0B5E\u0B64\u0B65\u0B78-\u0B81\u0B84\u0B8B-\u0B8D\u0B91\u0B96-\u0B98\u0B9B\u0B9D\u0BA0-\u0BA2\u0BA5-\u0BA7\u0BAB-\u0BAD\u0BBA-\u0BBD\u0BC3-\u0BC5\u0BC9\u0BCE\u0BCF\u0BD1-\u0BD6\u0BD8-\u0BE5\u0BFB-\u0BFF\u0C04\u0C0D\u0C11\u0C29\u0C3A-\u0C3C\u0C45\u0C49\u0C4E-\u0C54\u0C57\u0C5B-\u0C5F\u0C64\u0C65\u0C70-\u0C77\u0C80\u0C84\u0C8D\u0C91\u0CA9\u0CB4\u0CBA\u0CBB\u0CC5\u0CC9\u0CCE-\u0CD4\u0CD7-\u0CDD\u0CDF\u0CE4\u0CE5\u0CF0\u0CF3-\u0D00\u0D04\u0D0D\u0D11\u0D3B\u0D3C\u0D45\u0D49\u0D4F-\u0D56\u0D58-\u0D5E\u0D64\u0D65\u0D76-\u0D78\u0D80\u0D81\u0D84\u0D97-\u0D99\u0DB2\u0DBC\u0DBE\u0DBF\u0DC7-\u0DC9\u0DCB-\u0DCE\u0DD5\u0DD7\u0DE0-\u0DE5\u0DF0\u0DF1\u0DF5-\u0E00\u0E3B-\u0E3E\u0E5C-\u0E80\u0E83\u0E85\u0E86\u0E89\u0E8B\u0E8C\u0E8E-\u0E93\u0E98\u0EA0\u0EA4\u0EA6\u0EA8\u0EA9\u0EAC\u0EBA\u0EBE\u0EBF\u0EC5\u0EC7\u0ECE\u0ECF\u0EDA\u0EDB\u0EE0-\u0EFF\u0F48\u0F6D-\u0F70\u0F98\u0FBD\u0FCD\u0FDB-\u0FFF\u10C6\u10C8-\u10CC\u10CE\u10CF\u1249\u124E\u124F\u1257\u1259\u125E\u125F\u1289\u128E\u128F\u12B1\u12B6\u12B7\u12BF\u12C1\u12C6\u12C7\u12D7\u1311\u1316\u1317\u135B\u135C\u137D-\u137F\u139A-\u139F\u13F6\u13F7\u13FE\u13FF\u169D-\u169F\u16F9-\u16FF\u170D\u1715-\u171F\u1737-\u173F\u1754-\u175F\u176D\u1771\u1774-\u177F\u17DE\u17DF\u17EA-\u17EF\u17FA-\u17FF\u180E\u180F\u181A-\u181F\u1878-\u187F\u18AB-\u18AF\u18F6-\u18FF\u191F\u192C-\u192F\u193C-\u193F\u1941-\u1943\u196E\u196F\u1975-\u197F\u19AC-\u19AF\u19CA-\u19CF\u19DB-\u19DD\u1A1C\u1A1D\u1A5F\u1A7D\u1A7E\u1A8A-\u1A8F\u1A9A-\u1A9F\u1AAE\u1AAF\u1ABF-\u1AFF\u1B4C-\u1B4F\u1B7D-\u1B7F\u1BF4-\u1BFB\u1C38-\u1C3A\u1C4A-\u1C4C\u1C80-\u1CBF\u1CC8-\u1CCF\u1CF7\u1CFA-\u1CFF\u1DF6-\u1DFB\u1F16\u1F17\u1F1E\u1F1F\u1F46\u1F47\u1F4E\u1F4F\u1F58\u1F5A\u1F5C\u1F5E\u1F7E\u1F7F\u1FB5\u1FC5\u1FD4\u1FD5\u1FDC\u1FF0\u1FF1\u1FF5\u1FFF\u200B-\u200F\u202A-\u202E\u2060-\u206F\u2072\u2073\u208F\u209D-\u209F\u20BF-\u20CF\u20F1-\u20FF\u218C-\u218F\u23FB-\u23FF\u2427-\u243F\u244B-\u245F\u2B74\u2B75\u2B96\u2B97\u2BBA-\u2BBC\u2BC9\u2BD2-\u2BEB\u2BF0-\u2BFF\u2C2F\u2C5F\u2CF4-\u2CF8\u2D26\u2D28-\u2D2C\u2D2E\u2D2F\u2D68-\u2D6E\u2D71-\u2D7E\u2D97-\u2D9F\u2DA7\u2DAF\u2DB7\u2DBF\u2DC7\u2DCF\u2DD7\u2DDF\u2E43-\u2E7F\u2E9A\u2EF4-\u2EFF\u2FD6-\u2FEF\u2FFC-\u2FFF\u3040\u3097\u3098\u3100-\u3104\u312E-\u3130\u318F\u31BB-\u31BF\u31E4-\u31EF\u321F\u32FF\u4DB6-\u4DBF\u9FD6-\u9FFF\uA48D-\uA48F\uA4C7-\uA4CF\uA62C-\uA63F\uA6F8-\uA6FF\uA7AE\uA7AF\uA7B8-\uA7F6\uA82C-\uA82F\uA83A-\uA83F\uA878-\uA87F\uA8C5-\uA8CD\uA8DA-\uA8DF\uA8FE\uA8FF\uA954-\uA95E\uA97D-\uA97F\uA9CE\uA9DA-\uA9DD\uA9FF\uAA37-\uAA3F\uAA4E\uAA4F\uAA5A\uAA5B\uAAC3-\uAADA\uAAF7-\uAB00\uAB07\uAB08\uAB0F\uAB10\uAB17-\uAB1F\uAB27\uAB2F\uAB66-\uAB6F\uABEE\uABEF\uABFA-\uABFF\uD7A4-\uD7AF\uD7C7-\uD7CA\uD7FC-\uF8FF\uFA6E\uFA6F\uFADA-\uFAFF\uFB07-\uFB12\uFB18-\uFB1C\uFB37\uFB3D\uFB3F\uFB42\uFB45\uFBC2-\uFBD2\uFD40-\uFD4F\uFD90\uFD91\uFDC8-\uFDEF\uFDFE\uFDFF\uFE1A-\uFE1F\uFE53\uFE67\uFE6C-\uFE6F\uFE75\uFEFD-\uFF00\uFFBF-\uFFC1\uFFC8\uFFC9\uFFD0\uFFD1\uFFD8\uFFD9\uFFDD-\uFFDF\uFFE7\uFFEF-\uFFFB\uFFFE\uFFFF',
  'P': '\x21-\x23\x25-\\x2A\x2C-\x2F\x3A\x3B\\x3F\x40\\x5B-\\x5D\x5F\\x7B\x7D\xA1\xA7\xAB\xB6\xB7\xBB\xBF\u037E\u0387\u055A-\u055F\u0589\u058A\u05BE\u05C0\u05C3\u05C6\u05F3\u05F4\u0609\u060A\u060C\u060D\u061B\u061E\u061F\u066A-\u066D\u06D4\u0700-\u070D\u07F7-\u07F9\u0830-\u083E\u085E\u0964\u0965\u0970\u0AF0\u0DF4\u0E4F\u0E5A\u0E5B\u0F04-\u0F12\u0F14\u0F3A-\u0F3D\u0F85\u0FD0-\u0FD4\u0FD9\u0FDA\u104A-\u104F\u10FB\u1360-\u1368\u1400\u166D\u166E\u169B\u169C\u16EB-\u16ED\u1735\u1736\u17D4-\u17D6\u17D8-\u17DA\u1800-\u180A\u1944\u1945\u1A1E\u1A1F\u1AA0-\u1AA6\u1AA8-\u1AAD\u1B5A-\u1B60\u1BFC-\u1BFF\u1C3B-\u1C3F\u1C7E\u1C7F\u1CC0-\u1CC7\u1CD3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205E\u207D\u207E\u208D\u208E\u2308-\u230B\u2329\u232A\u2768-\u2775\u27C5\u27C6\u27E6-\u27EF\u2983-\u2998\u29D8-\u29DB\u29FC\u29FD\u2CF9-\u2CFC\u2CFE\u2CFF\u2D70\u2E00-\u2E2E\u2E30-\u2E42\u3001-\u3003\u3008-\u3011\u3014-\u301F\u3030\u303D\u30A0\u30FB\uA4FE\uA4FF\uA60D-\uA60F\uA673\uA67E\uA6F2-\uA6F7\uA874-\uA877\uA8CE\uA8CF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA95F\uA9C1-\uA9CD\uA9DE\uA9DF\uAA5C-\uAA5F\uAADE\uAADF\uAAF0\uAAF1\uABEB\uFD3E\uFD3F\uFE10-\uFE19\uFE30-\uFE52\uFE54-\uFE61\uFE63\uFE68\uFE6A\uFE6B\uFF01-\uFF03\uFF05-\uFF0A\uFF0C-\uFF0F\uFF1A\uFF1B\uFF1F\uFF20\uFF3B-\uFF3D\uFF3F\uFF5B\uFF5D\uFF5F-\uFF65',
  'S': '\\x24\\x2B\x3C-\x3E\\x5E\x60\\x7C\x7E\xA2-\xA6\xA8\xA9\xAC\xAE-\xB1\xB4\xB8\xD7\xF7\u02C2-\u02C5\u02D2-\u02DF\u02E5-\u02EB\u02ED\u02EF-\u02FF\u0375\u0384\u0385\u03F6\u0482\u058D-\u058F\u0606-\u0608\u060B\u060E\u060F\u06DE\u06E9\u06FD\u06FE\u07F6\u09F2\u09F3\u09FA\u09FB\u0AF1\u0B70\u0BF3-\u0BFA\u0C7F\u0D79\u0E3F\u0F01-\u0F03\u0F13\u0F15-\u0F17\u0F1A-\u0F1F\u0F34\u0F36\u0F38\u0FBE-\u0FC5\u0FC7-\u0FCC\u0FCE\u0FCF\u0FD5-\u0FD8\u109E\u109F\u1390-\u1399\u17DB\u1940\u19DE-\u19FF\u1B61-\u1B6A\u1B74-\u1B7C\u1FBD\u1FBF-\u1FC1\u1FCD-\u1FCF\u1FDD-\u1FDF\u1FED-\u1FEF\u1FFD\u1FFE\u2044\u2052\u207A-\u207C\u208A-\u208C\u20A0-\u20BE\u2100\u2101\u2103-\u2106\u2108\u2109\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A\u213B\u2140-\u2144\u214A-\u214D\u214F\u218A\u218B\u2190-\u2307\u230C-\u2328\u232B-\u23FA\u2400-\u2426\u2440-\u244A\u249C-\u24E9\u2500-\u2767\u2794-\u27C4\u27C7-\u27E5\u27F0-\u2982\u2999-\u29D7\u29DC-\u29FB\u29FE-\u2B73\u2B76-\u2B95\u2B98-\u2BB9\u2BBD-\u2BC8\u2BCA-\u2BD1\u2BEC-\u2BEF\u2CE5-\u2CEA\u2E80-\u2E99\u2E9B-\u2EF3\u2F00-\u2FD5\u2FF0-\u2FFB\u3004\u3012\u3013\u3020\u3036\u3037\u303E\u303F\u309B\u309C\u3190\u3191\u3196-\u319F\u31C0-\u31E3\u3200-\u321E\u322A-\u3247\u3250\u3260-\u327F\u328A-\u32B0\u32C0-\u32FE\u3300-\u33FF\u4DC0-\u4DFF\uA490-\uA4C6\uA700-\uA716\uA720\uA721\uA789\uA78A\uA828-\uA82B\uA836-\uA839\uAA77-\uAA79\uAB5B\uFB29\uFBB2-\uFBC1\uFDFC\uFDFD\uFE62\uFE64-\uFE66\uFE69\uFF04\uFF0B\uFF1C-\uFF1E\uFF3E\uFF40\uFF5C\uFF5E\uFFE0-\uFFE6\uFFE8-\uFFEE\uFFFC\uFFFD'
};

function sanitizeTyping(text, strict) {
  text = text.trim()
             .replace(/\s+/g, " ")
             .replace(new RegExp(RegexUnicode.C, "g"), ""); // control chars

  // https://cdnjs.cloudflare.com/ajax/libs/xregexp/3.1.1/xregexp-all.js
  if(!strict) {
    text = text.replace(/\(.*?\)/g, "")
               .replace(new RegExp('[' + RegexUnicode.P + RegexUnicode.S + ']', "g"), "") // punctuation, symbol
               .replace(/[-Ù‹Ù›]+/g, "");
  }
  return text;
}

function calculate_points_learn(score) {
  return 1 === score ? 45 : 0 === score ? 0 : Math.max(10, Math.round(45 * score) - 20);
}
function calculate_points_speed(time_spent) {
  var t = Math.floor(time_spent / 1e3);
  return t >= 6 ? Math.min(15, 25) : Math.min(15 + 7 * (6 - t), 25);
}
function calculate_points_review(points, current_streak) {
  points *= Math.pow(1.2, current_streak);
  points  = Math.min(points, 150);
  return Math.ceil(points);
}

function calculate_speed_bonus(time_spent, tpl) {
  if(tpl == "typing") {
    return time_spent < 4e3 ? 5 : 0;
  } else {
    return time_spent < 2e3 ? 3 : 0;
  }
}
function calculate_accuracy_bonus(percent_correct, num_scheduled_correct) {
  if(percent_correct == 100) {
    return 20 * num_scheduled_correct;

  } else if(percent_correct >= 90) {
    return 12 * num_scheduled_correct;

  } else if(percent_correct >= 80) {
    return 6 * num_scheduled_correct;

  } else if(percent_correct >= 70) {
    return 4 * num_scheduled_correct;

  } else if(percent_correct >= 50) {
    return 2 * num_scheduled_correct;

  } else {
    return 0;
  }
}

//+--------------------------------------------------------
//| HIGHLIGHT TEXT DIFF
//+--------------------------------------------------------

// https://codereview.stackexchange.com/questions/133586/a-string-prototype-diff-implementation-text-diff
// https://codereview.stackexchange.com/questions/133586/a-string-prototype-diff-implementation-text-diff
var diff = (function(){

  function rotate(arr, n){
    var len = arr.length;
    if (n % len === 0) {
      return arr.slice();
    }
    var res = new Array(arr.length)
    for (var i = 0; i < len; i++) {
      res[i] = arr[(i + (len + n % len)) % len];
    }
    return res;
  };

  // returns the first matching substring in-between the two strings
  function getMatchingSubstring(s,l,m){
    var i     = -1,
        n     = s.length,
        match = false,
        cd     = {fis:n, mtc:m, sbs:""}; // temporary object used to construct the cd (change data) object

    while (++i < n) {
      if(l[i] === s[i]) {
        if(match) {
          cd.sbs += s[i]; // o.sbs holds the matching substring itsef
        } else {
          match = true;
          cd.fis = i;
          cd.sbs = s[i];
        }
      } else if(match) {
        break; // stop after the first found substring
      }
    }
    return cd;
  }

  function getChanges(t,s,m,p){
    var isThisLonger, longer, shorter;

    // assignment of longer and shorter
    if(t.length >= s.length) {
      isThisLonger = true;
      longer       = t;
      shorter      = s;
    } else {
      isThisLonger = false;
      longer       = s;
      shorter      = t;
    }

    // get the index of first mismatching character in both strings
    var base_index = 0;
    while(shorter[base_index] === longer[base_index] && base_index < shorter.length) {
      base_index++;
    }

    // convert longer to array to be able to rotate it
    // shorter and longer now starts from the first mismatching character
    longer  = longer.split("").slice(base_index);
    shorter = shorter.slice(base_index);

    var len = longer.length,                   // length of the longer string
        cd = {fis: shorter.length,             // the index of matching string in the shorter string
              fil: len,                        // the index of matching string in the longer string
              sbs: "",                         // the matching substring itself
              mtc: m + s.slice(0,base_index)}, // if exists mtc holds the matching string at the front
        sub = {sbs:""};                       // returned substring per 1 character rotation of the longer string

    if(shorter !== "") {
      for(var rc = 0; rc < len && sub.sbs.length < p; rc++){             // rc -> rotate count, p -> precision factor
        sub = getMatchingSubstring(shorter, rotate(longer, rc), cd.mtc); // rotate longer string 1 char and get substring
        sub.fil = rc < len - sub.fis ? sub.fis + rc                      // mismatch is longer than the mismatch in short
                                     : sub.fis - len + rc;               // mismatch is shorter than the mismatch in short
        sub.sbs.length > cd.sbs.length && (cd = sub);                    // only keep the one with the longest substring.
      }
    }

    // insert the mismatching delete subsrt and insert substr to the cd object and attach the previous substring
    if(isThisLonger) {
      cd.del = longer.slice(0,cd.fil).join("");
      cd.ins = shorter.slice(0,cd.fis);
    } else {
      cd.del = shorter.slice(0,cd.fis);
      cd.ins = longer.slice(0,cd.fil).join("");
    }

    if(cd.del.indexOf(" ") == -1 || cd.ins.indexOf(" ") == -1) return cd;
    if(cd.del === "" || cd.ins === "" || cd.sbs === "") return cd;
    return getChanges(cd.del, cd.ins, cd.mtc, p);
  }

  function diff(txt1, txt2, p){
    p = p || 2; // p -> precision factor

    var cd       = getChanges(txt1,txt2,"",p),
        nextTxt2 = txt2.slice(cd.mtc.length + cd.ins.length + cd.sbs.length), // remaining part of "txt2"
        nextTxt1 = txt1.slice(cd.mtc.length + cd.del.length + cd.sbs.length), // remaining part of "txt1"
        result   = "";                                                        // the glorious result

    cd.del.length > 0 && (cd.del = '<span class = "deleted">'  + cd.del + '</span>');
    cd.ins.length > 0 && (cd.ins = '<span class = "inserted">' + cd.ins + '</span>');
    result = cd.mtc + cd.del + cd.ins + cd.sbs;

    if(nextTxt1 !== "" || nextTxt2 !== "") {
      result += diff(nextTxt1,nextTxt2,p);
    }
    return result;
  };

  return diff;
})();