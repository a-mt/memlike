
var process = process || {};
process.env = process.env || {};

window.MEMLIKE = window.MEMLIKE || {};
window.MEMLIKE.js_spreadsheet = {
  build_date: process.env.BUILD_DATE,
};

/* global $, window, document, console */
/* global fetch */
$(document).ready(function(){
  bindSpreadsheetEvents();
});

function bindSpreadsheetEvents() {
  var linkCourse = window.MEMLIKE.course.url,
      idCourse   = window.MEMLIKE.course.id

  // Choose to export either multimedia or classic levels
  var exportElem = document.getElementById('chooseExport0');
  exportElem && exportElem.addEventListener('click', chooseExport);

  exportElem = document.getElementById('chooseExport1');
  exportElem && exportElem.addEventListener('click', chooseExport);

  function chooseExport(){
    var val = this.value;

    document.getElementById(`export${val}`).disabled = false;
    document.getElementById(`export${1 - val}`).disabled = true;
    document.getElementById('exportAlt').disabled = (val == 1);
    document.getElementById('exportMore').disabled = (val == 1);
  }
  // Export using in memory data
  document.getElementById('exportInMemory').addEventListener('click', function(){
    new ExportInMemory();
  });

  // On render/export
  document.getElementById('spreadsheet_conf').addEventListener('submit', function(e){
    e.preventDefault();

    // Get the list of levels selected
    var levelsToExport = [],
        isMultimedia   = (typeof this.elements.export0 == 'undefined' || this.elements.export0.disabled) ? 1 : 0,
        item           = this.elements[`export${isMultimedia}`],
        exportAlt      = !isMultimedia && this.elements.exportAlt.checked,
        exportMore     = !isMultimedia && this.elements.exportMore.checked;

    // Course with no level: retrieve level 1 (ex: /course/233943/livre-1001-phrases-pour-parler-allemand/)
    if(item.type && item.type == 'hidden') {
      levelsToExport.push({
          href : linkCourse,
          idx  : 1,
          title: '',
          media: false,
        });

    // Retrieve selected levels
    } else {
      for(let i = 0; i < item.options.length; i++) {
        if(item.options[i].selected) {
          var rank = item.options[i].value;
          var level = window.MEMLIKE.course.levels[rank];

          levelsToExport.push({
            href: linkCourse + rank,
            idx: rank,
            title: level.name,
            media: level.type == 2,
          });
        }
      }
    }
    console.log('Export levels', levelsToExport);

    // Render or export spreadsheet
    if(isMultimedia) {
      if(document.activeElement.name == 'export'){
        new ExportMultimedia(linkCourse, idCourse, levelsToExport);
      } else {
        new SpreadSheetMultimedia(linkCourse, idCourse, levelsToExport);
      }

    } else {
      if(document.activeElement.name == 'export'){
        new Export(linkCourse, idCourse, levelsToExport, exportAlt, exportMore);
      } else {
        new SpreadSheet(linkCourse, idCourse, levelsToExport, exportAlt, exportMore);
      }
    }
  });
}

//+--------------------------------------------------------
//|
//| RENDER SPREADSHEET (table)
//|
//+--------------------------------------------------------

class SpreadSheet {

  // DOMElement this.body
  // integer    this.idCourse
  // array      this.levels
  // boolean    this.exportAlt

  /**
   * @param string idCourse
   * @param array levels
   * @param boolean exportAlt  - Export alternatives answers
   * @param boolean exportMore - Export extra columns (visible_info, hidden_info, attributes)
   */
  constructor(urlCourse, idCourse, levels, exportAlt, exportMore) {
    this.urlCourse  = urlCourse;
    this.idCourse   = idCourse;
    this.levels     = levels;
    this.exportAlt  = exportAlt;
    this.exportMore = exportMore;
    this.cookies    = window.getCookies();

    // Display a loader
    var container  = document.getElementById('spreadsheet'),
        loading    = this.createLoader(container);

    // Create the spreadsheet
    this.extraHeaders = {};
    this.createBody(container);
    this.createContent(loading);
    this.bindEvents(container);

    this.sort = {idx: 1, asc: 1};
  }

  bindEvents(container) {
    $('.sort', container).on('click', this.sortColumn.bind(this));
  }

  sortColumn(e) {
    var btn = e.target;
    var th = btn.closest('th');
    var tbody = th.closest('table').querySelector('tbody');

    var idx = th.cellIndex;
    var isNumeric = th.dataset.sort == 'numeric';
    var useDataValue = th.dataset.value == '1';

    if (idx == this.sort.idx) {
      this.sort.asc = 1 - this.sort.asc;
    } else {
      this.sort = {
        idx,
        asc: 1,
      }
    }
    var sortDesc = !this.sort.asc;

    var sortValues = function(tr_a, tr_b) {
      var td_a = tr_a.children[idx],
          td_b = tr_b.children[idx];

      var v_a = useDataValue ? td_a.dataset.value : td_a.innerText.trim(),
          v_b = useDataValue ? td_b.dataset.value : td_b.innerText.trim();

      if (sortDesc) {
        [v_b, v_a] = [v_a, v_b];
      }
      if (isNumeric) {
        return parseInt(v_a) - parseInt(v_b);
      }
      return v_a.localeCompare(v_b);
    }
    Array.from(tbody.children).sort(sortValues).forEach((tr) => {
      tbody.appendChild(tr);
    });
  }

  /**
   * Create the loader and it to the container
   * @param DOMElement container
   * @return DOMElement
   */
  createLoader(container) {
    var loading = document.createElement('div');

    loading.setAttribute('class', 'loading-spinner');
    container.innerHTML = '';
    container.appendChild(loading);

    document.getElementById('exportInMemory').style.display = 'none';
    return loading;
  }

  /**
   * Create a table
   * @return DOMElement
   */
  createBody(container) {
    var table = document.createElement('table');
    container.appendChild(table);

    table.innerHTML = `<thead><tr>
      <th class="lvl-idx num" data-key="export_column_level">
        ${window.I18N['export_column_level']}
      </th>
      <th class="item-idx num" data-value="1" data-key="export_column_index">
        ${window.I18N['export_column_index']}
        <button class="sort" type="button">⬍</button>
      </th>
      <th class="item-label" data-key="export_column_label">
        ${window.I18N['export_column_label']}
        <button class="sort" type="button">⬍</button>
      </th>
      <th class="item-definition" data-key="export_column_definition">
        ${window.I18N['export_column_definition']}
        <button class="sort" type="button">⬍</button>
      </th>
      <th class="score num" colspan="2" data-sort="numeric" data-value="1" data-key="export_column_score">
        ${window.I18N['export_column_score']}
        <button class="sort" type="button">⬍</button>
      </th>
      ${this.exportMore ? `<th class="item-more" data-key="export_column_more">${window.I18N['export_column_more']}</th>` : ''}
      </tr></thead>
      <tbody></tbody>`;

    this.body = table.lastElementChild;
  }

  getUrl(idLevel) {
    return `/ajax${this.urlCourse}${idLevel}/preview`;
  }

  /**
   * Populate the body
   */
  async createContent(loading) {
    var n       = this.levels.length-1,
        hasErr  = false;

    for(let i = 0; i <= n; i++) {
      let level = this.levels[i];

      let options = {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.cookies['csrftoken'] || '',
        },
      };
      await fetch(this.getUrl(level.idx), options)
      .then((response) => {
        // Returns 400 if column b isn't defined
        return response.ok ? response.json() : null;
      })
      .then((data) => {
        if(data) {
          var rows   = data.learnables,
              scores = data.progress; // current user scores

          for(let j = 0; j < rows.length; j++) {
            var item = rows[j];

            this.createRow(
              level,
              j,
              item.screens[1], // includes attributes as well
              scores && scores[j]
            );
          }
        }
        if(i == n && loading){
          loading.parentNode.removeChild(loading);
          loading = null;
        }

      }).catch((e) => {
        hasErr = true;
        console.error(e);

        loading.setAttribute('class', 'alert alert-danger');
        loading.innerHTML = window.I18N['error'];
      });

      if(hasErr) {
        break;
      }
    }
    this.end(hasErr);
  }

  /**
   * Create a new row
   * @param object level  - Data about current level
   * @param integer j     - Current row number
   * @param object data   - Row data
   * @param object score  - User score for current word
   * @param object data
   */
  createRow(level, j, data, score) {
    var tr   = document.createElement('tr'),
        html = '';

    html  = `<td class="lvl-idx num"><a href="${level.href}">${level.idx}</a></td>`;
    html += `<td class="item-idx num" data-value=${level.idx.padStart(4, '0') + '-' + j.toString().padStart(4, '0')}>${j+1}</td>`;
    html += `<td class="item-label">${this.getValue(data.item)}</td>`;
    html += `<td class="item-definition">${this.getValue(data.definition)}</td>`;
    html += this.getScore(score);

    if(this.exportMore) {
      html += '<td class="item-more">';
      if (data.audio) {
        html += [data.audio].map(it => {this.addExtraHeader(it.label); return `<div class="more"><span class="highlight">${it.label}</span> ${this.getValue(it, false)}</div>`;}).join('');
      }
      html += data.visible_info.map(it => {this.addExtraHeader(it.label); return `<div class="more"><span class="highlight">${it.label}</span> ${this.getValue(it, false)}</div>`;}).join('');
      html += data.hidden_info.map(it => {this.addExtraHeader(it.label); return `<div class="more"><span class="highlight">${it.label}</span> ${this.getValue(it, false)}</div>`;}).join('');
      html += data.attributes.map(it => {this.addExtraHeader(it.label); return `<div class="more"><span class="highlight">${it.label}</span> <span>${escapeHTML(it.value)}</span></div>`;}).join('');
      html += '</td>';
    }
    tr.innerHTML = html;
    this.body.appendChild(tr);
  }

  /**
   * Keep in mind the extra columns in "More"
   * To be able to export the rendered table to CSV
   * @param string label
   */
  addExtraHeader(label) {
    if(typeof this.extraHeaders[label] == 'undefined') {
      let k = Object.keys(this.extraHeaders).length;

      this.extraHeaders[label] = k;
    }
  }

  /**
   * Returns HTML: the content of the columnm (text, image, audio or video)
   * @param object item
   * @param boolean[optional] checkAlt - [true] Used to disable alternatives in additionnal informations
   * @return string
   */
  getValue(item, checkAlt=true) {
    var txt = '';

    switch(item.kind) {
      case 'text' :
        txt = `<span>${escapeHTML(item.value)}</span>`;
        if(checkAlt && this.exportAlt) {
          for(let i=0; i<item.alternatives.length; i++) {
            txt += '<div class="alt">';
            txt += `<span>${escapeHTML(item.alternatives[i])}</span>`;
            txt += '</div>';
          }
        }
        break;

      case 'image':
        txt = `<img src=${item.value[0]} class="text-image" />`;
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '<div class="alt">';
            txt += `<img src=${item.value[i]} class="text-image" />`;
            txt += '</div>';
          }
        }
        break;

      case 'audio':
        txt = `<audio src=${item.value[0].normal} controls></audio>`;
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '<div class="alt">';
            txt += `<audio src=${item.value[i].normal} controls></audio>`;
            txt += '</div>';
          }
        }
        break;

      case 'video':
        txt = `<video src=${item.value[0]} controls>Your browser does not support the video tag.</video>`;
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '<div class="alt">';
            txt += `<video src=${item.value[i]} controls>Your browser does not support the video tag.</video>`;
            txt += '</div>';
          }
        }
        break;

      default:
        return '';
    }
    return txt;
  }

  /**
   * Returns HTML: the user's score (correct/attemps)
   * @param object score
   * @return string
   */
  getScore(score) {
    if(!score || !score.attempts) {
      return '<td class="score num" colspan="2" data-value="0">-</td>';
    }
    var successRate, className;

    if(score.ignored) {
      successRate = 'Ignored';
      className   = 'ignored';
    } else {
      successRate = parseInt(score.correct / score.attempts * 100) + '%';
      className   = (successRate == 100 ? 'never-missed'
                     : (successRate < 20 ? 'often-missed'
                        : (successRate > 80 ? 'rarely-missed' : 'sometimes-missed')));
    }
    return `<td class="score left num ${className}" title="${successRate}" data-value="${successRate}">${this.truncateNum(''+score.correct)}</td>
            <td class="score right num ${className}" title="${successRate}" data-value="${successRate}">${this.truncateNum(''+score.attempts)}</td>`;
  }

  /**
   * Make sure the number isn't longer than length, or truncate the left (1012, 3 => 12)
   * @param string str
   * @param integer[optional] length - [3]
   * @return string
   */
  truncateNum(str, length=3) {
    if(str <= length) {
      return str;
    }
    return str.substring(str.length-length).replace(/^0+/, '');
  }

  /**
   * Return the filename of the generated CSV
   * @return string
   */
  getFilename() {
    var filename = 'Memrise-' + this.idCourse;

    if(this.levels.length == 1) {
      filename += '-' + this.levels[0].idx;
    }
    return filename + '.csv';
  }

  /**
   * Called when all levels have been fetched and rendered
   * We keep extra data needed to export the data in-memory
   * (rather than fetching all levels all over again)
   *
   * @param boolean hasErr  Used by subclass
   */
  end(hasErr) {
    this.body.dataset.file = this.getFilename();

    // Keep extra headers labels to export current data
    if(Object.keys(this.extraHeaders).length) {
      let extra = [];

      for(let label in this.extraHeaders) {
        extra[this.extraHeaders[label]] = label;
      }
      this.body.dataset.extraHeaders = JSON.stringify(extra);

    } else {
      delete this.body.dataset.extraHeaders;
    }

    document.getElementById('exportInMemory').style.display = null;
  }
}

//+--------------------------------------------------------
//|
//| RENDER SPREADSHEET - MULTIMEDIA (table)
//|
//+--------------------------------------------------------

class SpreadSheetMultimedia {

  // DOMElement this.body
  // string     this.urlCourse
  // array      this.levels

  /**
   * @param string urlCourse
   * @param array levels
   */
  constructor(urlCourse, idCourse, levels) {
    this.urlCourse = urlCourse;
    this.idCourse  = idCourse;
    this.levels    = levels;

    // Display a loader
    var container = document.getElementById('spreadsheet'),
        loading   = this.createLoader(container);

    // Create the spreadsheet
    this.createBody(container);
    this.createContent(loading);
  }

  /**
   * Create the loader and it to the container
   * @param DOMElement container
   * @return DOMElement
   */
  createLoader(container) {
    var loading = document.createElement('div');

    loading.setAttribute('class', 'loading-spinner');
    container.innerHTML = '';
    container.appendChild(loading);

    document.getElementById('exportInMemory').style.display = 'none';
    return loading;
  }

  /**
   * Create a table
   * @return DOMElement
   */
  createBody(container) {
    var table = document.createElement('table');
    container.appendChild(table);

    table.innerHTML = `<thead><tr>
      <th class="lvl-idx num">${window.I18N['export_column_level']}</th>
      <th class="item-definition">${window.I18N['export_column_content']}</th>
      </tr></thead>
      <tbody></tbody>`;

    this.body = table.lastElementChild;
  }

  /**
   * Populate the body
   */
  async createContent(loading) {
    var n      = this.levels.length-1,
        hasErr = false;

    for(let i = 0; i <= n; i++) {
      let level = this.levels[i];

      await fetch(this.getUrl(level.idx), {
        credentials: 'same-origin'
      })
      .then((response) => response.text())
      .then((data) => {
        this.createRow(level, data);

        if(i == n){
          loading.parentNode.removeChild(loading);
          loading = null;
        }

      }).catch((e) => {
        hasErr = true;
        console.error(e);

        loading.setAttribute('class', 'alert alert-danger');
        loading.innerHTML = window.I18N['error'];
      });

      if(hasErr) {
        break;
      }
    }
    this.end(hasErr);
  }

  /**
   * Returns the URL to retrieve the words of a level
   * @param string|integer idLevel
   * @return string
   */
  getUrl(idLevel) {
    return `/ajax${this.urlCourse}${idLevel}/media`;
  }

  /**
   * Create a new row
   * @param object data
   */
  createRow(level, data) {
    var tr   = document.createElement('tr'),
        html = '';

    html  = `<td class="lvl-idx num"><a href="${level.href}">${level.idx}</a></td>`;
    html += `<td class="item-label">
               <h3 class="course-title">${escapeHTML(level.title)}</h3>
               <div class="multimedia-raw" style="display: none">${escapeHTML(data)}</div>
               <div class="multimedia-wrapper">${this.parseMarkdown(data)}</div>
             </td>`;

    tr.innerHTML = html;
    this.body.appendChild(tr);
  }

  /**
   * Converts Markdown to HTML using Memrise's renderer
   * @param string txt
   * @return string
   */
  parseMarkdown(txt) {
    return window.markdown.toHTML(txt);
  }

  /**
   * Return the filename of the generated CSV
   * @return string
   */
  getFilename() {
    var filename = 'Memrise-' + this.idCourse;

    if(this.levels.length == 1) {
      filename += '-' + this.levels[0].idx;
    }
    return filename + '-multimedia.csv';
  }

  /**
   * Called when all levels have been fetched and rendered
   * We keep extra data needed to export the data in-memory
   * (rather than fetching all levels all over again)
   *
   * @param boolean hasErr  Used by subclass
   */
  end(hasErr) {
    this.body.dataset.file = this.getFilename();
    delete this.body.dataset.extraHeaders;

    document.getElementById('exportInMemory').style.display = null;
  }

}

//+--------------------------------------------------------
//|
//| EXPORT CSV
//|
//+--------------------------------------------------------

class Export extends SpreadSheet {

  /**
   * Create the loader and it to the container
   * @param DOMElement container
   * @return DOMElement
   */
  createLoader(container) {
    var loading = document.createElement('div');
    loading.setAttribute('class', 'loading-spinner');

    if(container.children.length) {
      container.insertBefore(loading, container.firstElementChild);
    } else {
      container.appendChild(loading);
    }
    return loading;
  }

  /**
   * Init the content of the CSV
   * @return DOMElement
   */
  createBody(container) {
    this.body    = '';
    this.headers = {};
  }

  /**
   * Create a new row
   * @param object level
   * @param integer j
   * @param object data
   * @param object score
   */
  createRow(level, j, data, score) {
    this.body += level.idx + ',';
    this.body += (j+1) + ',';
    this.body += this.getValue(data.item) + ',';
    this.body += this.getValue(data.definition) + ',';

    if(score && score.attempts){
      this.body += score.correct + ',';
      this.body += score.attempts + ',';
      this.body += parseInt(score.correct / score.attempts * 100);
    } else {
      this.body += ',,';
    }

    // Retrieve additional columns
    if(this.exportMore) {
      var arr = [];

      data.audio && this.getExtraColumns(arr, [data.audio]);
      this.getExtraColumns(arr, data.visible_info);
      this.getExtraColumns(arr, data.hidden_info);
      this.getExtraColumns(arr, data.attributes);

      // Add columns
      for(let i=0; i<arr.length; i++){
        this.body += ',';
        this.body += arr[i] || '';
      }
    }
    this.body += '\n';
  }

  /**
   * Retrieves the additional content in data
   * And puts it in the right place in arr
   * @param array arr
   * @param object[pointer] data
   */
  getExtraColumns(arr, data){
    var k;
    for(let i=0; i<data.length; i++) {
      var it = data[i];

      if(typeof this.headers[it.label] != 'undefined') {
        k = this.headers[it.label];
      } else {
        k = Object.keys(this.headers).length;
        this.headers[it.label] = k;
      }

      if(typeof it.kind != 'undefined') {
        arr[k] = this.getValue(it, false);
      } else {
        arr[k] = escapeCSV(it.value);
      }
    }
  }

  /**
   * Returns CSV-escaped text: the content of the column (text, image, audio or video)
   * @param object item
   * @param boolean[optional] checkAlt - [true] Used to disable alternatives in additionnal informations
   * @return string
   */
  getValue(item, checkAlt=true) {
    var txt;

    switch(item.kind) {
      case 'text' :
        txt = item.value;
        if(checkAlt && this.exportAlt) {
          for(let i=0; i<item.alternatives.length; i++) {
            txt += '\n' + item.alternatives[i];
          }
        }
        break;

      case 'image':
        txt = item.value[0];
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '\n' + item.value[i];
          }
        }
        break;

      case 'audio':
        txt = item.value[0].normal;
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '\n' + item.value[i].normal;
          }
        }
        break;

      case 'video':
        txt = item.value[0];
        if(checkAlt && this.exportAlt) {
          for(let i=1; i<item.value.length; i++) {
            txt += '\n' + item.value[i];
          }
        }
        break;

      default:
        return '';
    }
    return escapeCSV(txt);
  }

  /**
   * Trigger download of the CSV (in-memory)
   * @param boolean hasErr
   */
  end(hasErr) {
    if(hasErr) {
      return;
    }
    window.download(this.getHeaders() + '\n' + this.body, this.getFilename(), 'text/csv');
  }

  /**
   * Retrieve all headers
   * Includes visible_info / hidden_info / attributes if that option was checked
   * @return string
   */
  getHeaders() {
    var headers = [
      window.I18N['export_column_level'],
      window.I18N['export_column_index'],
      window.I18N['export_column_label'],
      window.I18N['export_column_definition'],
      window.I18N['export_column_score_correct'],
      window.I18N['export_column_score_attempts'],
      window.I18N['export_column_score_percent'],
    ].join(',');

    if(!this.exportMore) {
      return headers;
    }
    var extra = [];
    for(var label in this.headers) {
      extra[this.headers[label]] = escapeCSV(label);
    }
    return headers + (extra.length ? ',' + extra.join(',') : '');
  }
}

//+--------------------------------------------------------
//|
//| EXPORT CSV - MULTIMEDIA
//|
//+--------------------------------------------------------


class ExportMultimedia extends SpreadSheetMultimedia {

  /**
   * Create the loader and it to the container
   * @param DOMElement container
   * @return DOMElement
   */
  createLoader(container) {
    var loading = document.createElement('div');
    loading.setAttribute('class', 'loading-spinner');

    if(container.children.length) {
      container.insertBefore(loading, container.firstElementChild);
    } else {
      container.appendChild(loading);
    }
    return loading;
  }

  /**
   * Init the content of the CSV
   * @return DOMElement
   */
  createBody(container) {
    this.body = [
      window.I18N['export_column_level'],
      window.I18N['export_column_label'],
      window.I18N['export_column_content'],
    ].join(',') + '\n';
  }

  /**
   * Create a new row
   * @param object data
   */
  createRow(level, data) {
    this.body += level.idx + ',';
    this.body += escapeCSV(level.title) + ',';
    this.body += escapeCSV(data) + '\n';
  }

  /**
   * Trigger download of the CSV
   * @param boolean hasErr
   */
  end(hasErr) {
    if(!hasErr) {
      window.download(this.body, this.getFilename(), 'text/csv');
    }
  }
}

//+--------------------------------------------------------
//|
//| EXPORT IN-MEMORY
//|
//+--------------------------------------------------------

class ExportInMemory {

  /**
   * Entrypoint
   */
  constructor() {
    var container    = document.getElementById('spreadsheet'),
        body         = container.querySelector('tbody'),
        filename     = body.dataset.file;

    var extraHeaders = this.decodeExtraHeaders(body.dataset.extraHeaders),
        headers      = Array.from(container.querySelector('thead tr').children)
                            .map(node => node.dataset.key);

    var csv = this.getHeaders(headers, extraHeaders) + '\n';
    csv += this.getData(body, headers, extraHeaders);

    window.download(csv, filename || ('Memrise-' + this.idCourse + '.csv'), 'text/csv');
  }

  /**
   * @param array headers
   * @param array extraHeaders
   * @return string
   */
  getHeaders(_headers, extraHeaders) {
    var headers = [..._headers];

    var k = headers.indexOf('export_column_score');
    if(k != -1) {
      headers.splice(k, 1, ...[
        'export_column_score_correct',
        'export_column_score_attempts',
        'export_column_score_percent',
      ]);
    }
    k = headers.indexOf('export_column_more');
    if(k != -1) {
      headers.splice(k, 1, ...extraHeaders);
    }
    k = headers.indexOf('export_column_content');
    if(k != -1) {
      headers.splice(k, 1, ...[
        'export_column_label',
        'export_column_content',
      ]);
    }
    return headers.map(label => escapeCSV(window.I18N[label])).join(',');
  }

  /**
   * Retrieve the JSON-decoded list of extra headers
   * Or an empty list
   *
   * @param string|undefined data
   * @return array
   */
  decodeExtraHeaders(data) {
    return typeof data == 'undefined' ? [] : JSON.parse(data);
  }

  /**
   * Retrieve the rendered table as a CSV string
   * @param DOMElement body
   * @return string
   */
  getData(body, headers, extraHeaders) {
    var csv = '';

    for(let i=0; i<body.children.length; i++) {
      let tr    = body.children[i],
          data  = [];

      let k = 0;
      for(let j=0; j<headers.length; j++) {
        let slug  = headers[j],
            td    = tr.children[k];

        switch(slug) {
           case 'export_column_level':
           case 'export_column_index':
             csv += td.innerText + ',';
             break;

           case 'export_column_score':
             if(!td.hasAttribute('colspan')) {
                let correct = parseInt(td.innerText, 10),
                    attempt = parseInt(tr.children[k+1].innerText, 10);
                k++;

                csv += correct + ',';
                csv += attempt + ',';
                csv += parseInt(correct/attempt * 100);
              } else {
                csv += ',,';
              }

              break;

            case 'export_column_more':
              let more  = td.querySelectorAll('.more'),
                  extra = {};

              // Retrieve all additionnal that have been defined
              for(let j2=0; j2<more.length; j2++) {
                let label   = more[j2].firstElementChild.innerText,
                    content = this.getValue(more[j2].lastElementChild);

                 extra[label] = escapeCSV(content);
              }

              // Put them in order
              for(let j2=0; j2<extraHeaders.length; j2++) {
                let label = extraHeaders[j2];

                csv += ',' + (typeof extra[label] == 'undefined' ? '' : extra[label]);
              }
              break;

          // Multimedia
          case 'export_column_content':
            csv += escapeCSV(td.children[0].innerText.trim()) + ',';
            csv += escapeCSV(td.children[1].innerText.trim());
            break;

          default:
             csv += escapeCSV(this.getValue(td.firstElementChild, true)) + ',';
             break;
        }
        k++;
      }
      csv += '\n';
    }
    return csv;
  }

  /**
   * Retrieve the text of a DOMElement
   * @param DOMElement node
   * @param boolean siblings - [false] Return the content of siblings too
   * @return string
   */
  getValue(node, siblings=false) {
    if(['IMG', 'AUDIO', 'VIDEO'].indexOf(node.nodeName) != -1) {
      var links = Array.from(node.parentNode.querySelectorAll(node.nodeName))
                       .map(node => node.getAttribute('src'));
      return links.join('\n');
    } else {
      return siblings ? node.parentNode.innerText : node.innerText;
    }
  }
}

//+--------------------------------------------------------
//|
//| COMMON FONCTIONS (in-memory)
//|
//+--------------------------------------------------------

/**
 * Escape HTML
 * @param string txt
 * @return txt
 */
function escapeHTML(txt) {
  if(typeof txt != 'string') {
    return '';
  }
  return txt.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Escape text for CSV
 * Surround with quotes and escape quotes inside text
 */
function escapeCSV(txt) {
  if(typeof txt != 'string') {
    return '';
  }
  return '"' + txt.replace(/"/g, '""') + '"';
}
