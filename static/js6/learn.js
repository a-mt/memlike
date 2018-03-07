/** @jsx h */
'use strict';
const {h, Component, render} = window.preact;

/* global $ */
$(document).ready(function(){
  render(<Learn idCourse={window.$_URL.idCourse} level={window.$_URL.lvl} type={window.$_URL.type} thing={window.$_URL.thing} />, document.getElementById('learn-container'));
});

$.fn.random = function() {
  var randomIndex = Math.floor(Math.random() * this.length);
  return $(this[randomIndex]);
};

function range(start, stop, step=1){
  var arr = [start],
      i   = start;

  while(i < stop){
    i += step;
    arr.push(i);
  }
  return arr;
}

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

class Learn extends Component {
  state = { i: 0, n: 0, data: false, error: false, screen: false, recap: {}, level: 1, maxlevel: 1 };

  componentDidMount() {
    if(typeof this.props.level =="string" && this.props.level.indexOf('-')) {
      var range           = this.props.level.split('-');
      this.state.level    = parseInt(range[0]);
      this.state.maxlevel = parseInt(range[1]);
    } else {
      this.state.level    = parseInt(this.props.level);
      this.state.maxlevel = parseInt(this.props.level);
    }
    this.getData(this.state.level);
    window.warnbeforeunload = true;
  }
  componentDidUpdate(prevProps, prevState) {
    if(!this.init) {
      this.init = true;
    }
    window.imgZoom && window.imgZoom.reset();
    window.audioPlayer && window.audioPlayer.reset();

    // Automatically play first audio
    $('.autoplay .audio-player').random().trigger("click");

    if(!prevState.data || prevState.level != this.state.level) {
      document.getElementById('level-title').innerHTML = this.state.level + " - " + this.state.data.session.level.title;
    }
  }
  getData(level) {
    $.ajax({
      url: '/ajax/course/' + this.props.idCourse + '/' + level + '/' + this.props.type,
      success: function(data){
        if(!this.init) {
          this.bindEvents();
        }

        this.setState({
          recap: {},
          screen: false,
          error: false,
          level: level,

          data : data,
          i    : 0,
          n    : data.boxes.length
        });
      }.bind(this),
      error: function(xhr) {
        console.error(xhr.status + " " + xhr.statusText);
        this.setState({error: window.i18n.error });
      }.bind(this)
    });
  }
  bindEvents() {
    $(window).on('keyup', function(e){
      var key = e.which;

      // Press enter
      if(key == 13) {
        if(!this.expectChoice) {
          this.getNext();
        }

      // Press a choice number
      } else if(this.expectChoice && key >= 96 && key <= 105) {
        var char = parseInt(fromKeyCode(key));

        if(char < this.choices.length) {
          this.choose(char);
        }
      }
    }.bind(this));

    $('main').on('click', '.choice-box', function(e){
      this.choose(e.currentTarget.getAttribute('accesskey'));
    }.bind(this));

    window.onbeforeunload = function(e){
      if(!window.warnbeforeunload || this.state.recap) return;

      e = e || window.event;
      if (e) e.returnValue = 'Your changes will be lost.'; // IE, Firefox<4

      return 'Your changes will be lost.';
    }.bind(this);
  }

  choose(i) {
    var correct = (this.expectChoice == i);

    // Keep track of right/wrong answers
    var recap = Object.assign({}, this.state.recap),
        id    = this.state.data.boxes[this.state.i].learnable_id;
    if(!recap[id]) {
      recap[id] = {count: 0, ok: 0};
    }
    recap[id].count++;
    if(correct) {
      recap[id].ok++;
    }

    // Display correction
    this.setState({
      recap: recap,
      screen: "correction",
      correction: correct ? false : this.choices[parseInt(i)-1],
      kind: this.kind
    });
    this.expectChoice  = false;
  }
  getNext() {

    // Display next item
    if(this.state.i + 1 < this.state.n) {
      this.setState({
        i: this.state.i + 1,
        screen: false
      });

    // Display next level or go back to course's page
    } else if(this.state.screen == "recap"){
      if(this.state.level < this.state.maxlevel) {
        if(this.state.data) {
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
      }, function(){
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  render(props, state) {
    var percent = (state.n ? Math.ceil(state.i / state.n * 100) : 100);

    if(state.error) {
      return <div>{state.error}</div>;
    }
    if(!this.state.data) {
      return <div class="loading-spinner"></div>;
    }
    if(this.props.thing) {
      return this.render_presentation(this.props.thing);
    }
    var recap = (this.state.screen == "recap"),
        item  = (recap ? false : this.state.data.boxes[this.state.i]),
        tpl   = item.template,
        correct;

    if(this.state.screen == "correction") {
      tpl     = "presentation";
      correct = this.state.correction || true;
    }

    return <div>
        {/*<!-- PROGRESS BAR -->*/}
        <div class="progress-bar" role="progressbar" aria-valuenow={state.i} aria-valuemin="0" aria-valuemax={state.i}>
          <div class="counter">{state.i} / {state.n}</div>
          <div class="progress-bar-active" style={{'clip-path': 'polygon(0 0, '+percent+'% 0, '+percent+'% 100%, 0 100%)'}}>
            <div class="counter">{state.i} / {state.n}</div>
          </div>
        </div>

        {/*<!-- ITEM -->*/}
        {item && this['render_' + tpl](item.learnable_id, correct)}

        {recap && this.recap()}
      </div>;
  }
  render_sentinel(id) {
    var item       = this.state.data.screens[id].multiple_choice,
        inputKind  = item.prompt.text ? "text" : (item.prompt.img ? "img" : (item.prompt.audio ? "audio" : "video")),
        outputKind = item.answer.kind;

    this.kind = outputKind;

    // Randomize choices order
    var n          = item.choices.length,
        choicesRnd = randomize([...item.choices]);

    // Display 9 choices max
    if(n > 9) {
      n = 9;
      choicesRnd = choicesRnd.slice(0, n);
    }
    this.choices = choicesRnd;

    // Place the right answer somewhere in it
    var rnd = Math.random() * n - 1 | 0;

    return <div class="nicebox">
      <div class="big choice autoplay">{this._thing(item.prompt[inputKind], inputKind)}</div>
      <div class="medium choices">
        {choicesRnd.map((it, i) => {
          if(i == rnd) {
            this.expectChoice = i+1;
            it = item.answer.value;
          }
          return <div accesskey={i+1} class="choice-box nicebox" id={"choice-" + (i+1)}>
            <span class="choice-index">{i+1}.</span>
            {this._thingValue(it, outputKind)}
          </div>}
        )}
      </div>
    </div>;
  }
  displayCorrection(correction) {
    if(typeof correction == "boolean") {
      return <div class="alert alert-success">{window.i18n.correct_answer}!</div>;
    } else {
      return <div class="alert alert-danger">
        {window.i18n.wrong_answer}!&nbsp;
        <span>{window.i18n.your_answer_was}: <strong>{this._thingValue(correction, this.kind)}</strong></span>
      </div>;
    }
  }
  render_presentation(id, correction) {
    var item = this.state.data.screens[id].presentation;

    return <div>
    {correction && this.displayCorrection(correction)}
    <table class={"learn nicebox big thing" + (correction ? "": " autoplay")}>
        <tr>
          <td class="label">{item.item.label}</td>
          <td class="item">
            {this._thing(item.item)}
            {item.item.alternatives.map(alt => <div class="alt">{alt}</div>)}
          </td>
        </tr>
        <tr>
          <td class="label">{item.definition.label}</td>
          <td class="definition">
            {this._thing(item.definition)}
            {item.definition.alternatives.map(alt => <div class="alt">{alt}</div>)}
          </td>
        </tr>
        <tr class="sep"><td colspan="2"></td></tr>
        {item.audio && <tr>
          <td class="label">{item.audio.label}</td>
          <td class="audio">{this._thing(item.audio, "audio")}</td>
        </tr>}
        {item.visible_info.map(it => <tr>
          <td class="label">{it.label}</td>
          <td class="more">{this._thing(it)}</td>
        </tr>)}
        {item.hidden_info.map(it => <tr>
          <td class="label">{it.label}</td>
          <td class="more">{this._thing(it)}</td>
        </tr>)}
      </table>
    </div>;
  }
  _thingValue(it, kind) {
    return <span>{kind == "text" ? it
      : (kind == "image" ? <img src={it} class="text-image" />
      : (kind == "audio" ? <audio src={it} class="audio-player ico ico-l ico-audio"></audio>
      : ""))}</span>;
  }
  _thing(it, kind) {
    kind  = kind || it.kind;
    return <div class={kind}>
      {kind == "text" ? it.value
      : (kind == "image" ? <div class="media-list">{it.value.map(media => <img src={media} class="text-image" />)}</div>
      : (kind == "audio" ? <div class="media-list">{it.value.map(media => <audio src={media.normal} class="audio-player ico ico-l ico-audio"></audio>)}</div>
      : ""))}
    </div>;
  }
  recap() {
    var ids = {},
         tr = [];
    this.state.data.boxes.forEach((box) => {
      var id = box.learnable_id;
      if(ids[id]) return;

      var item = this.state.data.screens[id].presentation;
      ids[id] = 1;

      tr.push(<tr class="thing">
          <td>{this._thing(item.item)}</td>
          <td>{this._thing(item.definition)}</td>
          {this.props.type != "preview" && <td>{this.displayScore(this.state.recap[id])}</td>}
        </tr>);
    });
    return <table class="learn nicebox recap">{tr}</table>;
  }
  displayScore(recap) {
  if(!recap) {
    return <span>0/0</span>;
  }
  var err = recap.ok / recap.count * 100,
      className = "";
  if(err == 0) {
    className = "neverMissed";
  } else if(err > 80) {
    className = "oftenMissed";
  } else if(err < 20) {
    className = "rarelyMissed";
  } else {
    className = "sometimesMissed";
  }
  console.log(err);

  return <span class={className}>{recap.ok}/{recap.count}</span>;
  }
}