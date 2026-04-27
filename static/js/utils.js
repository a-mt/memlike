var process=process||{};process.env=process.env||{};window.MEMLIKE=window.MEMLIKE||{};window.MEMLIKE.js_utils={build_date:process.env.BUILD_DATE};/* global $, window, document, console, navigator *//* global setTimeout, URL, Blob */var GlobalEventEmitter=window.GlobalEventEmitter={_events:{},dispatch:function(eventName,data){if(!this._events[eventName])return;for(var i=0;i<this._events[eventName].length;i++)this._events[eventName][i](data)},subscribe:function(eventName,callback){if(!this._events[eventName])this._events[eventName]=[];this._events[eventName].push(callback)}//+--------------------------------------------------------
//| Get the value of a parameters of the given url (current location if false)
//| Doesn't support array parameters
//+--------------------------------------------------------
};var getUrlParameters=window.getUrlParameters=function(href){if(typeof href=='undefined'||href===false){href=window.location.href}var hash=href.indexOf('#');if(hash!=-1){href=href.substr(0,hash)}var vars={};href.replace(/[?&]+([^=&]+)=?([^&]*)?/gi,// regexp
function(m,key,value){// callback
vars[key]=value!==undefined?value:''});return vars};var getCookies=window.getCookies=function(){let cookie={};document.cookie.split(';').forEach(function(el){let[k,v]=el.split('=');cookie[k.trim()]=v});return cookie};var objectsAreEqual=window.objectsAreEqual=function(newObj,oldObj){if(Object.keys(oldObj).length!==Object.keys(newObj).length){return false}for(const key in oldObj){if(typeof newObj[key]!==typeof newObj[key]){return false}if(typeof newObj[key]==='object'){return objectsAreEqual(newObj[key],oldObj[key])}if(oldObj[key]!==newObj[key]){return false}}return true};//+--------------------------------------------------------
//| Play/pause audio tag
//+--------------------------------------------------------
var audioPlayer=window.audioPlayer={isInit:false,target:false,isPlaying:false,reset:function(){// Detect when audio has stopped playing
if(!audioPlayer.isInit){audioPlayer.isInit=true;document.body.addEventListener('ended',function(e){if(e.target==audioPlayer.target){audioPlayer.isPlaying=false;audioPlayer.target.button.classList.remove('active');audioPlayer.target=false}},true)}// Reset audioPlayer state
if(audioPlayer.isPlaying){audioPlayer.target.pause();audioPlayer.target.button.classList.remove('active')}audioPlayer.target=false;audioPlayer.isPlaying=false},init:function(){audioPlayer.reset();$('main').on('click','.audio-player',audioPlayer.play)},// Play the target (this) audio element
play:function(e,force){e.preventDefault();e.stopPropagation();let audioBtn=this;// the .audio-player element (button/a)
let audioElement=this;// the audio element (if it exists)
if(audioBtn.nodeName=='A'&&audioBtn.classList.contains('url')){window.open(audioElement.getAttribute('src'),'_blank');return}if(audioBtn.dataset&&'id'in audioBtn.dataset){audioElement=document.getElementById(audioBtn.dataset.id);if(!audioElement){console.error('Element with ID '+audioBtn.dataset.id+' doesnt exist')}}if(audioElement.nodeName!='AUDIO'){console.error('Expected an audio element, instead of:',audioElement);return}audioElement.button=audioBtn;// Toggle play/pause
if(audioPlayer.target===audioElement){if(force){if(!audioPlayer.isPlaying){audioElement.play();audioPlayer.isPlaying=true}return}if(audioPlayer.isPlaying){audioElement.pause();audioElement.button.classList.remove('active')}else{audioElement.play();audioElement.button.classList.add('active')}audioPlayer.isPlaying=!audioPlayer.isPlaying;// Pause any other player and play current target
}else{if(audioPlayer.isPlaying){audioPlayer.target.pause();audioPlayer.target.classList.remove('active')}audioElement.play();audioElement.button.classList.add('active');audioPlayer.target=audioElement;audioPlayer.isPlaying=true}},// Pause the current audio
pause:function(){if(audioPlayer.isPlaying){audioPlayer.target.pause();audioPlayer.target.button.classList.remove('active');audioPlayer.isPlaying=false}}};//+--------------------------------------------------------
//| View image full size
//+--------------------------------------------------------
var imgZoom=window.imgZoom={container:false,n:0,i:0,reset:function(){// for each images that have the text-image class: add the imgZoom attribute
imgZoom.n=$('main .text-image').each(function(i){$(this).attr('id','imgZoom-'+i).data('i',i)}).length},init:function(){imgZoom.reset();$('main').on('click','.text-image',imgZoom.open)},createContainer:function(){var div=$('<div id="imgZoom" style="display: none">').appendTo(document.body);// Backgroud=nd
$('<div class="backdrop">').appendTo(div).on('click',imgZoom.close);// Modal
$('<div class="modal">').appendTo(div)// Handle prev/next events
.on('click','.slideshow-trigger',function(){var i=$(this).hasClass('prev')?imgZoom.i-1:imgZoom.i+1;imgZoom.open.call(document.getElementById('imgZoom-'+i))})// Handle close btn
.on('click','.modal-close-link',imgZoom.close);imgZoom.container=div},open:function(){if(!imgZoom.container){imgZoom.createContainer()}var html=`<button type="button" class="modal-close-link">${window.I18N.close}</button>`;// Img & legend
var legend=$(this).closest('.thing').find('.text').text();html+=`<figure>
            <img class="zoom" src="${this.getAttribute('src')}">
            ${legend?`<figcaption>${legend}</figcaption>`:''}
          </figure>`;// Prev & next
imgZoom.i=$(this).data('i');if(imgZoom.i>0){html+='<div class="slideshow-trigger prev"></div>'}if(imgZoom.i+1<imgZoom.n){html+='<div class="slideshow-trigger next"></div>'}// Render
$('.modal',imgZoom.container).html(html);imgZoom.container.show()},close:function(){imgZoom.container&&imgZoom.container.hide()}};//+--------------------------------------------------------
//| Modal
//+--------------------------------------------------------
var modal=window.modal={$container:false,close_callback:{},createContainer:function(){var div=$('<div id="modal" style="display: none">').appendTo(document.body);// Background
$('<div class="backdrop">').appendTo(div).on('click',modal.close);// Modal
$('<div class="modal">').appendTo(div);modal.$container=div},getContainer:function(){if(!modal.$container){modal.createContainer()}return modal.$container},open:function(html){if(!modal.$container){modal.createContainer()}$('.modal',modal.$container).html(html);modal.reopen()},reopen(){modal.$container.show()},onclose:function(k,callback){if(!callback){delete modal.close_callback[k]}else if(typeof callback=='function'){modal.close_callback[k]=callback}},close:function(){modal.$container&&modal.$container.hide();for(var k in modal.close_callback){modal.close_callback[k].call(modal,k)}}};//+--------------------------------------------------------
//| Render markdown content
//+--------------------------------------------------------
var defineMarkdown=window.defineMarkdown=function(){if(window.markdown){window.markdown.decode=function(value){var STATIC_URL='https://static.memrise.com/',allowed_tags='p,strong,em,pre,code';value=value.replace(/img:http:\/\/www.memrise.com\/static\//g,'img:'+STATIC_URL).replace(/img:http:\/\/memrise.com\/static\//g,'img:'+STATIC_URL).replace(/img:\/static\//g,'img:'+STATIC_URL).replace(/img:([^\s<]+)/g,'`img:$1`');value=window.markdown.toHTML(value);var res=$('<div>').html(value);res.find('*').each(function(){$(this).is(allowed_tags)||$(this).remove()});value=res.html().trim().replace(/img:\s*([^\s<]+)/g,'<img class=\'img-tag\' src=\'$1\' />').replace(/embed:\s*([^\s<]+)/g,'<a class=\'embed\' href=\'$1\' target=\'_blank\'>$1</a>');// Header img + return carriage
value=value.replace(/<code>(<img class='img-tag' src='https:\/\/dummyimage.com\/600x\d+\/([0-9A-Fa-f]{6}))/g,function(match,img,background){return'<code style="background: #'+background+'" class="header">'+img}).replace(/\u2003+\n/g,'<br>\n');return value}}else{window.markdown={decode:function(value){return value}}}};var multimedia=window.multimedia={init:function(){$('.multimedia-wrapper').each(function(){var varname=this.getAttribute('data-var');if(window[varname]){$(this).html(window.markdown.decode(window[varname]))}$(this).removeClass('loading-spinner')})}};//+--------------------------------------------------------
//| Text To Speech
//+--------------------------------------------------------
// https://docs.cloud.google.com/translate/docs/languages?hl=de
var TTS=window.TTS={langs:{'af':'Afrikaans','sq':'Albanian','am':'Amharic','ar':'Arabic','hy':'Armenian','az':'Azerbaijani','eu':'Basque','be':'Belarusian','bn':'Bengali','bs':'Bosnian','bg':'Bulgarian','ca':'Catalan','ceb':'Cebuano','zh-CN':'Chinese (Simplified)','zh-TW':'Chinese (Traditional)','co':'Corsican','hr':'Croatian','cs':'Czech','da':'Danish','nl':'Dutch','en':'English','eo':'Esperanto','et':'Estonian','fi':'Finnish','fr':'French','fy':'Frisian','gl':'Galician','ka':'Georgian','de':'German','el':'Greek','gu':'Gujarati','ht':'Haitian Creole','ha':'Hausa','haw':'Hawaiian','iw':'Hebrew','hi':'Hindi','hmn':'Hmong','hu':'Hungarian','is':'Icelandic','ig':'Igbo','id':'Indonesian','ga':'Irish','it':'Italian','ja':'Japanese','jw':'Javanese','kn':'Kannada','kk':'Kazakh','km':'Khmer','ko':'Korean','ku':'Kurdish','ky':'Kyrgyz','lo':'Lao','la':'Latin','lv':'Latvian','lt':'Lithuanian','lb':'Luxembourgish','mk':'Macedonian','mg':'Malagasy','ms':'Malay','ml':'Malayalam','mt':'Maltese','mi':'Maori','mr':'Marathi','mn':'Mongolian','my':'Myanmar (Burmese)','ne':'Nepali','no':'Norwegian','ny':'Nyanja (Chichewa)','ps':'Pashto','fa':'Persian','pl':'Polish','pt':'Portuguese (Portugal, Brazil)','pa':'Punjabi','ro':'Romanian','ru':'Russian','sm':'Samoan','gd':'Scots Gaelic','sr':'Serbian','st':'Sesotho','sn':'Shona','sd':'Sindhi','si':'Sinhala (Sinhalese)','sk':'Slovak','sl':'Slovenian','so':'Somali','es':'Spanish','su':'Sundanese','sw':'Swahili','sv':'Swedish','tl':'Tagalog (Filipino)','tg':'Tajik','ta':'Tamil','te':'Telugu','th':'Thai','tr':'Turkish','uk':'Ukrainian','ur':'Urdu','uz':'Uzbek','vi':'Vietnamese','cy':'Welsh','xh':'Xhosa','yi':'Yiddish','yo':'Yoruba','zu':'Zulu'},get_audio(text,lang){if(!TTS.langs[lang]||text.length>=200){return}const tk=Math.floor(Math.random()*1000000);const url=`https://translate.google.com/translate_tts?ie=UTF-8&tl=${lang}&client=tw-ob&q=${encodeURIComponent(text)}&tk=${tk}&ttsspeed=1`;return'https://cors-anywhere.99901dev.workers.dev/?q='+encodeURIComponent(url);// return 'https://google-tts-api.herokuapp.com/?q=' + encodeURIComponent(text) + '&tl=' + lang + '&ttspeed=1&download';
}};//+--------------------------------------------------------
//| File download
//+--------------------------------------------------------
/**
 * Trigger a file download of the given mimeType
 * ex: download(csvContent, 'dowload.csv', 'text/csv;encoding:utf-8');
 *
 * @param string content
 * @param string fileName
 * @param mimeType
 */var download=window.download=function(content,fileName,mimeType){var a=document.createElement('a');mimeType=mimeType||'application/octet-stream';// IE10
if(navigator.msSaveBlob){navigator.msSaveBlob(new Blob([content],{type:mimeType}),fileName);//html5 A[download]
}else if(URL&&'download'in a){a.href=URL.createObjectURL(new Blob([content],{type:mimeType}));a.setAttribute('download',fileName);document.body.appendChild(a);a.click();document.body.removeChild(a)}else{window.location.href='data:application/octet-stream,'+encodeURIComponent(content);// only this mime type is supported
}};
//# sourceMappingURL=utils.js.map