/** @jsx h */
'use strict';
const {h, Component, render} = window.preact;

// Incorrectly configured build doesn't replace in-place process.env:
// ensure the js still works
var process = process || {};
process.env = process.env || {};

const build = {
  status: process.env.VAR,
  date: process.env.BUILD_DATE,
};

/* global $, window, document, console */
/* global setTimeout, setInterval, clearInterval, localStorage, Set */
$(document).ready(function(){
  if(window.MEMLIKE.garden.levels_index == '') {
    window.MEMLIKE.course.levels[1] = {'name': '', 'type': 1};
  }
  Object.freeze(window.MEMLIKE.course);
  Object.freeze(window.MEMLIKE.garden);

  window.MEMLIKE.session_settings = {
    'disable_multimedia': !!localStorage.getItem('session_settings_disable_multimedia'),
    'disable_tapping': !!localStorage.getItem('session_settings_disable_tapping'),
    'disable_typing': !!localStorage.getItem('session_settings_disable_typing'),
    'save_progress': !!window.MEMLIKE.garden.session_settings_save_progress,
    'reverse_prompt_and_answer': !!window.MEMLIKE.garden.session_settings_reverse_prompt_and_answer,
    'session_id': window.MEMLIKE.garden.session_id,
  };
  render(<Learn
    levels_index={window.MEMLIKE.garden.levels_index}
    session_type={window.MEMLIKE.garden.session_type}
    preview_thing_id={window.MEMLIKE.garden.preview_thing_id}
    session_id={window.MEMLIKE.garden.session_is_anonymous}
    course={window.MEMLIKE.course}
  />, document.getElementById('learn-container'));

  render(<LearnSettingsBtn
    session_type={window.MEMLIKE.garden.session_type}
  />, document.getElementById('learn-settings-btn'));
});

//+--------------------------------------------------------
//| Helper functions
//+--------------------------------------------------------

/**
 * Returns a random element from the current array
 */
$.fn.random = function() {
  var randomIndex = Math.floor(Math.random() * this.length);
  return $(this[randomIndex]);
};
Array.prototype.random = function(){
  var randomIndex = Math.floor(Math.random() * this.length);
  return this[randomIndex];
};

/**
* Returns an integer random number between min (included) and max (included)
* @param int min
* @param int max
* @return int
*/
function randrange(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Returns a new array, containing the elements of arr shuffled
 * @param array arr
 * @return array
 */
function randomize(arr){
 var c = arr.length, rnd;

 while(c){
  rnd = (Math.random() * c--) | 0;
  [arr[c], arr[rnd]] = [arr[rnd], arr[c]];
 }
 return arr;
}

/**
 * Returns the character corresponding to the keycode
 * @param int key
 * @return string char
 */
function fromKeyCode(key) {
  return String.fromCharCode((96 <= key && key <= 105)? key-48 : key);
}

/**
 * Create a Date object from a valid ISO 8601 string
 * @param string value
 * @return Date
 */
function decodeDateString(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Date) {
    return value;
  }
  var d = new Date(value);

  // invalid value: use now
  if (isNaN(d.getTime())) {
    return new Date();
  }
  return d;
}

//+--------------------------------------------------------
//| Settings
//+--------------------------------------------------------

class LearnSettingsModal extends Component {
  constructor(props) {
    super(props);

    this.state = {...window.MEMLIKE.session_settings};

    this.closeModal = this.closeModal.bind(this);
    this.updateSettings = this.updateSettings.bind(this);
  }
  closeModal() {
    window.modal.close();
  }
  updateSettings() {
    Object.assign(window.MEMLIKE.session_settings, this.state);
    localStorage.setItem('session_settings_disable_multimedia', this.state.disable_multimedia ? '1' : '');
    localStorage.setItem('session_settings_disable_tapping', this.state.disable_tapping ? '1' : '');
    localStorage.setItem('session_settings_disable_typing', this.state.disable_typing ? '1' : '');
    localStorage.setItem('session_settings_id', this.state.session_id || '');

    this.closeModal();
    window.GlobalEventEmitter.dispatch('update-settings', this.state);
  }

  handleChange(id) {
    this.setState({
      [id]: !this.state[id],
    });
  }

  render() {
    return <div className="settings learn-settings">
      <div className="form">
        <div>
          <input
            id="disable_typing"
            type="checkbox"
            defaultChecked={this.state.disable_typing}
            onChange={this.handleChange.bind(this, 'disable_typing')}
            autoComplete="off"
          />
          <label htmlFor="disable_typing">{window.I18N['learn_settings_disable_typing']}</label>
        </div>
        <div>
          <input
            id="disable_tapping"
            type="checkbox"
            defaultChecked={this.state.disable_tapping}
            onChange={this.handleChange.bind(this, 'disable_tapping')}
            autoComplete="off"
          />
          <label htmlFor="disable_tapping">{window.I18N['learn_settings_disable_tapping']}</label>
        </div>
        <div>
          <input
            id="disable_multimedia"
            type="checkbox"
            defaultChecked={this.state.disable_multimedia}
            onChange={this.handleChange.bind(this, 'disable_multimedia')}
            autoComplete="off"
          />
          <label htmlFor="disable_multimedia">{window.I18N['learn_settings_disable_multimedia']}</label>
        </div>
        <div>
          <input
            id="save_progress"
            type="checkbox"
            defaultChecked={this.state.save_progress}
            onChange={this.handleChange.bind(this, 'save_progress')}
            autoComplete="off"
          />
          <label htmlFor="save_progress">{window.I18N['learn_settings_save_progress']}</label>
        </div>
        <div>
          <input
            id="reverse_prompt_and_answer"
            type="checkbox"
            defaultChecked={this.state.reverse_prompt_and_answer}
            onChange={this.handleChange.bind(this, 'reverse_prompt_and_answer')}
            autoComplete="off"
          />
          <label htmlFor="reverse_prompt_and_answer">{window.I18N['learn_settings_reverse_prompt_and_answer']}</label>
        </div>
      </div>
      <div className="btn-group">
        <button className="btn" onClick={this.closeModal}>{window.I18N['cancel']}</button>
        <button className="btn green" onClick={this.updateSettings}>{window.I18N['save']}</button>
      </div>
    </div>
  }
}

class LearnSettingsBtn extends Component {
  constructor(props) {
    super(props);

    this.timerIsRunning = false;
    this.show = false;
    this.toggleSettings = this.toggleSettings.bind(this);
    this.onCloseModal = this.onCloseModal.bind(this);
  }
  onCloseModal() {
    window.modal.onclose('learn-settings', null);

    if(!this.show) {
      return;
    }
    this.show = false;
    Timer && Timer.continue();
  }
  toggleSettings() {
    this.show = !this.show;

    if(!this.show) {
      return;
    }
    Timer && Timer.pause();
    var div = window.modal.getContainer().get(0).querySelector('.modal');
    div.innerHTML = '';

    render(<LearnSettingsModal />, div);
    window.modal.reopen();
    window.modal.onclose('learn-settings', this.onCloseModal);
  }
  render() {
    if (this.props.session_type == 'preview') {
      return null;
    }
    return (
      <button className="settings-btn" type="button" onClick={this.toggleSettings} title={window.I18N.learn_settings}>
        <span className="ico ico-settings ico-l ico-grey"></span>
      </button>
    );
  }
}

//+--------------------------------------------------------
//| Speed review timer
//+--------------------------------------------------------

const Timer = {
  maxTime: 6e3,
  remainingTime: null,
  lastUpdate: null,
  target: null,
  interval: null,
  callback: null,
  isRunning: false,
  isPaused: false,

  stop: function(){
    Timer.interval && clearInterval(Timer.interval);

    if(!Timer.isRunning) {
      return;
    }
    var time = Date.now();

    // The user submitter an answer: tick a last time
    Timer.isRunning     = false;
    Timer.remainingTime -= (time - Timer.lastUpdate);
    Timer.lastUpdate     = time;
  },
  start: function(callback){
    Timer.callback      = callback;
    Timer.remainingTime = Timer.maxTime;
    Timer.lastUpdate    = Date.now();
    Timer.interval      = setInterval(Timer.tick.bind(this), 150);
    Timer.isRunning     = true;
    Timer.isPaused      = false;
  },
  getTime: function(){
    if (Timer.remainingTime === null) {
      return 0;
    }
    return Timer.maxTime - Math.max(Timer.remainingTime, 0);
  },
  pause: function() {
    if (Timer.isPaused) {
      return;
    }
    Timer.isPaused = true;
  },
  continue: function() {
    if (!Timer.isPaused) {
      return;
    }
    Timer.lastUpdate = Date.now();
    Timer.isPaused = false;
  },
  tick: function(){
    if(!Timer.isRunning || Timer.isPaused) {
      return;
    }
    var time = Date.now();
    Timer.remainingTime -= (time - Timer.lastUpdate);
    Timer.lastUpdate     = time;

    if(Timer.remainingTime <= 0) {
      clearInterval(Timer.interval);
      Timer.isRunning = false;

      $('#speed_review-timer').css('height', '100%');

      Timer.callback && setTimeout(Timer.callback, 300);
    } else {
      var percent = 1 - (Timer.remainingTime / Timer.maxTime);
      $('#speed_review-timer').css('height', (percent * 100) + '%');
    }
  }
};

//+--------------------------------------------------------
//| BUILDING STATE.DATA
//+--------------------------------------------------------

const LEARN_UNTIL_GROWTH_LEVEL = 6;
const LEARN_LASTDATE_TIMEOUT_SECONDS = 172800; // 2 * 24 * 3600 = 2 days ago
const LEARN_WITH_AUTOPLAY_AUDIO = 1;
const LEARN_BUILD_CHOICES_LENGTH = 12;

const TEST_DIFFICULTY = {
  'Unknown': 0,
  'Easy': 1,
  'Moderate': 2,
  'Hard': 3,
};

const REVIEW_INTERVAL_LADDER = [
  {interval: .1666, tolerance: .1},
  {interval: .5, tolerance: .3},
  {interval: 1, tolerance: .5},
  {interval: 6, tolerance: 1},
  {interval: 12, tolerance: 0},
  {interval: 24, tolerance: 0},
  {interval: 48, tolerance: 0},
  {interval: 96, tolerance: 0},
  {interval: 180, tolerance: 0},
];

/**
 * Build the session state
 * from the retrieved list of elements to learn
 */
const GameDataBuilder = {
  learnablesMap: {},
  sessionType: 'preview',

  shouldDisplayPresentation: function(learnableProgress) {
    if (!learnableProgress || !learnableProgress.last_date) {
      return true;
    }
    try {
      const lastDate = new Date(learnableProgress.last_date);
      const thresholdDate = new Date(Date.now() - LEARN_LASTDATE_TIMEOUT_SECONDS * 1000);
      return lastDate < thresholdDate;
    } catch(e) {
      console.error(e);
      return true;
    }
  },

  getScreenList: function(sessionType, learnables, progressMap) {
    var screens = [];

    switch(sessionType) {
      case 'learn':
        let testsToAdd = [];

        for (let learnable of learnables) {
          const learnableID = '' + learnable.id;
          const learnableProgress = progressMap[learnableID];

          if (GameDataBuilder.shouldDisplayPresentation(learnableProgress)) {
            screens.push({
              learnableID,
              template: 'presentation',
              learningGrowthLevel: 0,
            });
          }

          // How many times do we have to repeat the test to learn it
          const growthLevel = learnableProgress ? learnableProgress.growth_level : 0;

          const learningLevel = (growthLevel | 0) + 1;
          const targetLevel = Math.min((growthLevel | 0) + 3, LEARN_UNTIL_GROWTH_LEVEL);

          if (learningLevel > targetLevel) {
            console.warn('The following learnable has already been learned:', learnable);
          } else {
            testsToAdd.push({learnableID, learningLevel, targetLevel});
          }
        }

        // While there are still tests to add
        while(testsToAdd.length) {
          let testsToAdd_next = [];

          // For each learnable that have to be tested
          for(let i = 0; i < testsToAdd.length; i++) {
            let item = testsToAdd[i];
            let {learnableID, learningLevel, targetLevel} = item;

            // Get a random index to insert the test
            // 2 steps after the presentation of the learnable
            // or anywhere after the first test
            let idx = screens.findLastIndex((screen) => screen.learnableID == learnableID);
            let min = 0;
            let max = screens.length;
            let isPresentation = false;

            if (idx != -1) {
              min = idx;
              isPresentation = idx in screens && screens[idx].template == 'presentation';
            }
            let insertAtIndex = isPresentation ? Math.min(min + 2, max) : randrange(min, max);

            // Insert the test at the chosen random index
            screens.splice(insertAtIndex, 0, {
              learnableID,
              template: 'sentinel',
              learningGrowthLevel: learningLevel, // target growth level
            });

            // Do we still have to repeat the test to learn it
            learningLevel += 1;
            if (targetLevel >= learningLevel) {
              testsToAdd_next.push({learnableID, learningLevel, targetLevel});
            }
          }
          testsToAdd = testsToAdd_next;
        }
        break;

      case 'speed_review':
      case 'classic_review':
        for (let learnable of learnables) {
          screens.push({
            learnableID: '' + learnable.id,
            template: 'sentinel',
            learningGrowthLevel: 0,
          });
        }
        screens = randomize(screens);
        break;

      case 'preview':
      default:
        for (let learnable of learnables) {
          screens.push({
            learnableID: '' + learnable.id,
            template: 'presentation',
            learningGrowthLevel: 0,
          });
        }
        break;
    }
    return screens;
  },

  /**
   * Build the "data" to store in the current state
   * from the data retrieved from the backend
   *
   * @param string sessionType
   * @param dict data
   * @return dict
   */
  formatData: function(sessionType, data) {

    // Build screensTemplateMap (data.screensTemplateMap[learnableID][tpl][0])
    const screensTemplateMap = {};
    const learnablesMap = {};

    for (let learnable of data.learnables) {
      const screens = {};

      // A screen = {correct, is_strict, ...} (cf learning_session_preview.json)
      for (let screenID in learnable.screens) {
        let screen = learnable.screens[screenID];
        screens[screen.template] = [screen];
      }
      screensTemplateMap['' + learnable.id] = screens;
      learnablesMap['' + learnable.id] = learnable;
    }

    // Build progressMap {learnableID: {growth_level, current_streak, correct, attempts, is_difficult}}
    const progressMap = {};
    for (let item of data.progress) {
      progressMap['' + item.learnable_id] = Object.assign(item, {
        created_date: decodeDateString(item.created_date),
        next_date: decodeDateString(item.next_date),
        last_date: decodeDateString(item.last_date),
      });
    }

    const screens = GameDataBuilder.getScreenList(sessionType, data.learnables, progressMap);
    console.log('Screens:', screens);

    GameDataBuilder.sessionType = sessionType;
    GameDataBuilder.learnablesMap = learnablesMap;

    GameScreenBuilder.reset();
    GameProgressHandler.reset();

    return {
      screens,
      screensTemplateMap,
      progressMap,
      learnablesMap,
    }
  }
}

/**
 * Build new screens to accomodate our session settings
 * (inverted prompt/answer)
 */
const GameScreenBuilder = {
  definitions: null,

  reset: function() {
    GameScreenBuilder.definitions = null;
  },

  getDefinitions: function() {
    var learnables = Object.values(GameDataBuilder.learnablesMap);
    var list = [];

    for (let i=0; i<learnables.length; i++) {
      let learnable = learnables[i];
      let definition = learnable.screens['1'].definition;
      let hasTokens = learnable.definition_element_tokens;

      // text
      /**
        "id": 30664511848706,
        "learning_element": "die Auswertung",
        "definition_element": "l'évaluation",
        "learning_element_tokens": ["die", "Auswertung"],
        "definition_element_tokens": ["l", "évaluation"],
        "difficulty": "unknown",
        "item_type": "word",
      */
      if(hasTokens) {
        let value = learnable.definition_element;
        let valueSanitized = sanitizeTyping(value);

        if (valueSanitized) {
          list.push({value, valueSanitized});
        }
        definition.alternatives.forEach((value) => {
          let s = sanitizeTyping(value);

          if (s && ScoreAnswer.getStringDistance(valueSanitized, s) > 3) {
            list.push({value, valueSanitized: s});
          }
        });

      // others
      } else {
        /**
          "definition": {
            "label": "English",
            "kind": "text",
            "value": "l'évaluation",
            "alternatives": [],
            "style": [],
            "direction": "source",
            "markdown": false
          },
          "definition": {
            "label": "Audio",
            "kind": "audio",
            "value": [{
              "normal": "https://static.memrise.com/uploads/things/audio/36962605_140810_2048_20.mp3",
              "slow": null
            }],
            "alternatives": [],
            "style": [],
            "direction": "source",
            "markdown": false
          },
          "definition": {
            "label": "Brain",
            "kind": "image",
            "value": [
              "https://static.memrise.com/uploads/things/images/39867261_140924_0443_47.jpg",
              "https://static.memrise.com/uploads/things/images/39867261_140924_0444_07.jpg",
              "https://static.memrise.com/uploads/things/images/39867261_140924_0445_10.jpg"
            ],
            "alternatives": [],
            "style": [],
            "direction": "source",
            "markdown": false
          },
        */
        GameScreenBuilder.flattenValue(definition.value).forEach((value) => {
          list.push({value});
        });
        definition.alternatives.forEach((value) => {
          list.push({value});
        });
      }
    }
    return list;
  },

  getChoices: function(kind, correctChoices) {
    if (!GameScreenBuilder.definitions) {
      GameScreenBuilder.definitions = GameScreenBuilder.getDefinitions();
    }
    let choices = [];

    // Retrieve the definition of other learnables
    var definitions = GameScreenBuilder.definitions;
    console.log('Definitions', definitions, kind, value);

    if (definitions.length <= 15 || kind != 'text') {
      choices = randomize(definitions).filter((element) => correctChoices.indexOf(element.value) == -1);

    } else {
      var value = correctChoices[0],
          valueSanitized = sanitizeTyping(value),
          valueTokens = valueSanitized.split(' ').slice(0, 10);

      for (let i=0; i<definitions.length; i++) {
        let definition = definitions[i];
        if (!definition.valueSanitized || definition.valueSanitized == valueSanitized) {
          continue;
        }

        // Retrieve definitions that are fairly similar in length to our current word
        let itemTokens = definition.valueSanitized.split(' ');
        let X = valueTokens.map((token, i) => {
          return i < itemTokens.length ? Math.abs(token.length - itemTokens[i].length) : 1
        });
        let w = 1;
        let x = X.reduce((i, s) => s + i*(w += .5, w), 0) | 0;

        choices.push(Object.assign({weight: x}, definition));
      }
      choices = choices.sort((a, b) => a.weight - b.weight);
    }
    return choices.slice(0, LEARN_BUILD_CHOICES_LENGTH).map(item => item.value);
  },

  getInvertedPromptAndAnswer: function(screen) {
    var answerKind = screen.answer.kind;
    var promptKind = getPromptType(screen.prompt);

    return [
      {[answerKind]: screen.answer},
      screen.prompt[promptKind],
    ];
  },

  /**
   * Normalize value as a flat array of strings
   *
   * "value": "l'évaluation"
   * -> ["l'évaluation"]
   *
   * "value": [{
   *   "normal": "https://static.memrise.com/uploads/things/audio/36962605_140810_2048_20.mp3",
   *   "slow": null
   * }],
   * -> ["https://static.memrise.com/uploads/things/audio/36962605_140810_2048_20.mp3"]
   *
   * "value": [
   *   "https://static.memrise.com/uploads/things/images/39867261_140924_0443_47.jpg",
   *   "https://static.memrise.com/uploads/things/images/39867261_140924_0444_07.jpg",
   *   "https://static.memrise.com/uploads/things/images/39867261_140924_0445_10.jpg"
   * ]
   * -> idem
   */
  flattenValue: function(value) {
    const inner = function(value) {
      if (typeof value == 'string') {
        return [value];
      }
      if (value.normal) {
        return value.normal;
      }
      if (value.forEach && value.length > 0) {
        return value.map((s) => inner(s));
      }
      console.error('Dont know how to flatten this:', value);
    }
    return inner(value).flat();
  },

  buildScreen_reversed_multiple_choice: function(learnableScreens) {
    if ('reversed_multiple_choice2' in learnableScreens) {
      return true;
    }
    var screen = learnableScreens.multiple_choice[0];
    screen.template = 'reversed_multiple_choice2';
    [screen.prompt, screen.answer] = GameScreenBuilder.getInvertedPromptAndAnswer(screen);

    screen.correct = [];
    let value = GameScreenBuilder.flattenValue(screen.answer.value).forEach((value) => {
      screen.correct.push(value);
    });
    screen.answer.alternatives.forEach((value) => {
      screen.correct.push(value);
    });

    screen.choices = GameScreenBuilder.getChoices(
      screen.answer.kind,
      screen.correct,
    );
    learnableScreens['reversed_multiple_choice2'] = [screen];
    console.log('buildScreen_reversed_multiple_choice', screen, learnableScreens.reversed_multiple_choice[0]);
    return true;
  },

  buildScreen_reverse_typing: function(learnableScreens) {
    if ('reversed_typing' in learnableScreens) {
      return true;
    }
    var screen = learnableScreens.typing[0];
    screen.template = 'reversed_typing';
    [screen.prompt, screen.answer] = GameScreenBuilder.getInvertedPromptAndAnswer(screen);
    if (screen.answer.kind != 'text') {
      return false;
    }
    learnableScreens['reversed_typing'] = [screen];

    screen.correct = [];
    let value = GameScreenBuilder.flattenValue(screen.answer.value).forEach((value) => {
      screen.correct.push(value);
    });
    screen.answer.alternatives.forEach((value) => {
      screen.correct.push(value);
    });

    var tmp = sanitizeTyping(screen.answer.value).replace(' ', '').split('');
    screen.choices = randomize(Array.from(new Set(tmp)));
    console.log('buildScreen_reverse_typing', screen);
    return true;
  }
};

const GameProgressHandler = {
  events: [],
  is_saving: false,

  reset: function() {
    GameProgressHandler.events = [];
    GameProgressHandler.is_saving = false;
    $('#learn-settings-btn').removeClass('loading-spinner-before');
  },

  /**
   * Compute the next growh level for the given progress,
   * assuming the user gave the right answer
   *
   * @param dict learnableProgress
   * @param int growthLevel
   */
  getNextGrowthLevel: function(learnableProgress, difficulty=TEST_DIFFICULTY.Easy) {

    // FirstOnboardingSessionGrowthLevelStrategy
    if (GameDataBuilder.session_type == 'first_session') {
      return 2 === learnableProgress.growth_level ? LEARN_UNTIL_GROWTH_LEVEL : learnableProgress.growth_level + 1;
    }

    // StandardGrowthLevelStrategy
    if (true) {
      return learnableProgress.growth_level + 1;
    }

    // SuperchargeGrowthLevelStrategy
    return (
      learnableProgress.attempts === learnableProgress.correct
      && learnableProgress.growth_level < LEARN_UNTIL_GROWTH_LEVEL
      && (
          difficulty == TEST_DIFFICULTY.Easy && learnableProgress.growth_level >= 2
       || difficulty == TEST_DIFFICULTY.Moderate && learnableProgress.growth_level >= 3
      )
    ) ? LEARN_UNTIL_GROWTH_LEVEL : learnableProgress.growth_level + 1;
  },

  /**
   * Create a new date, with [interval] days added to date
   *
   * @param Date date
   * @param float interval (in days) - see REVIEW_INTERVAL_LADDER
   * @return Date
   */
  getDateIncrementedByInterval: function(date, interval) {
    const deltaFrom = 0,
          deltaTo = .007;

    if (!interval) {
      interval = deltaTo;
    }
    if (!date) {
      date = new Date();
    }
    interval += randrange(deltaFrom, deltaTo);

    return new Date(date.getTime() + 24 * interval * 3600 * 1000);
  },

  /**
   * Retrieve the index corresponding
   * to the given interval in the REVIEW_INTERVAL_LADDER (fuzzy)
   *
   * @param float interval
   * @return int index
   */
  getRungIndex: function(interval) {

    // Get the last rung greater than the given interval
    for (var i = REVIEW_INTERVAL_LADDER.length; i > 0 && REVIEW_INTERVAL_LADDER[--i | 0].interval > interval;) {
        // pass
    }
    // Return the rung no greather than the given interval
    return Math.max(i - 1 | 0, 0);
  },

  /**
   * Compute the interval and next_date for the given progress
   *
   * @param dict progress
   * @param Date date_answer
   * @param float score
   * @return dict
   */
  getNextIntervalDate: function(learnableProgress, dateAnswer, score) {

    // No review data until we learned the item
    if (learnableProgress.growth_level < LEARN_UNTIL_GROWTH_LEVEL) {
      return {
        interval : null,
        next_date: null,
      };
    }

    // We just learned the item: set the next review with the first interval
    if(!learnableProgress.interval
      || !learnableProgress.next_date
      || learnableProgress.interval < REVIEW_INTERVAL_LADDER[0].interval
    ) {
      var interval = REVIEW_INTERVAL_LADDER[0].interval;
      return {
        interval,
        next_date: GameProgressHandler.getDateIncrementedByInterval(dateAnswer, interval),
      }
    }

    var rungIndex = GameProgressHandler.getRungIndex(learnableProgress.interval | 0),
        tolerance = REVIEW_INTERVAL_LADDER[rungIndex].tolerance,
        reviewDate = new Date(learnableProgress.next_date.getTime() - 24 * tolerance * 3600 * 1000),
        isReviewDatePast = (new Date()).getTime() >= reviewDate.getTime();

    // We got the answer right but the item isn't due to review: keep the nextDate as-is
    var isCorrect = score == 1,
        isIncorrect = score == 0;

    if (isCorrect && !isReviewDatePast) {
      return {
        interval : learnableProgress.interval,
        next_date: learnableProgress.next_date,
      };
    }

    if (isIncorrect) {
      rungIndex = rungIndex > 2 ? 2 : rungIndex;
    } else if(isCorrect) {
      if(rungIndex === 1
        && learnableProgress.current_streak === learnableProgress.attempts
        && learnableProgress.current_streak > 0
      ) {
        rungIndex += 2;
      } else {
        rungIndex += 1;
      }
    } else { // nearly correct
      rungIndex = learnableProgress.current_streak > 0 ? rungIndex : Math.max(rungIndex - 1, 0);
    }

    var interval = REVIEW_INTERVAL_LADDER[rungIndex].interval;
    return {
      interval,
      next_date: GameProgressHandler.getDateIncrementedByInterval(dateAnswer, interval),
    }
  },

  /**
   * Compute whether the progress of the current learnable
   * is now considered to be difficult
   *
   * @param dict progress
   * @return bool
   */
  isDifficult: function(learnableProgress) {
    if (learnableProgress.ignored || learnableProgress.not_difficult) {
      return false;
    }
    if (learnableProgress.starred) {
      return true;
    }
    if (learnableProgress.attempts === 1 || learnableProgress.total_streak >= 3) {
      return false;
    }
    var ratio = learnableProgress.attempts > 0 ? learnableProgress.correct / learnableProgress.attempts : 1;

    return learnableProgress.attempts < 6 && ratio < .75 || learnableProgress.attempts >= 6 && ratio < .92
  },

  /**
   * Compute the attempts and streak for the given progress
   *
   * @param dict progress
   * @param float score
   * @return dict
   */
  getNextStreak: function(learnableProgress, score) {
    /*
      "when": 1771925218,
      "interval": 0.5,
      "total_streak": -1,
      "current_streak": 0,
      "correct": 11,
      "attempts": 12,
      "points": 0,
      "score": 0,
    */
    var isCorrect = score == 1;
    return {
      attempts       : learnableProgress.attempts + 1,
      correct        : learnableProgress.correct + (isCorrect ? 1 : 0),
      current_streak : isCorrect ? learnableProgress.current_streak + 1 : 0,
      total_streak   : Math.max(learnableProgress.total_streak + (isCorrect ? 1 : -1), 0),
    }
  },

  /**
   * Create a new progress object from the saved on
   * (send to memrise, will be used to trigger reviews)
   */
  getProgress: function(learnableID, savedProgress, score) {
    var progress = {
        learnable_id  : '' + learnableID,
        starred       : savedProgress.starred || false,
        ignored       : savedProgress.ignored || false,
        not_difficult : savedProgress.not_difficult || false,

        attempts      : savedProgress.attempts || 0,
        correct       : savedProgress.correct || 0,
        current_streak: savedProgress.current_streak || 0,
        total_streak  : savedProgress.total_streak || 0,

        created_date  : savedProgress.created_date || new Date(),
        last_date     : new Date(),
        next_date     : savedProgress.next_date || null,
        interval      : savedProgress.interval || null,
        growth_level  : savedProgress.growth_level || 0,
    };

    // Update the progress
    // progress.is_difficult = this.isDifficult(progress);
    progress.growth_level = score == 1 ? GameProgressHandler.getNextGrowthLevel(progress) : progress.growth_level;

    Object.assign(progress, GameProgressHandler.getNextIntervalDate(progress, progress.last_date, score));
    Object.assign(progress, GameProgressHandler.getNextStreak(progress, score));
    return progress;
  },

  // Send progress to memrise
  registerEvent: function(courseID, learnableID, event) {
    var learnable = GameDataBuilder.learnablesMap[learnableID] || {};

    if (String(learnable.id) !== learnableID) {
      console.error('Couldnt find learnable related to event', learnable, event);
      return;
    }

    // Replace our custom game data to be compatible with memrise
    if (event.box_template == 'reversed_multiple_choice2') {
      event.box_template = 'reversed_multiple_choice';

    } else if(event.box_template == 'reversed_typing') {
      event.box_template = 'typing';
      event.given_answer = (
        event.score == 0 ? '' : GameScreenBuilder.flattenValue(learnable.screens['1'].definition.value)[0]
      );
    }

    // Fluff up our event with required info
    var item = event;

    Object.assign(item, {
      course_id          : parseInt(courseID),
      learning_element   : learnable.learning_element,
      definition_element : learnable.definition_element,
    });

    if(item.created_date) {
      item.created_date = (item.created_date.getTime() / 1000) | 0;
    }
    if(item.next_date) {
      item.next_date = (item.next_date.getTime() / 1000) | 0;
    }
    if(item.last_date) {
      item.last_date = (item.last_date.getTime() / 1000) | 0;
    }
    item.when = item.last_date;

    console.log('Event', learnable, item);
    GameProgressHandler.events.push(item);
  },

  registerSessionEnd(data) {
    GameProgressHandler.is_saving = true;
    $('#learn-settings-btn').addClass('loading-spinner-before');

    var events = [...GameProgressHandler.events];
    var requests = [];
    console.log('Session end', data, events);

    // Send events in batches of 50
    while(events.length) {
      var batch = events.splice(0, 50);

      requests.push({
        url: '/ajax/register_progress',
        method: 'POST',
        data: JSON.stringify({
          events: batch,
        }),
        contentType: 'application/json',
      });
    }

    // Send session end
    requests.push({
      url: '/ajax/register_end',
      method: 'POST',
      data: JSON.stringify(data),
      contentType: 'application/json',
    });

    // Send each request one after the other
    function executeRequestsQueue() {
      if(!requests.length) {
        GameProgressHandler.is_saving = false;
        $('#learn-settings-btn').removeClass('loading-spinner-before');
        return;
      }
      var request = requests.shift();
      request.success = executeRequestsQueue;
      $.ajax(request);
    }
    executeRequestsQueue();
  }
};

//+--------------------------------------------------------
//| Render game
//+--------------------------------------------------------

class Learn extends Component {
  DISPLAY_DEBUG_SCREEN = false;

  session_settings = {};
  levels_index = [];

  level_data = false;
  level_summary_data = false;

  state = {
    level_i: 0,
    level_n: 0,
    level_type: 1,

    error: false,
    meta_screen: false,
    screen_i: 0,
    screen_n: 0,

    points: 0,
    hearts: 3,
    use_course_and_level_index: false,
  };

  //+--------------------------------------------------------
  //| LIFECYCLE
  //+--------------------------------------------------------

  // Constructor
  constructor(props) {
    super(props);

    const state = {};

    if (window.$_GET && window.$_GET.display_debug_screen) {
        this.DISPLAY_DEBUG_SCREEN = true;
    }

    // We're reviewing the entire course, rather than a specific level?
    if(typeof this.props.levels_index == 'string') { // all
      this.levels_index   = this.props.levels_index.split(',').map((i) => parseInt(i));

      state.level_i = this.levels_index[0] || 1;
      state.level_n = this.levels_index[this.levels_index.length-1] || 1;
      state.use_course_and_level_index = !(this.props.session_type != 'preview');  // request course | course_id_and_level_index
    } else {
      state.level_i = parseInt(this.props.levels_index);
      state.level_n = parseInt(this.props.levels_index);
      state.use_course_and_level_index = true;
    }
    this.session_settings   = {...window.MEMLIKE.session_settings};
    this.state = state;

    this.setChoices = this.setChoices.bind(this);
    this.onSessionSettingsUpdated = this.onSessionSettingsUpdated.bind(this);
  }

  onSessionSettingsUpdated(settings) {
    console.log('Session settings', settings);

    Object.assign(this.session_settings, settings);
  }

  // Initialization: retrieve datas via AJAX then bind events
  componentDidMount() {
    window.GlobalEventEmitter.subscribe('update-settings', this.onSessionSettingsUpdated);

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
    $('main').on('click', '.typing .button', function(e){
      this.parentNode.previousElementSibling.value += this.innerHTML;
      this.parentNode.previousElementSibling.focus();
    });

    // Tapping
    $('main').on('click', '.tapping .button', function(){
      var parent = this.parentNode;

      if(parent.className == 'keyboard') {
        parent.previousElementSibling.innerHTML += (
          '<button class="button" data-id="' + this.getAttribute('id') + '">' + this.innerHTML + '</button>'
        );
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
      window.audioPlayer && window.audioPlayer.play.call(this.querySelector('audio'), e, true);

    }).on('mouseleave', '.choice-box.audio', function(){
      window.audioPlayer && window.audioPlayer.pause.call(this.querySelector('audio'));
    });

    // Retrieve data
    this.getData(this.state.level_i, function(data){
      if(!this.props.preview_thing_id) {
        window.onbeforeunload = this.warnbeforeunload.bind(this);
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

    // Add text To Speech
    let ttsAdded = false;
    if(window.TTS) {
      $('.text[lang].tts').each(function(){
        var src = window.TTS.get_audio(this.innerText, this.getAttribute('lang'));

        if(src) {
          var $audio = $('audio', this);
          if($audio.length) {
            $audio.attr('src', src);

          } else {
            var k = Date.now();
            var elem = document.createElement('span');
            elem.innerHTML = `
              <audio id="audio-${k}" src=${src}></audio>
              <button type="button" data-id="audio-${k}" class="audio-player" aria-label="${window.I18N.play_audio}">
                <i class="ico ico-l ico-audio"></i>
              </button>`;

            this.appendChild(elem);
            ttsAdded = true;
          }
        }
      });
    }

    // Automatically play an audio track
    // if there aren't any audio elements in the course, try the tts instead (outside .audio elements)
    $('.autoplay .audio .audio-player').random().focus().trigger('click').length || (
      ttsAdded && $('.autoplay .audio-player').random().focus().trigger('click')
    );

    // Update level title
    if(this.state.use_course_and_level_index) {
      if(!prevState.level_i || prevState.level_i != this.state.level_i) {
        var name = '';
        var idx = this.state.level_i;

        if (idx < 1) {
          idx += 1;
        }
        if (idx in this.props.course.levels) {
          name = this.props.course.levels[idx].name;
        }
        var title = idx + (name ? ' - ' + name : '');
        document.getElementById('level-title').innerHTML = title;
      }
    }

    // Start the timer
    if(this.state.meta_screen != 'correction') {
      if(this.props.session_type == 'speed_review'){
        Timer.start(this.time_over.bind(this));
      }
    }

    // Debug screen
    if (this.DISPLAY_DEBUG_SCREEN) {
      $('#debug-screen').on('click', 'li', function(e){
        if(e.target.classList.contains('disabled')) return;

        this.setState({
          debug_screen: e.target.innerHTML == 'default' ? false : e.target.innerHTML
        });
      }.bind(this));
    }
  }

  /**
   * Retrieve the current level data
   */
  getData(level_i, callback) {
    const session_type = this.props.session_type;

    // Retrieve level type
    var level_type = 1;
    if (level_i == 0) {
      level_i = 1;
    }
    if (level_i == 1 && !this.props.course.levels.length) {
      // pass
    } else if (!(level_i in this.props.course.levels)) {
      console.error('Level data cannot be retrieved');
      return this.setState({error: 1});
    } else {
      level_type = this.props.course.levels[level_i].type;
    }

    var url = '/ajax' + this.props.course.url;
    if(!this.state.use_course_and_level_index) {
      url += 'all/' + session_type;
    } else if(level_type == 2) {
      url += level_i + '/media';
    } else {
      url += level_i + '/' + session_type;
    }

    $.ajax({
      url: url,
      data: { session: this.props.session_id },
      success: function(data){
        callback && callback(data);

        let gameData = GameDataBuilder.formatData(session_type, data);
        let error = false;

        if (!gameData.screens.length) {
          switch (session_type) {
            case 'learn':
              error = window.I18N.learn_err_empty_learn;
              break;

            case 'preview':
              error = window.I18N.learn_err_empty_preview;
              break;

            case 'review':
              error = window.I18N.learn_err_empty_review;
              break;

            default:
              error = window.I18N.learn_err_empty;
              break;
          }
        }

        this.level_data = gameData;
        this.level_summary_data = {
          nb_scheduled_correct: 0,
          nb_scheduled: 0,
          speed_bonus: 0,
          learnables: {},
        };

        this.setState({
          meta_screen : false,
          error,
          level_i,
          level_type,
          points   : 0,
          screen_i : 0,
          screen_n : (gameData.screens ? gameData.screens.length : 1),
        });
      }.bind(this),

      error: function(xhr) {
        if(xhr.status == 403) {
          this.setState({error: 403});
        } else {
          console.error(xhr.status + ' ' + xhr.statusText);
          this.setState({error: 500});
        }
      }.bind(this),
    });
  }

  //+--------------------------------------------------------
  //| EVENTS
  //+--------------------------------------------------------

  // Trigger warning when user closes tab
  warnbeforeunload(e) {
    if(GameProgressHandler.is_saving) {
      // pass
    } else if(this.state.meta_screen == 'summary' || this.state.error) {
      return;
    }
    var msg = 'Your changes will be lost.';

    e = e || window.event;
    if (e) { // IE, Firefox < 4
      e.returnValue = msg;
    }
    return msg;
  }

  expectedSubmit() {
    var expectChoice = this.expectChoice;
    if (expectChoice === null) {
      return false;
    }
    this.expectChoice = null;
    return expectChoice;
  }

  // Listen to keyboard inputs: next screen, multiple choice answer
  keyup(e) {
    var key = e.which;

    // Press enter
    if(key == 13) {
      if(e.target.classList.contains('button') || e.target.classList.contains('choice-box')) {
        if(!e.target.classList.contains('disabled')) {
          e.target.click();
        }
        return;
      }
      return this.handle_submit(e);
    }

    // Multiplice choice: press a number
    if(this.expectChoice == 'numeric' && key > 96 && key <= 105) {
      var char = parseInt(fromKeyCode(key));

      if(char > this.choices.length) {
        return;
      }
      this.multiple_choice(char);
    }
  }

  handle_submit(e) {

    // Presentation
    if(!this.expectChoice) {
      this.getNext();

    // Typing
    } else if(this.expectChoice == 'text') {
      this.choice($('.typing input').val() || '');

    // Tapping
    } else if(this.expectChoice == 'tapping') {
      var chosen = [];
      $('.tapping .input button').each(function(){
        chosen.push(this.innerHTML);
      });
      this.tapping_choice(chosen);

    // Numeric
    } else {
      console.info('Skipping', this.expectChoice);
      this.skip_choice();
    }
  }

  //+--------------------------------------------------------
  //| GAME COMPUTATIONS
  //+--------------------------------------------------------

  // Multiple choice: User chooses a answer
  multiple_choice(i) {
    if(this.state.meta_screen == 'lost') {
      return;
    }
    Timer.stop();

    // Check if we got the right answer
    var idx    = parseInt(i)-1,
        choice = idx < this.choices.length ? this.choices[idx].attributes : '';

    // getNormalPoints, getSpeedPoints
    this.choice_feedback({
      value : choice.value,
      score : choice.isValid ? 1 : 0,
      kind  : choice.answerType,
      i     : idx
    });
  }

  skip_choice() {
    Timer.stop();

    this.time_over();
  }

  time_over() {
    this.choice_feedback({
      value : '',
      score : 0,
      kind  : ''
    });
  }

  // Text entry: User submit its answer
  choice(givenAnswer) {
    givenAnswer = givenAnswer.trim();

    var sanitizedGivenAnswer = sanitizeTyping(givenAnswer, this.is_strict).toLowerCase();

    var score   = 0,
        correctAnswer = '';

    // Text input
    for(let i=0; i<this.choices.length; i++) {
      var choice = this.choices[i].toLowerCase().trim(),
          s      = ScoreAnswer.computeScore(sanitizedGivenAnswer, choice);

      if(s && s > score) {
        score = s;
        correctAnswer = choice;
      }
    }

    this.choice_feedback({
      value    : givenAnswer,
      testValue: sanitizedGivenAnswer,
      refValue : correctAnswer,
      score    : score,
      kind     : 'text'
    });
  }

  // Tapping: User order words
  tapping_choice(entry) {
    var isValid = 0;
    entry = entry.join(' ').trim();

    for(var i=0; i<this.choices.length; i++) {
      if(entry == this.choices[i].join(' ').trim()) {
        isValid = 1;
        break;
      }
    }

    this.choice_feedback({
      value : entry,
      score : isValid ? 1 : 0,
      kind  : 'text'
    });
  }

  // Answer has been submitted and checked: compute progress, points & give feedback
  // input: {value,score,kind,...rest}
  choice_feedback(input) {
    Timer.stop();

    if(!this.level_data) {
      return;
    }
    var learnableID = this.level_data.screens[this.state.screen_i].learnableID;

    // Update the streak status and next review data
    // Values from this object are incremented each time this learnable is learned
    // and retrieved from the backend at the beginning of the learning session
    var progress = GameProgressHandler.getProgress(
      learnableID,
      this.level_data.progressMap[learnableID] || {},
      input.score,
    );
    this.level_data.progressMap[learnableID] = progress;

    // Update the earned points
    var current_streak = progress.current_streak;
    var isCorrect = input.score == 1;

    var time_spent = 0;
    if (this.props.session_type == 'speed_review') {
      time_spent = Timer.getTime();

      if (!isCorrect) {
        this.state.hearts -= 1;
      }
    }
    var points = AwardPoints.getPoints(
      this.props.session_type,
      this.template,
      time_spent,
      input.score,
      current_streak,
    );

    // Values from this object are send to the backend for stats
    // But don't have an impact for the next learning session
    var event = {
        learnable_id : learnableID,
        box_template : this.template,
        given_answer : input.value,
        score        : input.score,
        time_spent   : time_spent,
        points       : points,
        bonus_points : 0,
    };
    this.session_settings.save_progress && GameProgressHandler.registerEvent(
      this.props.course.id,
      learnableID,
      Object.assign(event, progress),
    );

    // Count right and wrong answers
    this.level_summary_data.nb_scheduled += 1;
    this.level_summary_data.nb_scheduled_correct += (isCorrect ? 1 : 0);

    var learnablesSummary = this.level_summary_data.learnables;
    if(!learnablesSummary[learnableID]) {
      learnablesSummary[learnableID] = {
        count: 0,
        right: 0,
        pos: Object.keys(learnablesSummary).length,
      };
    }
    learnablesSummary[learnableID].count++;
    if(isCorrect) {
      learnablesSummary[learnableID].right++;
    }

    // Display correction
    if(this.props.session_type == 'speed_review') {
      this.show_correct(input);

      if(this.state.hearts == 0) {
        this.state.meta_screen = 'lost';
        this.state.error  = 1;

        $(document.body).append(`<div class="overlay">
          <div class="no-heart"></div>
          <p class="overlay-text">${window.I18N.no_more_hearts} !</p>
          <div class="btn-group">
            <a href="${window.MEMLIKE.garden.session_origin_url}">${window.I18N.return}</a>
            <a href="${window.location.href}">${window.I18N.replay}</a>
          </div>
        </div>`);

        return;
      }

      // We intentionally don't update the state, so that componentDidUpdate isn't called
      this.state.points += event.points;

      setTimeout(function(){
        $('.choice-box').removeClass('correct').removeClass('incorrect');
        this.getNext();
      }.bind(this), isCorrect ? 500 : 3000);

    } else {
      this.level_summary_data.speed_bonus += event.bonus_points;

      this.setState({
        meta_screen: 'correction',
        correct: input,
        debug_screen: false,
        points: this.state.points + event.points,
      });
    }
  }

  show_correct(input) {
    if('i' in input) {
      $('#choice-' + (input.i+1)).addClass(input.score == 1 ? 'correct' : 'incorrect');
    }
    if(input.score != 1) {
      for(var j=0; j<this.choices.length; j++) {
        if(this.choices[j].attributes.isValid) {
          $('#choice-' + (j+1)).addClass('correct');
          break;
        }
      }
    }
  }

  // Display next screen
  getNext() {

    // Next item
    if(this.state.screen_i + 1 < this.state.screen_n) {
      this.setState({
        screen_i: this.state.screen_i + 1,
        meta_screen: false
      });

    // After displaying the summary: display the next level or go back to the course
    } else if(this.state.meta_screen == 'summary' || this.state.level_type == 2){
      if(this.state.use_course_and_level_index && this.state.level_i < this.state.level_n) {
        if(this.level_data) {
          this.level_data = false;
          this.getData(this.levels_index[this.levels_index.indexOf(this.state.level_i) + 1]);
        }
      } else {
        this.state.error = 1; // prevent warning
        window.location.href = window.MEMLIKE.garden.session_origin_url;
      }

    // Summary
    } else {
      var data = {
        session_points: this.state.points,
        //session_bonus_points : this.level_summary_data.speed_bonus + computePoints_bonusForAccuracy(this.level_summary_data.nb_scheduled_correct / this.level_summary_data.nb_scheduled * 100, this.level_summary_data.nb_scheduled),
        session_type: this.props.session_type == 'classic_review' ? 'review' : this.props.session_type,
        session_source_type: this.state.use_course_and_level_index ? 'course_id_and_level_index' : 'course',
        session_source_id: this.props.course.id,
      };
      if (this.state.use_course_and_level_index) {
        data.session_source_sub_index = this.state.level_i;
      }
      this.session_settings.save_progress && GameProgressHandler.registerSessionEnd(data);

      this.setState({
        screen_i: this.state.screen_n,
        meta_screen: 'summary'
      }, function(){
        window.imgZoom && window.imgZoom.reset();
      });
    }
  }

  //+--------------------------------------------------------
  //| RENDERING
  //+--------------------------------------------------------

  resetChoices() {
    this.expectChoice  = false;
    this.choices       = false;
  }

  setChoices(choices, type, is_strict) {
    this.expectChoice = type; // numeric | text | tapping
    this.choices      = choices;
    this.is_strict    = is_strict || 1;
  }

  render() {

    // Something went wrong
    if(this.state.error) {
      if(this.state.error == 403) {
        return <p>{window.I18N._403} <a href="/login" className="link">{window.I18N.login}</a></p>;
      } else if (typeof this.state.error == 'string') {
        return <p>{this.state.error}</p>;
      } else {
        return <p>{window.I18N.error}</p>;
      }
    }

    // Loading data
    if(!this.state.meta_screen && !this.state.screen_n) {
      return <div className="loading-spinner"></div>;
    }

    // Preview thing
    if(this.props.preview_thing_id) {
      if(this.state.debug_screen) {
        return this.screen();
      } else {
        return <div>
          {this.DISPLAY_DEBUG_SCREEN ? this.addBoxDebugMenu() : null}
          {this.render_presentation(false)}
        </div>;
      }
    }

    // Media level
    if(this.state.level_type == 2 && this.state.use_course_and_level_index) {
      return this.markdown();
    }

    // Summary
    if(this.state.meta_screen == 'summary') {
      return <div>{this.addStats()}{this.screen()}</div>;
    }

    // Default
    return <div>
      {this.DISPLAY_DEBUG_SCREEN && this.addBoxDebugMenu()}

      {/* POINTS, HEARTS, PROGRESS BAR */}
      {this.addStats()}

      {/* SCREEN */}
      {this.props.session_type == 'speed_review'
        ? <div className="speed_review"><div id="speed_review-timer" key={Date.now()}></div>{this.screen()}</div>
        : this.screen()}

      <span className="btn submit" tabIndex="0">{window.I18N.next}</span>
    </div>;
  }

  addStats() {
    var percent = (this.state.screen_n ? Math.ceil(this.state.screen_i / this.state.screen_n * 100) : 100);

    return <div className="progress-stats">
      {this.props.session_type == 'speed_review' &&
        <div className="hearts-wrapper">{[1,2,3].map((i) => (
          <span key={i} className={'heart ' + (i <= this.state.hearts ? 'full' : 'empty')}></span>
          ))}
        </div>}
      <div className="points-num">{this.state.points}</div>

      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={this.state.screen_i}
        aria-valuemin="0"
        aria-valuemax={this.state.screen_i}
      >
        <div className="counter">{this.state.screen_i} / {this.state.screen_n}</div>
        <div className="progress-bar-active" style={{'clip-path': 'polygon(0 0, '+percent+'% 0, '+percent+'% 100%, 0 100%)'}}>
          <div className="counter">{this.state.screen_i} / {this.state.screen_n}</div>
        </div>
      </div>
    </div>;
  }

  addBoxDebugMenu() {
    var item    = this.level_data.screens[this.state.screen_i],
        screen  = this.level_data.screensTemplateMap[item.learnableID],
        current = this.state.debug_screen;

    return <ul id="debug-screen">
      <li className={current ? '' : 'active'}>default</li>
      <li className={('multiple_choice' in screen && screen.multiple_choice ? '' : 'disabled')
              + (current == 'multiple_choice' ? ' active' : '')}>
        multiple_choice
      </li>
      <li className={('typing' in screen && screen.typing ? '' : 'disabled')
              + (current == 'typing' ? ' active' : '')}>
        typing
      </li>
      <li className={('reversed_multiple_choice' in screen && screen.reversed_multiple_choice ? '' : 'disabled')
              + (current == 'reversed_multiple_choice' ? ' active' : '')}>
        reversed_multiple_choice
      </li>
      <li className={('audio_multiple_choice' in screen && screen.audio_multiple_choice ? '' : 'disabled')
              + (current == 'audio_multiple_choice' ? ' active' : '')}>
        audio_multiple_choice
      </li>
      <li className={('tapping' in screen && screen.tapping ? '' : 'disabled')
              + (current == 'tapping' ? ' active' : '')}>
        tapping
      </li>
      <li className={('typing' in screen && screen.typing ? '' : 'disabled')
              + (current == 'copytyping' ? ' active' : '')}>
        copytyping
      </li>
      <li className={('typing' in screen && screen.typing.audio ? '' : 'disabled')
              + (current == 'audio_typing' ? ' active' : '')}>
        audio_typing
      </li>
      <li className={('reversed_multiple_choice' in screen && screen.reversed_multiple_choice[0].prompt.video ? '' : 'disabled')
              + (current == 'reversed_multiple_choice_prompt_video' ? ' active' : '')}>
        reversed_multiple_choice_prompt_video
      </li>
      <li className={('multiple_choice' in screen && screen.multiple_choice[0].prompt.video ? '' : 'disabled')
              + (current == 'video-pre-presentation' ? ' active' : '')}>
        video-pre-presentation
      </li>
      <li className={(screen.presentation ? '' : 'disabled')
              + (current == 'presentation' ? ' active' : '')}>
        presentation
      </li>
    </ul>;
  }

  screen() {
    this.resetChoices();

    if(!this.level_data) {
      return null;
    }
    if(this.state.debug_screen) {
      switch(this.state.debug_screen) {
        case 'multiple_choice'         : return this.render_tpl({ template: 'multiple_choice' });
        case 'typing'                  : return this.render_tpl({ template: 'typing' });
        case 'reversed_multiple_choice': return this.render_tpl({ template: 'reversed_multiple_choice' });
        case 'audio_multiple_choice'   : return this.render_tpl({ template: 'audio_multiple_choice' });
        case 'tapping'                 : return this.render_tpl({ template: 'tapping' });
        case 'copytyping'              : return this.render_tpl({ template: 'copytyping' });
        case 'audio_typing'            : return this.render_tpl({ template: 'typing', promptWith: 'audio' });
        case 'reversed_multiple_choice_prompt_video': return this.render_tpl({ template: 'reversed_multiple_choice', promptWith: 'video' });
        case 'video-pre-presentation'  : return this.render_tpl({ template: 'multiple_choice', promptWith: 'video' });
        case 'presentation'            : return this.render_tpl({ template: 'presentation' });
      }
    }
    if(this.state.meta_screen == 'summary') {
      return this.summary();
    }
    if(this.state.meta_screen == 'correction') {
      return this.render_presentation(this.state.correct || true);
    }

    // No defined screen: display next learnable
    const item = this.level_data.screens[this.state.screen_i];
    if(!item) {
      console.log('No item to display', this.level_data.screens, this.state.screen_i);
      return null;
    }
    const screens = this.level_data.screensTemplateMap[item.learnableID];
    if(!screens) {
      console.log('No screen to display', this.level_data.screensTemplateMap, item);
      return null;
    }
    console.log('Screen', item, screens);

    if(item.learningGrowthLevel) {
      switch(item.learningGrowthLevel) {
        case 1:
            return this.render_tpl({
              template: 'multiple_choice',
              nChoices: 4
            });

        case 2:
          if(screens.reversed_multiple_choice.video && !this.session_settings.disable_multimedia) {
            return this.render_tpl({
              template: 'reversed_multiple_choice',
              nChoices: 4,
              promptWith: 'video'
            });
          }
          if(screens.audio_multiple_choice && Math.random() > .5 && !this.session_settings.disable_multimedia) {
            return this.render_tpl({
              template: 'audio_multiple_choice'
            });
          }
          if(screens.tapping && !this.session_settings.disable_tapping) {
            return this.render_tpl({
              template: 'tapping',
              difficulty: 0
            });
          }
          return this.render_tpl({
            template: 'reversed_multiple_choice',
            nChoices: 4
          });

        case 3:
          if(screens.tapping && !this.session_settings.disable_tapping) {
            return this.render_tpl({
              template: 'tapping',
              difficulty: .5
            });
          }
          if(screens.typing && !this.session_settings.disable_typing) {
            return this.render_tpl({
              template: 'typing'
            });
          }
          return this.render_tpl({
            template: 'multiple_choice',
            nChoices: 9
          });

        case 4:
          if(screens.multiple_choice.video && !this.session_settings.disable_multimedia) {
            return this.render_tpl({
              template: 'reversed_multiple_choice',
              nChoices: 4,
              promptWith: 'video'
            });
          }
          if(Math.random() > .5 && !this.session_settings.disable_multimedia) {
            var s = [];
            if(screens.typing.audio && !this.session_settings.disable_typing) {
              s.push({
                template: 'typing',
                promptWith: 'audio'
              });
            }
            if(screens.reversed_multiple_choice.audio && !this.session_settings.disable_multimedia) {
              s.push({
                template: 'reversed_multiple_choice',
                nChoices: 4,
                promptWith: 'audio'
              });
            }
            if(s.length > 0) {
              return this.render_tpl(s.random());
            }
          }
          return this.render_tpl({
            template: 'reversed_multiple_choice',
            nChoices: [4, 6].random()
          });

        case 5:
          if(screens.taping && !this.session_settings.disable_tapping) {
            return this.render_tpl({
              template: 'tapping',
              difficulty: .5
            });
          }
          return this.render_tpl({
            template: 'multiple_choice',
            nChoices: [6, 9].random()
          });

        default:
          if(screens.typing && !this.session_settings.disable_typing) {
            return this.render_tpl({
              template: 'typing'
            });
          }
          return {
            template: 'multiple_choice',
            nChoices: 9
          };
      }
    }

    if(this.props.session_type == 'speed_review') {
      if(this.session_settings.reverse_prompt_and_answer && screens.reversed_multiple_choice) {
        return this.render_tpl({
          template: 'reversed_multiple_choice',
          nChoices: 4
        });
      }
      return this.render_tpl({
        template: 'multiple_choice',
        nChoices: 4
      });
    }

    if (item.template == 'sentinel') {

      // Reversing Question on the answer, answer with the question
      if(this.session_settings.reverse_prompt_and_answer) {
        if(screens.typing
          && !this.session_settings.disable_typing
          && GameScreenBuilder.buildScreen_reverse_typing(screens)
        ) {
          return this.render_tpl({
            template: 'reversed_typing',
          });
        }
        return this.render_tpl({
            template: (GameScreenBuilder.buildScreen_reversed_multiple_choice(screens), 'reversed_multiple_choice2'),
            nChoices: 9
        });
      }

      if(screens.typing && !this.session_settings.disable_typing) {
        return this.render_tpl({
          template: 'typing',
        });
      }
      if(screens.audio_multiple_choice && Math.random() > .5 && !this.session_settings.disable_multimedia) {
        return this.render_tpl({
          template: 'audio_multiple_choice'
        });
      }
      return this.render_tpl({
          template: 'multiple_choice',
          nChoices: 9
      });
    }

    return this.render_tpl({ template: item.template });
  }

  render_tpl(setting) {
    this.template = setting.template;

    switch(setting.template) {
      case 'multiple_choice': return this.render_multiple_choice(setting);
      case 'reversed_typing': return this.render_reversed_typing(setting);
      case 'typing': return this.render_typing(setting);
      case 'reversed_multiple_choice': return this.render_reversed_multiple_choice(setting);
      case 'reversed_multiple_choice2': return this.render_reversed_multiple_choice2(setting);
      case 'audio_multiple_choice': return this.render_audio_multiple_choice(setting);
      case 'tapping': return this.render_tapping(setting);
      case 'copytyping': return this.render_copytyping(setting);
      case 'presentation':
        return this.render_presentation();
      default:
        console.error(setting.template + " doesn't exist");
    }
  }
  get_screen(tpl) {
    /*
    Returns the current screen data
    Exemple:
        {
          "template": "multiple_choice",
          "prompt": {
            "text": {
              "label": "French",
              "kind": "text",
              "value": "Vois-tu le chien ?",
              "alternatives": [],
              "style": [],
              "direction": "source",
              "markdown": false
            },
            "audio": null,
            "video": null,
            "image": null
          },
          "answer": {
            "label": "German",
            "kind": "text",
            "value": "Siehst du den Hund ?",
            "alternatives": [],
            "style": [],
            "direction": "target",
            "markdown": false
          },
          "correct": [
            "Siehst du den Hund ?"
          ],
          "choices": [
            "Siehst du das Pferd ?",
            "Siehst du die Katze ?",
            "Siehst du die Tiere ?",
            "Die Tiere sind süß",
            "Der Hund ist süß",
            "Gib der Katze des Essen",
            "Gib dem Hund das Essen",
            "Die Katze ist süß",
            "Es ist das Essen des Hundes",
            "Es ist das Essen des Pferdes",
            "Es ist das Essen der Tiere",
            "Das Pferd ist süß"
          ],
          "audio": null,
          "markdown": false,
          "attributes": [
            {
              "label": "Gender",
              "value": "der Hund"
            }
          ],
          "post_answer_info": null,
          "placeholder": null,
          "feedback_screen": null,
          "is_strict": false,
          "translation_prompt": null,
          "gap_prompt": null
        }
    */
    var id = this.props.preview_thing_id || this.level_data.screens[this.state.screen_i].learnableID;
    return this.level_data.screensTemplateMap[id][tpl][0];
  }

  render_audio_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen('audio_multiple_choice')}
              nChoices={setting.nChoices || 4}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_reversed_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen('reversed_multiple_choice')}
              nChoices={setting.nChoices || 4}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_reversed_multiple_choice2(setting) {
    return <MultipleChoice
              item={this.get_screen('reversed_multiple_choice2')}
              nChoices={setting.nChoices || (this.props.session_type == 'speed_review' ? 4 : 9)}
              setChoices={this.setChoices} />;
  }
  render_multiple_choice(setting) {
    return <MultipleChoice
              item={this.get_screen('multiple_choice')}
              nChoices={setting.nChoices || (this.props.session_type == 'speed_review' ? 4 : 9)}
              promptWith={setting.promptWith}
              setChoices={this.setChoices} />;
  }
  render_reversed_typing(setting) {
    return <Typing
              item={this.get_screen('reversed_typing')}
              setChoices={this.setChoices} />;
  }
  render_typing(setting) {
    return <Typing
              item={this.get_screen('typing')}
              setChoices={this.setChoices}
              promptWith={setting.promptWith} />;
  }
  render_tapping(setting) {
    return <Tapping
              item={this.get_screen('tapping')}
              difficulty={setting.difficulty || 1}
              setChoices={this.setChoices} />;
  }
  render_copytyping(){
    var prompt = this.get_screen('typing');
    this.setChoices(prompt.correct, 'text', prompt.is_strict);

    return <Presentation
              item={this.get_screen('presentation')}
              prompt={prompt} />;
  }
  render_presentation(correct) {
    return (
      <Presentation
        item={this.get_screen('presentation')}
        correct={correct}
        langCodeTarget={this.props.course.target ? this.props.course.target.language_code : null}
        langCodeSource={this.props.course.source ? this.props.course.source.language_code : null}
        disableMultimedia={this.session_settings.disable_multimedia}
      />
    );
  }
  summary() {
    var items = [];

    if(this.props.session_type == 'preview') {
      if(this.level_data) {
        for(var i=0; i<this.level_data.screens.length; i++) {
          var id = '' + this.level_data.screens[i].learnableID;

          items.push(this.level_data.screensTemplateMap[id].presentation[0]);
        }
      }
    } else {
      for(var id in this.level_summary_data.learnables) {
        var item = this.level_summary_data.learnables[id];

        items[item.pos] = {...item, ...this.level_data.screensTemplateMap[id].presentation[0]};
      }
    }
    return <Summary items={Object.values(items)} session_type={this.props.session_type} />;
  }
  markdown() {
    var data = window.markdown.decode(eval(this.level_data));
    return <div className="nicebox" dangerouslySetInnerHTML={{__html: data}} />;
  }
}

const Value = function(props) {
  var content   = props.content,
      attrs     = {},
      className = props.className || '';
  if(props.lang) {
    attrs.lang = props.lang;
  }
  var k = Date.now(),
      i = 0;

  if(props.single) {
    switch(props.type) {
      case 'text' : return (
        <span>{content}</span>
      );
      case 'image': return (
        <img key={k} src={content} className="text-image" />
      );
      case 'audio': return (
        <span key={k}>
          <audio id={'audio-' + k} src={content}></audio>
          <button type="button" data-id={'audio-' + k} className="audio-player" aria-label={window.I18N.play_audio}>
            <i className="ico ico-l ico-audio"></i>
          </button>
        </span>
      );
      case 'video': return (
        <video key={k} src={content} className="video-player" controls autoPlay>
          Your browser does not support the video tag.
        </video>
      );
    }
  } else {
    switch(props.type) {
      case 'text' : return (
        <div className={'text ' + className} {...attrs}>{content}</div>
      );
      case 'image': return (
        <div className="image">
          <div className="media-list">{content.map(media => (
            <img key={k + i++} src={media} className="text-image loading" />
          ))}</div>
        </div>
      );
      case 'audio': return (
        <div className="audio">
          <div className="media-list">{content.map(media => (
            <span key={k + i++}>
              <audio id={'audio-' + (k + i)} src={media.normal}></audio>
              <button type="button" data-id={'audio-' + (k + i)} className="audio-player" aria-label={window.I18N.play_audio}>
                <i className="ico ico-l ico-audio"></i>
              </button>
            </span>
          ))}</div>
        </div>
      );
      case 'video': return (
        <div className="video">
          <div className="media-list">
            <video key={k + i++} src={content.random()} className="video-player" controls autoPlay>
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      );
    }
  }
};

const Correction = function(props) {
  var data = props.data;

  if(data.score == 1) {
    return <div className="alert alert-success">{window.I18N.correct_answer}!</div>;

  } else if(data.score == 0) {
    return <div className="alert alert-danger">
      {window.I18N.wrong_answer}!&nbsp;
      {data.value
        ? <span>{window.I18N.your_answer_was}: <strong><Value content={data.value} type={data.kind} single="1" /></strong></span>
        : <span>{window.I18N.your_answer_was_empty}</span>}
    </div>;

  } else {
    return <div className="alert alert-warning">
      {window.I18N.near_answer}!&nbsp;
      <span>{window.I18N.your_answer_was}: <strong>
        {data.kind == 'text'
          ? <span>{data.testValue} <small
              className="correction"
              dangerouslySetInnerHTML={{__html: '(' + highlightDiff(data.testValue, data.refValue) + ')'}}
            /></span>
          : <Value content={data.value} type={data.kind} single="1" />}
      </strong></span>
    </div>;
  }
};

const Presentation = function(props){
  var item = props.item,
      correct = props.correct,
      k    = Date.now(),
      i    = 0,
      item_lang = '',
      autoplay = LEARN_WITH_AUTOPLAY_AUDIO || !correct;

  // Add TSS if we're learning a language
  if (this.props.langCodeTarget && this.props.langCodeSource) {
    item_lang = item.item.direction == 'target' ? this.props.langCodeTarget : this.props.langCodeSource;
  }
	return <div>

    {/*-- Correction --*/}
    {correct && <Correction data={correct} />}

    {/*-- Content --*/}
    <table className={'learn nicebox big thing' + (autoplay ? ' autoplay' : '')}>

        {/*-- Item --*/}
        <tr>
          <td className="label">{item.item.label}</td>
          <td className="item">
            <Value content={item.item.value} type={item.item.kind} lang={item_lang} className={item.audio ? '' : 'tts'} />
            {item.item.alternatives.map(txt =>
              <div key={k + i++} className="alt">{txt}</div>
            )}
          </td>
        </tr>

        {/*-- Definition --*/}
        <tr>
          <td className="label">{item.definition.label}</td>
          <td className="definition">
            <Value content={item.definition.value} type={item.definition.kind} />
            {item.definition.alternatives.map(txt =>
              <div key={k + i++} className="alt">{txt}</div>
            )}
          </td>
        </tr>
        <tr className="sep"><td colSpan="2"></td></tr>

        {/*-- Audio --*/}
        {!this.props.disableMultimedia && item.audio && <tr key={k + i++}>
          <td className="label">{item.audio.label}</td>
          <td className="audio"><Value content={item.audio.value} type="audio" /></td>
        </tr>}

        {/*-- Additional content --*/}
        {item.visible_info.map(it => <tr key={k + i++}>
          <td className="label">{it.label}</td>
          <td className="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {item.hidden_info.map(it => <tr key={k + i++}>
          <td className="label">{it.label}</td>
          <td className="more"><Value content={it.value} type={it.kind} /></td>
        </tr>)}

        {/*-- Attributs --*/}
        {item.attributes.map(it => <tr key={k + i++}>
          <td className="label">{it.label}</td>
          <td className="more"><span className="badge"><Value content={it.value} type="text" single="1" /></span></td>
        </tr>)}
      </table>

      {/*-- Copytyping --*/}
      {props.prompt && <div className="typing-container" key={k + i++}>
          <div className="typing">
            <input
              type="text"
              autoComplete="off"
              spellCheck="false"
              value=""
              placeholder={props.prompt.answer.value}
              tabIndex="1"
              autoFocus="autofocus"
            />
            <ul className="keyboard">{props.prompt.choices.map((letter, i) =>
              <li key={i} className="button" tabIndex="0">{letter}</li>
            )}</ul>
          </div>
        </div>}
    </div>;
};

function getPromptType(prompt) {
  if(prompt.text) return 'text';
  if(prompt.image) return 'image';
  if(prompt.audio) return 'audio';
  if(prompt.video) return 'video';
}

const MultipleChoice = function(props) {
  var item       = props.item,
      itemType   = props.promptWith || getPromptType(item.prompt),
      answerType = item.answer.kind;

  // Randomize choices order
  var n          = item.choices.length,
      choicesRnd = randomize([...item.choices]);

  // Display 9 choices max
  if(n > props.nChoices) {
    n = props.nChoices;
    choicesRnd = choicesRnd.slice(0, n);

  } else if(n < props.nChoices) {
    for (let i=n; i<props.nChoices; i++) {
      choicesRnd.push(choicesRnd.random());
    }
  }

  // Place the right answer somewhere in it
  var rnd  = (Math.random() * n - 1) | 0,
     isArr = $.isArray(item.answer.value);

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

  // Display our screens
  var choices = choicesRnd.map((value, i) => {
    return (
      <ChoiceBox
        key={i}
        i={i+1}
        value={value}
        answerType={answerType}
        isValid={rightAnswers.includes(value)}
      />
    );
  });
  props.setChoices(choices, 'numeric');

  return <div className="nicebox">

    {/*-- Item --*/}
    <div className="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />
    </div>

    {/*-- Choices --*/}
    <div className={'medium choices n' + props.nChoices}>{choices}</div>
  </div>;
};

class ChoiceBox extends Component {
  render(props) {
    return <div accessKey={props.i} className={'choice-box nicebox ' + props.answerType} id={'choice-' + props.i} tabIndex="0">
      <span className="choice-index">{props.i}.</span>
      <Value content={props.value} type={props.answerType} single="1" />
    </div>;
  }
}

const Typing = function(props) {
  var item     = props.item,
      itemType = props.promptWith || getPromptType(item.prompt),
      i = 0;

  props.setChoices(item.correct, 'text', item.is_strict);

  return <div className="nicebox">
    <div className="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />

      {/*-- Attributs --*/}
      {item.attributes && <div className="clues">
        {item.attributes.map(it => <span key={i++} className="badge"><Value content={it.value} type="text" single="1" /></span>)}
      </div>}
    </div>
    <div className="typing-container">
      <div className="typing" key={Date.now()}>
        <input type="text" autoComplete="off" spellCheck="false" value="" tabIndex="1" autoFocus="autofocus" />
        <ul className="keyboard">{item.choices.map((letter, i) =>
          <li key={letter} className="button" tabIndex="0">{letter}</li>
        )}</ul>
      </div>
    </div>
  </div>;
};

const Tapping = function(props) {
  var item     = props.item,
      itemType = getPromptType(item.prompt);

  props.setChoices(item.correct, 'tapping', item.is_strict);

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
  i = 0;

  return <div className="nicebox">
    <div className="big choice autoplay">
      <Value content={item.prompt[itemType].value} type={itemType} />

      {/*-- Attributs --*/}
      {item.attributes && <div className="clues">
        {item.attributes.map(it => <span key={i++} className="badge"><Value content={it.value} type="text" single="1" /></span>)}
      </div>}
    </div>
    <div className="tapping-container">
      <div className="tapping" key={Date.now()}>
        <div className="input"></div>
        <ul className="keyboard">{randomize(choices).map((word, i) =>
          <li key={i} className="button" tabIndex="0" id={'btn-' + i}>{word}</li>
        )}</ul>
      </div>
    </div>
  </div>;
};

const Summary = function(props) {
  var items = props.items,
      session_type = props.session_type,
      i = 0;

  return <table className="learn nicebox summary">
  {items.map((item) => {
    var rate = '';

    // Compute success rate
    if(session_type != 'preview') {
      var successRate = item.right / item.count * 100,
          className = (
            successRate == 100 ? 'neverMissed' : (
              successRate < 20 ? 'oftenMissed' : (
                successRate > 80 ? 'rarelyMissed' : 'sometimesMissed'
          ))),
          rate = <span className={className}>{item.right}/{item.count}</span>;
    }

    // Render item
    return <tr key={i++} className="thing">
      <td><Value content={item.item.value} type={item.item.kind} /></td>
      <td><Value content={item.definition.value} type={item.definition.kind} /></td>
      {rate && <td>{rate}</td>}
    </tr>})}
  </table>;
};

//+--------------------------------------------------------
//| SCORING SYSTEM
//+--------------------------------------------------------

const AwardPoints = {
  getPoints(session_type, template, time_spent, score, current_streak) {
    var points      = 0,
        speed_bonus = 0;

    // Score
    switch(session_type){
      case 'learn':
        points = AwardPoints.getPoints_learn(score);
        break;

      case 'classic_review':
        points = AwardPoints.getPoints_learn(score);
        if(current_streak) {
          points = AwardPoints.getPoints_review(points, current_streak);
        }
        if(score == 1 && time_spent) {
          speed_bonus = AwardPoints.getPoints_bonusForSpeed(time_spent, template);
        }
        break;

      case 'speed_review':
        if(score == 1) {
          points = AwardPoints.getPoints_speedReview(time_spent);
        }
        break;
    }
    return points + speed_bonus;
  },

  getPoints_learn: function(score) {
    return 1 === score ? 45 : 0 === score ? 0 : Math.max(10, Math.round(45 * score) - 20);
  },
  getPoints_speedReview: function(time_spent) {
    var t = Math.floor(time_spent / 1e3);
    return t >= 6 ? Math.min(15, 25) : Math.min(15 + 7 * (6 - t), 25);
  },
  getPoints_review: function(points, current_streak) {
    points *= Math.pow(1.2, current_streak);
    points  = Math.min(points, 150);
    return Math.ceil(points);
  },
  getPoints_bonusForSpeed: function(time_spent, tpl) {
    if(tpl == 'typing') {
      return time_spent < 4e3 ? 5 : 0;
    } else {
      return time_spent < 2e3 ? 3 : 0;
    }
  },
  getPoints_bonusForAccuracy: function(percent_correct, nb_scheduled_correct) {
    if(percent_correct == 100) {
      return 20 * nb_scheduled_correct;

    } else if(percent_correct >= 90) {
      return 12 * nb_scheduled_correct;

    } else if(percent_correct >= 80) {
      return 6 * nb_scheduled_correct;

    } else if(percent_correct >= 70) {
      return 4 * nb_scheduled_correct;

    } else if(percent_correct >= 50) {
      return 2 * nb_scheduled_correct;

    } else {
      return 0;
    }
  }
};

const ScoreAnswer = {
  FIRST_LETTER_WEIGHT: .1,
  DISTANCE_WEIGHT: .9,

  /**
   * Check whether the givenAnswer is right or not
   * And score the similarity between the given response and the expected answer
   * (1 = correct, 0 = incorrect, 0<x<1 = more or less similar)
   */
  computeScore: function(givenAnswer, correctAnswer) {
    if(!givenAnswer) {
      return 0;
    }
    var both_are_numeric = $.isNumeric(parseInt(givenAnswer, 10)) && $.isNumeric(parseInt(correctAnswer, 10));

    if(both_are_numeric) {
      return ScoreAnswer.getNumericScore(givenAnswer, correctAnswer);
    } else {
      return ScoreAnswer.getStringScore(givenAnswer, correctAnswer);
    }
  },

  getNumericScore: function(givenAnswer, correctAnswer) {
    return (parseInt(givenAnswer, 10) === parseInt(correctAnswer, 10) ? 1 : 0);
  },

  getStringScore: function(givenAnswer, correctAnswer) {
    var tolerance = ScoreAnswer.getDistanceTolerance(correctAnswer.length),
        distance = ScoreAnswer.getStringDistance(givenAnswer, correctAnswer);
    if (distance >= tolerance) return 0;

    var weightFirstLetter = correctAnswer.charAt(0) === givenAnswer.charAt(0) ? 1 : 0,
        weight = (tolerance - distance) / tolerance,
        s = ScoreAnswer.FIRST_LETTER_WEIGHT * weightFirstLetter + ScoreAnswer.DISTANCE_WEIGHT * weight;

    return s < .5 && (s = 0), s;
  },

  getDistanceTolerance: function(length) {
    return length * (
      length > 18 ? .5
        : length < 3 ? 1
          : -1 * length / 33 + 1.1
    );
  },

  /**
   * Compute the levenshtein distance between a and b
   */
  getStringDistance: function(a, b) {
    var computeDistanceMatrix = function() {
      var getItemAt;

      if($.isArray(a)) {
        getItemAt = function(arr, i) { return arr[i] };
      } else {
        getItemAt = function(arr, i) { return arr.charAt(i) };
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
            matrix[i - 1][j - 1] + (getItemAt(a, i - 1) === getItemAt(b, j - 1) ? 0 : 1)
          );
        }
      }
      return matrix;
    };

    var matrix = computeDistanceMatrix();
    return matrix[a.length][b.length];
  }
}

//+--------------------------------------------------------
//| TEXT NORMALIZATION
//+--------------------------------------------------------

// https://cdnjs.cloudflare.com/ajax/libs/xregexp/3.1.1/xregexp-all.js
const RegexUnicode = {
  'C': '\0-\x1F\x7F-\x9F\xAD\u0378\u0379\u0380-\u0383\u038B\u038D\u03A2\u0530\u0557\u0558\u0560\u0588\u058B\u058C\u0590\u05C8-\u05CF\u05EB-\u05EF\u05F5-\u0605\u061C\u061D\u06DD\u070E\u070F\u074B\u074C\u07B2-\u07BF\u07FB-\u07FF\u082E\u082F\u083F\u085C\u085D\u085F-\u089F\u08B5-\u08E2\u0984\u098D\u098E\u0991\u0992\u09A9\u09B1\u09B3-\u09B5\u09BA\u09BB\u09C5\u09C6\u09C9\u09CA\u09CF-\u09D6\u09D8-\u09DB\u09DE\u09E4\u09E5\u09FC-\u0A00\u0A04\u0A0B-\u0A0E\u0A11\u0A12\u0A29\u0A31\u0A34\u0A37\u0A3A\u0A3B\u0A3D\u0A43-\u0A46\u0A49\u0A4A\u0A4E-\u0A50\u0A52-\u0A58\u0A5D\u0A5F-\u0A65\u0A76-\u0A80\u0A84\u0A8E\u0A92\u0AA9\u0AB1\u0AB4\u0ABA\u0ABB\u0AC6\u0ACA\u0ACE\u0ACF\u0AD1-\u0ADF\u0AE4\u0AE5\u0AF2-\u0AF8\u0AFA-\u0B00\u0B04\u0B0D\u0B0E\u0B11\u0B12\u0B29\u0B31\u0B34\u0B3A\u0B3B\u0B45\u0B46\u0B49\u0B4A\u0B4E-\u0B55\u0B58-\u0B5B\u0B5E\u0B64\u0B65\u0B78-\u0B81\u0B84\u0B8B-\u0B8D\u0B91\u0B96-\u0B98\u0B9B\u0B9D\u0BA0-\u0BA2\u0BA5-\u0BA7\u0BAB-\u0BAD\u0BBA-\u0BBD\u0BC3-\u0BC5\u0BC9\u0BCE\u0BCF\u0BD1-\u0BD6\u0BD8-\u0BE5\u0BFB-\u0BFF\u0C04\u0C0D\u0C11\u0C29\u0C3A-\u0C3C\u0C45\u0C49\u0C4E-\u0C54\u0C57\u0C5B-\u0C5F\u0C64\u0C65\u0C70-\u0C77\u0C80\u0C84\u0C8D\u0C91\u0CA9\u0CB4\u0CBA\u0CBB\u0CC5\u0CC9\u0CCE-\u0CD4\u0CD7-\u0CDD\u0CDF\u0CE4\u0CE5\u0CF0\u0CF3-\u0D00\u0D04\u0D0D\u0D11\u0D3B\u0D3C\u0D45\u0D49\u0D4F-\u0D56\u0D58-\u0D5E\u0D64\u0D65\u0D76-\u0D78\u0D80\u0D81\u0D84\u0D97-\u0D99\u0DB2\u0DBC\u0DBE\u0DBF\u0DC7-\u0DC9\u0DCB-\u0DCE\u0DD5\u0DD7\u0DE0-\u0DE5\u0DF0\u0DF1\u0DF5-\u0E00\u0E3B-\u0E3E\u0E5C-\u0E80\u0E83\u0E85\u0E86\u0E89\u0E8B\u0E8C\u0E8E-\u0E93\u0E98\u0EA0\u0EA4\u0EA6\u0EA8\u0EA9\u0EAC\u0EBA\u0EBE\u0EBF\u0EC5\u0EC7\u0ECE\u0ECF\u0EDA\u0EDB\u0EE0-\u0EFF\u0F48\u0F6D-\u0F70\u0F98\u0FBD\u0FCD\u0FDB-\u0FFF\u10C6\u10C8-\u10CC\u10CE\u10CF\u1249\u124E\u124F\u1257\u1259\u125E\u125F\u1289\u128E\u128F\u12B1\u12B6\u12B7\u12BF\u12C1\u12C6\u12C7\u12D7\u1311\u1316\u1317\u135B\u135C\u137D-\u137F\u139A-\u139F\u13F6\u13F7\u13FE\u13FF\u169D-\u169F\u16F9-\u16FF\u170D\u1715-\u171F\u1737-\u173F\u1754-\u175F\u176D\u1771\u1774-\u177F\u17DE\u17DF\u17EA-\u17EF\u17FA-\u17FF\u180E\u180F\u181A-\u181F\u1878-\u187F\u18AB-\u18AF\u18F6-\u18FF\u191F\u192C-\u192F\u193C-\u193F\u1941-\u1943\u196E\u196F\u1975-\u197F\u19AC-\u19AF\u19CA-\u19CF\u19DB-\u19DD\u1A1C\u1A1D\u1A5F\u1A7D\u1A7E\u1A8A-\u1A8F\u1A9A-\u1A9F\u1AAE\u1AAF\u1ABF-\u1AFF\u1B4C-\u1B4F\u1B7D-\u1B7F\u1BF4-\u1BFB\u1C38-\u1C3A\u1C4A-\u1C4C\u1C80-\u1CBF\u1CC8-\u1CCF\u1CF7\u1CFA-\u1CFF\u1DF6-\u1DFB\u1F16\u1F17\u1F1E\u1F1F\u1F46\u1F47\u1F4E\u1F4F\u1F58\u1F5A\u1F5C\u1F5E\u1F7E\u1F7F\u1FB5\u1FC5\u1FD4\u1FD5\u1FDC\u1FF0\u1FF1\u1FF5\u1FFF\u200B-\u200F\u202A-\u202E\u2060-\u206F\u2072\u2073\u208F\u209D-\u209F\u20BF-\u20CF\u20F1-\u20FF\u218C-\u218F\u23FB-\u23FF\u2427-\u243F\u244B-\u245F\u2B74\u2B75\u2B96\u2B97\u2BBA-\u2BBC\u2BC9\u2BD2-\u2BEB\u2BF0-\u2BFF\u2C2F\u2C5F\u2CF4-\u2CF8\u2D26\u2D28-\u2D2C\u2D2E\u2D2F\u2D68-\u2D6E\u2D71-\u2D7E\u2D97-\u2D9F\u2DA7\u2DAF\u2DB7\u2DBF\u2DC7\u2DCF\u2DD7\u2DDF\u2E43-\u2E7F\u2E9A\u2EF4-\u2EFF\u2FD6-\u2FEF\u2FFC-\u2FFF\u3040\u3097\u3098\u3100-\u3104\u312E-\u3130\u318F\u31BB-\u31BF\u31E4-\u31EF\u321F\u32FF\u4DB6-\u4DBF\u9FD6-\u9FFF\uA48D-\uA48F\uA4C7-\uA4CF\uA62C-\uA63F\uA6F8-\uA6FF\uA7AE\uA7AF\uA7B8-\uA7F6\uA82C-\uA82F\uA83A-\uA83F\uA878-\uA87F\uA8C5-\uA8CD\uA8DA-\uA8DF\uA8FE\uA8FF\uA954-\uA95E\uA97D-\uA97F\uA9CE\uA9DA-\uA9DD\uA9FF\uAA37-\uAA3F\uAA4E\uAA4F\uAA5A\uAA5B\uAAC3-\uAADA\uAAF7-\uAB00\uAB07\uAB08\uAB0F\uAB10\uAB17-\uAB1F\uAB27\uAB2F\uAB66-\uAB6F\uABEE\uABEF\uABFA-\uABFF\uD7A4-\uD7AF\uD7C7-\uD7CA\uD7FC-\uF8FF\uFA6E\uFA6F\uFADA-\uFAFF\uFB07-\uFB12\uFB18-\uFB1C\uFB37\uFB3D\uFB3F\uFB42\uFB45\uFBC2-\uFBD2\uFD40-\uFD4F\uFD90\uFD91\uFDC8-\uFDEF\uFDFE\uFDFF\uFE1A-\uFE1F\uFE53\uFE67\uFE6C-\uFE6F\uFE75\uFEFD-\uFF00\uFFBF-\uFFC1\uFFC8\uFFC9\uFFD0\uFFD1\uFFD8\uFFD9\uFFDD-\uFFDF\uFFE7\uFFEF-\uFFFB\uFFFE\uFFFF',
  'P': '\x21-\x23\x25-\\x2A\x2C-\x2F\x3A\x3B\\x3F\x40\\x5B-\\x5D\x5F\\x7B\x7D\xA1\xA7\xAB\xB6\xB7\xBB\xBF\u037E\u0387\u055A-\u055F\u0589\u058A\u05BE\u05C0\u05C3\u05C6\u05F3\u05F4\u0609\u060A\u060C\u060D\u061B\u061E\u061F\u066A-\u066D\u06D4\u0700-\u070D\u07F7-\u07F9\u0830-\u083E\u085E\u0964\u0965\u0970\u0AF0\u0DF4\u0E4F\u0E5A\u0E5B\u0F04-\u0F12\u0F14\u0F3A-\u0F3D\u0F85\u0FD0-\u0FD4\u0FD9\u0FDA\u104A-\u104F\u10FB\u1360-\u1368\u1400\u166D\u166E\u169B\u169C\u16EB-\u16ED\u1735\u1736\u17D4-\u17D6\u17D8-\u17DA\u1800-\u180A\u1944\u1945\u1A1E\u1A1F\u1AA0-\u1AA6\u1AA8-\u1AAD\u1B5A-\u1B60\u1BFC-\u1BFF\u1C3B-\u1C3F\u1C7E\u1C7F\u1CC0-\u1CC7\u1CD3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205E\u207D\u207E\u208D\u208E\u2308-\u230B\u2329\u232A\u2768-\u2775\u27C5\u27C6\u27E6-\u27EF\u2983-\u2998\u29D8-\u29DB\u29FC\u29FD\u2CF9-\u2CFC\u2CFE\u2CFF\u2D70\u2E00-\u2E2E\u2E30-\u2E42\u3001-\u3003\u3008-\u3011\u3014-\u301F\u3030\u303D\u30A0\u30FB\uA4FE\uA4FF\uA60D-\uA60F\uA673\uA67E\uA6F2-\uA6F7\uA874-\uA877\uA8CE\uA8CF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA95F\uA9C1-\uA9CD\uA9DE\uA9DF\uAA5C-\uAA5F\uAADE\uAADF\uAAF0\uAAF1\uABEB\uFD3E\uFD3F\uFE10-\uFE19\uFE30-\uFE52\uFE54-\uFE61\uFE63\uFE68\uFE6A\uFE6B\uFF01-\uFF03\uFF05-\uFF0A\uFF0C-\uFF0F\uFF1A\uFF1B\uFF1F\uFF20\uFF3B-\uFF3D\uFF3F\uFF5B\uFF5D\uFF5F-\uFF65',
  'S': '\\x24\\x2B\x3C-\x3E\\x5E\x60\\x7C\x7E\xA2-\xA6\xA8\xA9\xAC\xAE-\xB1\xB4\xB8\xD7\xF7\u02C2-\u02C5\u02D2-\u02DF\u02E5-\u02EB\u02ED\u02EF-\u02FF\u0375\u0384\u0385\u03F6\u0482\u058D-\u058F\u0606-\u0608\u060B\u060E\u060F\u06DE\u06E9\u06FD\u06FE\u07F6\u09F2\u09F3\u09FA\u09FB\u0AF1\u0B70\u0BF3-\u0BFA\u0C7F\u0D79\u0E3F\u0F01-\u0F03\u0F13\u0F15-\u0F17\u0F1A-\u0F1F\u0F34\u0F36\u0F38\u0FBE-\u0FC5\u0FC7-\u0FCC\u0FCE\u0FCF\u0FD5-\u0FD8\u109E\u109F\u1390-\u1399\u17DB\u1940\u19DE-\u19FF\u1B61-\u1B6A\u1B74-\u1B7C\u1FBD\u1FBF-\u1FC1\u1FCD-\u1FCF\u1FDD-\u1FDF\u1FED-\u1FEF\u1FFD\u1FFE\u2044\u2052\u207A-\u207C\u208A-\u208C\u20A0-\u20BE\u2100\u2101\u2103-\u2106\u2108\u2109\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A\u213B\u2140-\u2144\u214A-\u214D\u214F\u218A\u218B\u2190-\u2307\u230C-\u2328\u232B-\u23FA\u2400-\u2426\u2440-\u244A\u249C-\u24E9\u2500-\u2767\u2794-\u27C4\u27C7-\u27E5\u27F0-\u2982\u2999-\u29D7\u29DC-\u29FB\u29FE-\u2B73\u2B76-\u2B95\u2B98-\u2BB9\u2BBD-\u2BC8\u2BCA-\u2BD1\u2BEC-\u2BEF\u2CE5-\u2CEA\u2E80-\u2E99\u2E9B-\u2EF3\u2F00-\u2FD5\u2FF0-\u2FFB\u3004\u3012\u3013\u3020\u3036\u3037\u303E\u303F\u309B\u309C\u3190\u3191\u3196-\u319F\u31C0-\u31E3\u3200-\u321E\u322A-\u3247\u3250\u3260-\u327F\u328A-\u32B0\u32C0-\u32FE\u3300-\u33FF\u4DC0-\u4DFF\uA490-\uA4C6\uA700-\uA716\uA720\uA721\uA789\uA78A\uA828-\uA82B\uA836-\uA839\uAA77-\uAA79\uAB5B\uFB29\uFBB2-\uFBC1\uFDFC\uFDFD\uFE62\uFE64-\uFE66\uFE69\uFF04\uFF0B\uFF1C-\uFF1E\uFF3E\uFF40\uFF5C\uFF5E\uFFE0-\uFFE6\uFFE8-\uFFEE\uFFFC\uFFFD'
};

function sanitizeTyping(text, strict) {
  text = text.trim()
             .replace(/\s+/g, ' ')
             .replace(new RegExp(RegexUnicode.C, 'g'), ''); // control chars

  // https://cdnjs.cloudflare.com/ajax/libs/xregexp/3.1.1/xregexp-all.js
  if(!strict) {
    text = text.replace(/\(.*?\)/g, '')
               .replace(new RegExp('[' + RegexUnicode.P + RegexUnicode.S + ']', 'g'), ' ') // punctuation, symbol
               .replace(/[-Ù‹Ù›]+/g, ' ')
               .replace(/\s+/g, ' ');
  }
  return text.trim();
}

//+--------------------------------------------------------
//| HIGHLIGHT TEXT DIFF
//+--------------------------------------------------------

// https://codereview.stackexchange.com/questions/133586/a-string-prototype-diff-implementation-text-diff
const highlightDiff = (function(){

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
  }

  // returns the first matching substring in-between the two strings
  function getMatchingSubstring(s,l,m){
    var i     = -1,
        n     = s.length,
        match = false,
        cd     = {fis:n, mtc:m, sbs:''}; // temporary object used to construct the cd (change data) object

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
    longer  = longer.split('').slice(base_index);
    shorter = shorter.slice(base_index);

    var len = longer.length,                   // length of the longer string
        cd = {fis: shorter.length,             // the index of matching string in the shorter string
              fil: len,                        // the index of matching string in the longer string
              sbs: '',                         // the matching substring itself
              mtc: m + s.slice(0,base_index)}, // if exists mtc holds the matching string at the front
        sub = {sbs:''};                       // returned substring per 1 character rotation of the longer string

    if(shorter !== '') {
      for(var rc = 0; rc < len && sub.sbs.length < p; rc++){             // rc -> rotate count, p -> precision factor
        sub = getMatchingSubstring(shorter, rotate(longer, rc), cd.mtc); // rotate longer string 1 char and get substring
        sub.fil = rc < len - sub.fis ? sub.fis + rc                      // mismatch is longer than the mismatch in short
                                     : sub.fis - len + rc;               // mismatch is shorter than the mismatch in short
        sub.sbs.length > cd.sbs.length && (cd = sub);                    // only keep the one with the longest substring.
      }
    }

    // insert the mismatching delete subsrt and insert substr to the cd object and attach the previous substring
    if(isThisLonger) {
      cd.del = longer.slice(0,cd.fil).join('');
      cd.ins = shorter.slice(0,cd.fis);
    } else {
      cd.del = shorter.slice(0,cd.fis);
      cd.ins = longer.slice(0,cd.fil).join('');
    }

    if(cd.del.indexOf(' ') == -1 || cd.ins.indexOf(' ') == -1) return cd;
    if(cd.del === '' || cd.ins === '' || cd.sbs === '') return cd;
    return getChanges(cd.del, cd.ins, cd.mtc, p);
  }

  class Diff {
    count = 0
    p = 2  // p -> precision factor

    constructor(p) {
      this.p = p || 2;
    }
    addCount(txt) {
      this.count += txt.length;
      return txt;
    }

    highlight(txt1, txt2){
      var cd       = getChanges(txt1,txt2,'',this.p),
          nextTxt2 = txt2.slice(cd.mtc.length + cd.ins.length + cd.sbs.length), // remaining part of "txt2"
          nextTxt1 = txt1.slice(cd.mtc.length + cd.del.length + cd.sbs.length), // remaining part of "txt1"
          result   = '';                                                        // the glorious result

      cd.del.length > 0 && (cd.del = '<span class="deleted">'  + this.addCount(cd.del) + '</span>');
      cd.ins.length > 0 && (cd.ins = '<span class="inserted">' + this.addCount(cd.ins) + '</span>');
      result = cd.mtc + cd.del + cd.ins + cd.sbs;

      if(nextTxt1 !== '' || nextTxt2 !== '') {
        result += this.highlight(nextTxt1,nextTxt2);
      }
      return result;
    }

    highlightTokens(txt1, txt2) {
      this.count = 0;

      var cmp = this.highlight(txt1, txt2),
          count_highlight = this.count;

      // Attempt comparison through tokenization
      var tokens1 = txt1.split(' '),
          tokens2 = txt2.split(' ');

      if (tokens1.length != tokens2.length) {
        return cmp;
      }
      this.count = 0;

      var cmp_tokens = [];
      for(let i=0; i<tokens1.length; i++) {
        cmp_tokens.push(this.highlight(tokens1[i], tokens2[i]));
      }

      if (this.count < count_highlight) {
        return cmp_tokens.join(' ');
      }
      return cmp;
    }
  }

  function diff(txt1, txt2, p) {
    return new Diff(p).highlightTokens(txt1, txt2);
  }
  return diff;
})();
