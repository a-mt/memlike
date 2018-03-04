/** @jsx h */
'use strict';
const {h, Component, render} = window.preact;

/* global $ */
$(document).ready(function(){
  
  render(<Learn idCourse={window.$_URL.idCourse} level={window.$_URL.lvl} />, document.getElementById('learn-container'))
});

class Learn extends Component {
  state = { i: 0, n: 0, data: false, error: false, recap: false, level: 1, maxlevel: 1 };

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
      window.imgZoom && window.imgZoom.reset();
      window.audioPlayer && window.audioPlayer.reset();
    }
    if(!prevState.data || prevState.level != this.state.level) {
      document.getElementById('level-title').innerHTML = this.state.level + " - " + this.state.data.session.level.title;
    }
  }
  getData(level) {
    $.ajax({
      url: '/ajax/course/' + this.props.idCourse + '/' + level,
      success: function(data){
        if(!this.init) {
          this.bindEvents();
        }

        this.setState({
          recap: false,
          error: false,
          level: level,

          data : data,
          i    : 0,
          n    : data.learnables.length
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
      if(e.which == 13) { // press enter

        // Display next item
        if(this.state.i + 1 < this.state.n) {
          this.setState({
            i: this.state.i + 1
          }, function(){
            window.imgZoom && window.imgZoom.reset();
            window.audioPlayer && window.audioPlayer.reset();
          });

        // Display next level or go back to course's page
        } else if(this.state.recap){
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
            recap: true
          }, function(){
            window.imgZoom && window.imgZoom.reset();
          });
        }
      }
    }.bind(this));

    window.onbeforeunload = function(e){
      if(!window.warnbeforeunload) {
        return;
      }
        e = e || window.event;
        if (e) { // IE, Firefox<4
          e.returnValue = 'Your changes will be lost.';
        } 
        return 'Your changes will be lost.';
    };
  }

  render(props, state) {
    var percent = (state.n ? Math.ceil(state.i / state.n * 100) : 100);

    if(state.error) {
      return <div>{state.error}</div>;
    }
    if(!this.state.data) {
      return <div class="loading-spinner"></div>;
    }
    var item = (this.state.recap ? false : this.state.data.boxes[this.state.i]);
    
    return <div>
        {/*<!-- PROGRESS BAR -->*/}
        <div class="progress-bar" role="progressbar" aria-valuenow={state.i} aria-valuemin="0" aria-valuemax={state.i}>
          <div class="counter">{state.i} / {state.n}</div>
          <div class="progress-bar-active" style={{'clip-path': 'polygon(0 0, '+percent+'% 0, '+percent+'% 100%, 0 100%)'}}>
            <div class="counter">{state.i} / {state.n}</div>
          </div>
        </div>

        {/*<!-- ITEM -->*/}
        {item && this['render_' + item.template](item.learnable_id)}

        {this.state.recap && this.recap()}
      </div>;
  }
  render_presentation(id) {
    var item = this.state.data.learnables.find(item => item.learnable_id == id);

    return <table class="learn nicebox thing big">
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
        {item.confused_answers.map(answer => <tr>
          <td class="label">{answer.label}</td>
          <td class="more">{answer.value}</td>
        </tr>)}
      </table>;
  }
  _thing(it) {
    return <div class={it.kind}>
      {it.kind == "text" ? it.value
      : (it.kind == "image" ? <div class="media-list">{it.value.map(media => <img src={media} class="text-image" />)}</div>
      : (it.kind == "audio" ? <div class="media-list">{it.value.map(media => <audio src={media.normal} class="audio-player ico ico-l ico-audio"></audio>)}</div>
      : ""))}
    </div>;
  }
  recap() {
    return <table class="learn nicebox recap">
      {this.state.data.boxes.map(box => {
        var item = this.state.data.learnables.find(item => item.learnable_id == box.learnable_id);
        return <tr class="thing">
          <td>{this._thing(item.item)}</td>
          <td>{this._thing(item.definition)}</td>
        </tr>})}
    </table>;
  }
}