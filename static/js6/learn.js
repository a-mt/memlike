/** @jsx h */
'use strict';
const {h, Component, render} = window.preact;

/* global $ */
$(document).ready(function(){
  Object.freeze(window.course);
  render(<Learn level={window.$_URL.lvl} type={window.$_URL.type} thing={window.$_URL.thing} usesession={window.$_URL.usesession} />, document.getElementById('learn-container'));
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
//| Render game
//+--------------------------------------------------------

class Learn extends Component {
  state = { i: 0, n: 0, data: false, error: false, screen: false, recap: {}, level: 1, maxlevel: 1, level_type: 1, review_all: false };

  //+--------------------------------------------------------
  //| LIFECYCLE
  //+--------------------------------------------------------

  // Constructor
  constructor(props) {
    super(props);

    if(typeof this.props.level =="string") { // all
      this.state.level      = 1;
      this.state.maxlevel   = Object.keys(window.course.levels).length;
      this.state.review_all = (this.props.type == "classic_review" || this.props.type == "speed_review");
    } else {
      this.state.level    = parseInt(this.props.level);
      this.state.maxlevel = parseInt(this.props.level);
    }

    this.setMultipleChoices = this.setMultipleChoices.bind(this);
  }

  // Initialization: retrieve datas via AJAX then bind events
  componentDidMount() {
    this.getData(this.state.level, function(){ 

      window.onbeforeunload = this.warnbeforeunload.bind(this);

      // User clicks on a multiple choice answer
      $('main').on('click', '.choice-box', function(e){
        this.multiple_choice(e.currentTarget.getAttribute('accesskey'));
      }.bind(this));

      // Listen to keyboard inputs: next screen, multiple choice
      $(window).on('keyup', this.keyup.bind(this));

    }.bind(this));
  }

  // Every time screen gets updated
  componentDidUpdate(prevProps, prevState) {
    if(!this.init) {
      this.init = true;
    }

    // Reset image zoom and audio player
    window.imgZoom     && window.imgZoom.reset();
    window.audioPlayer && window.audioPlayer.reset();

    // Automatically play first audio
    $('.autoplay .audio-player').random().trigger("click");

    // Update level title
    if(!prevState.data || prevState.level != this.state.level) {
      document.getElementById('level-title').innerHTML = this.state.level + " - " + window.course.levels[this.state.level].name;
    }
  }

  // Retrieve the current level datas
  getData(level, callback) {
    var level_type = window.course.levels[level].type;
    $.ajax({
      url: '/ajax' + window.course.url
                   + (this.state.review_all ? 'all' : level) + '/'
                   + (level_type == 2 ? "media" : this.props.type),
      data: {
        session: this.props.usesession
      },
      success: function(data){
        callback && callback();

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
    if(this.state.recap || this.state.error) return;
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
      if(!this.expectChoice) {
        this.getNext();
      }

    // Press a number
    } else if(this.expectChoice && key >= 96 && key <= 105) {
      var char = parseInt(fromKeyCode(key));

      if(char <= this.choices.length) {
        this.multiple_choice(char);
      }
    }
  }

  //+--------------------------------------------------------
  //| GAME COMPUTATIONS
  //+--------------------------------------------------------

  // Multiple choice: User chooses a answer
  multiple_choice(i) {

    // Check if we got the right answer
    var idx    = parseInt(i)-1,
        choice = this.choices[idx].attributes;

    // getNormalPoints, getSpeedPoints
    this.choice_feedback(choice.value, choice.isValid, choice.isValid ? 1 : 0, choice.answerType, idx);
  }

  // Answer has been submitted and checked: give feedback
  choice_feedback(text, correct, score, kind, i) {

    // Count right and wrong answers
    var recap = Object.assign({}, this.state.recap),
        id    = this.state.data.boxes[this.state.i].learnable_id;
    if(!recap[id]) {
      recap[id] = {count: 0, right: 0, pos: Object.keys(recap).length};
    }
    recap[id].count++;
    if(correct) {
      recap[id].right++;
    }

    // Display correction
    if(this.props.type == "speed_review") {

      if(correct) {
        $("#choice-" + (i+1)).addClass("correct");
      } else {
        $("#choice-" + (i+1)).addClass("incorrect");

        for(var j=0; j<this.choices.length; j++) {
          if(this.choices[j].attributes.isValid) {
            $("#choice-" + (j+1)).addClass("correct");
            break;
          }
        }
      }
      this.expectChoice = false;
      this.choices      = false;
      this.state.recap  = recap;

      setTimeout(function(){
        $(".choice-box").removeClass("correct").removeClass("incorrect");
        this.getNext();
      }.bind(this), 500);

    } else {
      this.setState({
        recap: recap,
        screen: "correction",
        correct: correct ? false : {value: text, kind: kind}
      });
      this.expectChoice  = false;
      this.choices       = false;
    }
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
      if(!this.state.review_all && this.state.level < this.state.maxlevel) {
        if(this.state.data) {
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
      }, function(){
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  //+--------------------------------------------------------
  //| RENDERING
  //+--------------------------------------------------------

  setMultipleChoices(choices) {
    this.expectChoice = "numeric";
    this.choices      = choices;
  }

  render(props, state) {
    if(state.error) {
      if(state.error == 403) {
        return <p>{window.i18n._403} <a href="/login" class="link">{window.i18n.login}</a></p>;
      } else {
        return <p>{window.i18n.error}</p>;
      }
    }
    if(!this.state.data) {
      return <div class="loading-spinner"></div>;
    }
    if(this.props.thing) {
      return this.render_presentation(this.props.thing);
    }
    if(this.state.level_type == 2) {
      return this.markdown();
    }
    var recap   = (this.state.screen == "recap"),
        item    = (recap ? false : this.state.data.boxes[this.state.i]),
        percent = (state.n ? Math.ceil(state.i / state.n * 100) : 100),
        tpl     = item.template,
        correct;

    if(this.state.screen == "correction") {
      tpl     = "presentation";
      correct = this.state.correct || true;
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
    var item    = this.state.data.screens[id].multiple_choice,
        nChoice = (this.props.type == "speed_review" ? 4 : 9);

    return <Sentinel item={item} nChoice={nChoice} setChoices={this.setMultipleChoices} />;
  }
  render_presentation(id, correct) {
    var item = this.state.data.screens[id].presentation;

    return <Presentation item={item} correct={correct} />;
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
  var content = props.content;

  if(props.single) {
    switch(props.type) {
      case "text" : return <span>{content}</span>;
      case "image": return <img src={content} class="text-image" />;
      case "audio": return <audio src={content} class="audio-player ico ico-l ico-audio"></audio>;
    }
  } else {
    switch(props.type) {
      case "text" : return <div class="text">{content}</div>;
      case "image": return <div class="image"><div class="media-list">{content.map(media => <img src={media} class="text-image" />)}</div></div>;
      case "audio": return <div class="audio"><div class="media-list">{content.map(media => <audio src={media.normal} class="audio-player ico ico-l ico-audio"></audio>)}</div></div>;
    }
  }
};

const Presentation = function(props){
  var item = props.item,
  correct = props.correct;

	return <div>

    {/*-- Correction --*/}
    {correct && (typeof correct == "boolean"
      ? <div class="alert alert-success">{window.i18n.correct_answer}!</div>
      : <div class="alert alert-danger">
        {window.i18n.wrong_answer}!&nbsp;
        <span>{window.i18n.your_answer_was}: <strong><Value content={correct.value} type={correct.kind} single="1" /></strong></span>
      </div>)}

    {/*-- Content --*/}
    <table class={"learn nicebox big thing" + (correct ? "": " autoplay")}>

        {/*-- Item --*/}
        <tr>
          <td class="label">{item.item.label}</td>
          <td class="item">
            <Value content={item.item.value} type={item.item.kind} />
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
        {item.audio && <tr>
          <td class="label">{item.audio.label}</td>
          <td class="audio"><Value content={item.audio.value} type="audio" /></td>
        </tr>}

        {/*-- Additional content --*/}
        {item.visible_info.map(it => <tr>
          <td class="label">{it.label}</td>
          <td class="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {item.hidden_info.map(it => <tr>
          <td class="label">{it.label}</td>
          <td class="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {/*-- Attributs --*/}
        {item.attributes.map(it => <tr>
          <td class="label">{it.label}</td>
          <td class="more"><span class="badge"><Value content={it.value} type="text" single="1" /></span></td>
        </tr>)}
      </table>
    </div>;
};

const Sentinel = function(props) {
  var item       = props.item,
      itemType   = "text",
      answerType = item.answer.kind;

  if(item.prompt.img) itemType = "image";
  else if(item.prompt.audio) itemType = "audio";
  else if(item.prompt.video) itemType = "video";

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
  props.setChoices(choices);

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
    return <div accesskey={props.i} class="choice-box nicebox" id={"choice-" + props.i}>
      <span class="choice-index">{props.i}.</span>
      <Value content={props.value} type={props.answerType} single="1" />
    </div>;
  }
}

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
