/** @jsx h */
'use strict';

const { h, Component, render } = window.preact;

/* global $ */
/* global navigator, Blob, URL, File, fetch */

$(document).ready(function () {
  Object.freeze(window.course);

  render(h(Edit, { course: window.course }), document.getElementById('edit-levels'));
});

//+--------------------------------------------------------
//| Render Levels
//+--------------------------------------------------------

class Edit extends Component {
  constructor(props) {
    super(props);
    this.setNewRow = this.setNewRow.bind(this);
  }

  setNewRow(new_row) {
    this.new_row = new_row;
    bindEvents(new_row);
  }

  render() {
    var opentab = window.location.hash.match(/#(i|l)_(\d+)/);

    return h(
      'div',
      null,
      window.course.levels.map((level, i) => {
        var show = false;
        if (opentab) {
          if (opentab[1] == "i") {
            show = i + 1 == opentab[2];
          } else {
            show = level.id == opentab[2];
          }
        }
        return h(EditLevel, { show: show, key: i, level: level, setNewRow: this.setNewRow });
      })
    );
  }
}

class EditLevel extends Component {
  constructor(props) {
    super(props);

    this.state = { "show": false };
    this.toggle = this.toggle.bind(this);
  }

  componentDidMount() {
    if (this.props.show) {
      this.getData();
    }
  }

  toggle() {
    if (!this.state.show && !this.data) {
      this.getData();
    } else {
      this.setState({
        show: !this.state.show
      });
    }
  }

  getData() {
    $.ajax({
      url: "/ajax/level/" + this.props.level.id,
      success: function (data) {
        if (this.props.level.pool) {
          var div = $('.table-container', data.rendered);

          this.data = div.get(0).outerHTML;
          this.props.setNewRow(div.find('tr').last().get(0).outerHTML);
        } else {
          this.data = $('.level-multimedia', data.rendered).get(0).outerHTML;
        }
        this.setState({
          show: true
        });
      }.bind(this)
    });
  }

  render() {
    var level = this.props.level;

    return h(
      'div',
      { 'class': "edit-level nicebox" + (this.state.show ? "" : " collapsed"), 'data-level-id': level.id, 'data-pool-id': level.pool || "" },
      h(
        'div',
        { 'class': 'edit-level-actions' },
        this.state.show && h(
          'label',
          { 'class': 'export action', title: window.i18n._export },
          h('i', { dangerouslySetInnerHTML: { __html: '&darr;' } })
        ),
        this.state.show && h(
          'label',
          { 'class': 'import action', title: window.i18n._import, 'for': "import_" + level.id },
          h('input', { type: 'file', id: "import_" + level.id }),
          h('i', { dangerouslySetInnerHTML: { __html: '&uarr;' } })
        ),
        h('label', { 'class': 'toggle action', onClick: this.toggle, dangerouslySetInnerHTML: { __html: '&updownarrow;' } })
      ),
      h(
        'div',
        { 'class': 'edit-level-label' },
        h(
          'label',
          null,
          level.name
        ),
        !level.pool && h(
          'span',
          null,
          '\xA0(multimedia)'
        )
      ),
      this.state.show && h('div', { dangerouslySetInnerHTML: { __html: this.data } })
    );
  }
}

//+--------------------------------------------------------
//| Events
//+--------------------------------------------------------

var isInit = false,
    focused = false,
    altInit = false;

function bindEvents(new_row) {
  if (isInit) {
    return;
  }
  isInit = true;
  init();

  function init() {
    $('#edit-levels')

    // New row
    .on('focus', 'input', focus_input).on('blur', '.adding input.wide', blur_input_adding).on('focus', '.adding tr:last-child input.wide', focus_lastRow)

    // Update cell
    .on('click', 'div.text', click_cell).on('keyup', 'input.wide', type_cell).on('blur', '.things input.wide', blur_input_thing).on('click', '.multimedia-edit button', click_saveMultimedia)

    // Update alternatives
    .on('click', '.edit-alts', click_editAlt)

    // Update attachments
    .on('change', '.things input[type="file"]', send_file).on('click', '.dropdown-toggle', click_displayFiles).on('click', '.dropdown-row .ico-trash', click_removeFile)

    // Delete row
    .on('click', '.ico-close', click_deleteRow)

    // Import/export
    .on('click', '.export', click_export).on('change', '.import input', send_import);
  }

  //+---------------------------------------------------------------------------
  // Remember current input focused
  function focus_input() {
    focused = this;
  }

  //+---------------------------------------------------------------------------
  // On blur cell in adding tbody: add row
  function blur_input_adding() {
    focused = false;

    // Retrieve the row datas
    var $tr = $(this).closest('tr'),
        data = {},
        empty = true;

    $tr.find('td[data-key]').each(function () {
      var val = $(this).find('input').val();
      if (val) {
        empty = false;
      }
      data[$(this).data('key')] = val;
    });
    if (empty) {
      return;
    }

    // Check if we changed row or just cell of the row
    setTimeout(function () {
      if (focused && $(focused).closest('tr').is($tr)) {
        return;
      }
      $tr.addClass('disabled');
      addRow($tr, data);
    }, 100);
  }

  // POST new row
  function addRow($tr, data, uploads) {
    var $level = $tr.closest('.edit-level'),
        idLevel = $level.data('level-id');

    $.ajax({
      url: "/ajax/level/" + idLevel + "/add",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        data: JSON.stringify(data)
      },
      success: function (json) {
        var html = json.rendered_thing,
            $newTr = $(html).appendTo($('.things', $level));

        if (uploads && window.File) {
          downloadFromUrls($newTr, idLevel, uploads);
        }
        $tr.remove();
      },
      error: function (xhr) {
        console.error(xhr);
        $tr.remove('disabled');
      }
    });
  }

  // Import rows: handle file upload from URL
  function downloadFromUrls($tr, idLevel, uploads) {
    var thingId = $tr.data('thing-id');

    for (var i = 0; i < uploads.length; i++) {
      var upload = uploads[i],
          cellId = upload[0],
          $column = $tr.children('[data-key="' + cellId + '"]');

      downloadFromUrl($column, thingId, cellId, upload);
    }
  }
  function downloadFromUrl($column, thingId, cellId, upload) {
    var name = upload[1],
        url = upload[2],
        mime = upload[3];

    fetch(url).then(res => res.blob()).then(blob => {
      var file = new File([blob], name, { type: mime });

      uploadFile($column, cellId, thingId, file);
    });
  }

  //+---------------------------------------------------------------------------
  // Focus last row: add a new row
  function focus_lastRow() {
    $(this).closest('.adding').append(new_row);
  }

  //+---------------------------------------------------------------------------
  // Click on cell: display input
  function click_cell() {
    if (this.firstElementChild) {
      return;
    }
    var input = document.createElement('input');
    input.value = this.innerHTML;
    input.type = "text";
    input.className = "wide";
    this.appendChild(input);
    input.focus();
  }

  //+---------------------------------------------------------------------------
  // On enter: focus next row
  function type_cell(e) {
    if (e.which != 13) {
      return;
    }
    var $tr = $(e.target).closest('tr'),
        $nextTr = $tr.next('tr');

    if ($nextTr.length == 0) {
      $nextTr = $tr.closest('tbody').next('tbody').children(':not(.header)').first();
      $nextTr.find('input.wide').first().focus();
    } else {
      $nextTr.find('div.text, input.wide').first().trigger('click').focus();
    }
  }

  //+---------------------------------------------------------------------------
  // On click "alternatives": edit alternatives
  function click_editAlt(e) {
    e.preventDefault();

    var $btn = $(e.target),
        thingId = $btn.closest('.thing').data('thing-id'),
        cellId = $btn.closest('.column').data('key');

    $.ajax({
      url: "/ajax/level/" + thingId + "/alt",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer
      },
      success: function (data) {
        var alts = data.thing.columns[cellId].alts,
            html = `<div class="alts">
          ${alts.map(alt => `<div class="alt">
            <input type="text" name="${alt.id}" value=${alt.val} />
            <button type="button" class="alt-action"></button>
          </div>`).join('')}

          <div class="alt">
            <input type="text" value="" />
            <button type="button" class="alt-action"></button>
          </div>
        </div>

        <div class="alt-actions">
          <button class="btn alt-cancel">Annuler</button>
          <button class="btn active alt-save" data-cell="${cellId}" data-thing=${thingId}>Sauvegarder</button>
        </div>`;

        window.modal.open(html);
        bindAltEvents();
      }
    });
  }

  function bindAltEvents() {
    if (altInit) {
      return;
    }
    altInit = true;

    $('#modal').on('click', '.alt-cancel', function () {
      window.modal.close();
    }).on('click', '.alt-action', click_altAction).on('click', '.alt-save', click_altSave);
  }

  // Click alt action: last row = add new, others = remove current
  function click_altAction() {
    var $alt = $(this).closest('.alt'),
        $alts = $(this).closest('.alts');

    if ($alts.children().last().is($alt)) {
      $alts.append(`<div class="alt">
        <input type="text" value="" />
        <button type="button" class="alt-action"></button>
      </div>`);
    } else {
      $alt.remove();
    }
  }

  // Click alt save: save modal content and close
  function click_altSave() {
    var cellId = $(this).data('cell'),
        thingId = $(this).data('thing'),
        alts = [];

    $('#modal input').each(function () {
      if (this.value.trim()) {
        alts.push(this.value.trim());
      }
    });

    $.ajax({
      url: "/ajax/level/" + thingId + "/alt_edit",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        alts: JSON.stringify(alts),
        cellId: cellId
      },
      success: function (data) {
        window.modal.close();
      }
    });
  }

  //+---------------------------------------------------------------------------
  // On click "delete": delete row
  function click_deleteRow(e) {
    e.preventDefault();
    if (confirm('Delete this row ?')) {
      removeRow($(e.target).closest('tr'));
    }
  }

  function removeRow($tr) {
    var $level = $tr.closest('.edit-level'),
        thingid = $tr.data('thing-id'),
        levelid = $level.data('level-id');

    $.ajax({
      url: "/ajax/level/" + levelid + "/remove",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        id_thing: thingid
      },
      success: function (json) {
        $tr.remove();
      },
      error: function (xhr) {
        console.error(xhr);
        $tr.remove('disabled');
      }
    });
  }

  //+---------------------------------------------------------------------------
  // On blur cell in things tbody: update cell
  function blur_input_thing() {
    var txt = this.value.trim(),
        $div = $(this.parentNode);

    if (txt == $div.text()) {
      $div.text(txt);
      return;
    }
    $div.text(txt);

    var thingId = $div.closest('.thing').data('thing-id'),
        cellId = $div.closest('.column').data('key');

    updateCell(thingId, cellId, txt);
  }

  // POST new cell value
  function updateCell(thingId, cellId, cellValue) {
    $.ajax({
      url: "/ajax/level/" + thingId + "/edit",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        cellId: cellId,
        cellValue: cellValue
      },
      error: function () {
        alert('Something went wrong when trying to update cell');
      }
    });
  }

  //+---------------------------------------------------------------------------
  // On send file: upload file
  function send_file(e) {
    var $column = $(this).closest('.column'),
        cellId = $column.data('key'),
        thingId = $(this).closest('.thing').data('thing-id'),
        file = this.files[0];

    uploadFile($column, cellId, thingId, file);
  }

  function uploadFile($column, cellId, thingId, file) {
    var fd = new FormData();
    fd.append('file', file);
    fd.append('csrftoken', window.course.csrftoken);
    fd.append('referer', window.course.referer);
    fd.append('cellId', cellId);

    $.ajax({
      url: '/ajax/level/' + thingId + '/upload',
      data: fd,
      processData: false,
      contentType: false,
      type: 'POST',
      success: function (data) {
        if (data.message) {
          alert(data.message);
        }
        $column.replaceWith(data.rendered);
      }
    });
  }

  //+---------------------------------------------------------------------------
  // On click files: display attachments
  function click_displayFiles(e) {
    var div = e.target.nextElementSibling;
    div.innerHTML = div.innerHTML.replace(/ src="#"/g, '').replace(/ data-url="/g, ' src="');
  }

  //+---------------------------------------------------------------------------
  // On click remove file: remove attachment
  function click_removeFile(e) {
    removeFile($(e.target));
  }

  function removeFile($btn) {
    var fileId = $btn.closest('.dropdown-row').data('file-id'),
        $column = $btn.closest('.column'),
        cellId = $column.data('key'),
        thingId = $btn.closest('.thing').data('thing-id');

    $.ajax({
      url: '/ajax/level/' + thingId + '/upload_remove',
      data: {
        "csrftoken": window.course.csrftoken,
        "referer": window.course.referer,
        "cellId": cellId,
        "fileId": fileId
      },
      type: 'POST',
      success: function (data) {
        if (data.message) {
          alert(data.message);
        }
        $column.replaceWith(data.rendered);
      }
    });
  }

  //+---------------------------------------------------------------------------
  // On click save: update multimedia content
  function click_saveMultimedia() {
    var $btn = $(this);
    $btn.attr('disabled', 'disabled');

    var idLevel = $btn.closest('.edit-level').data('level-id');
    $.ajax({
      url: "/ajax/level/" + idLevel + "/edit_multimedia",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        txt: $btn.prev().val()
      },
      success: function () {
        $btn.removeAttr('disabled');
      }
    });
  }

  //+---------------------------------------------------------------------------
  function click_export() {
    var $level = $(this).closest('.edit-level'),
        idLevel = $level.data('level-id'),
        $table = $level.find('table'),
        row = [],
        csvContent = "";

    // Get headers
    $table.children('.columns').find('.column,.attribute').each(function () {
      row.push($(this).text().trim());
    });
    csvContent += exportCsv(row);

    // Get rows
    $table.children('.things').children().each(function () {
      var empty = true;

      row = [];

      // Get columns
      $(this).children('.column,.attribute').each(function () {
        var $col = $(this),
            txt = "";

        // Text
        if ($col.hasClass('text')) {
          txt = $col.find('.text').text().trim();

          // Image attachment
        } else if ($col.hasClass('image')) {
          var list = [];

          // Get list of images
          $col.find('.images').children('.dropdown-row').each(function () {
            var $item = $(this).find('img'),
                url = $item.attr('data-url');

            if (!url) {
              url = $item.attr('src');
            }
            if (url && url != "#") {
              var filename = url.substring(url.lastIndexOf('/') + 1);
              list.push(filename + ' (' + url + ')');
            }
          });
          txt = list.join(',');
        } else if ($col.hasClass('audio')) {
          var list = [];

          // Get list of audios
          $col.find('.audios').children('.dropdown-row').each(function () {
            var $item = $(this).find('a'),
                url = $item.attr('data-url');

            if (!url) {
              url = $item.attr('src');
            }
            if (url && url != "#") {
              var filename = url.substring(url.lastIndexOf('/') + 1);
              list.push(filename + ' (' + url + ')');
            }
          });
          txt = list.join(',');
        }

        // Add column to row
        if (txt) {
          empty = false;
        }
        row.push(txt);
      });

      // Export row
      if (!empty) {
        csvContent += exportCsv(row);
      }
    });
    download(csvContent, window.course.title + '_' + idLevel + '.csv', 'text/csv;encoding:utf-8');
  }

  function send_import(e) {
    if (!e.target.files) {
      return;
    }
    var file = e.target.files[0];
    if (file.type != "text/csv") {
      alert('You should send a .csv file (comma separated)');
      return;
    }

    var reader = new FileReader(),
        $level = $(this).closest('.edit-level');
    reader.onload = function (f) {
      return function (e) {
        import_file($level, e.target.result);
      };
    }(file);

    reader.readAsText(file);
  }

  function import_file($level, content) {
    var data = $.csv.toArrays(content);
    if (!data.length) {
      return;
    }

    var $table = $level.find('table'),
        $adding = $table.children('.adding'),
        table_headers = [],
        table_keys = [],
        types = [];

    // Get table headers
    $table.children('.columns').find('.column,.attribute').each(function () {
      var $col = $(this),
          type = "text";

      if ($col.hasClass("image")) {
        type = "image";
      } else if ($col.hasClass("audio")) {
        type = "audio";
      }
      types.push(type);

      table_headers.push($col.text().trim().toLowerCase());
      table_keys.push($col.data('key'));
    });

    // Get position of headers in CSV
    var headers = [];
    for (var i = 0; i < data[0].length; i++) {
      var header = data[0][i].trim(),
          k = table_headers.indexOf(header.toLowerCase());

      headers.push(k == -1 ? -1 : table_keys[k]);
    }
    table_headers = null;
    table_keys = null;

    // Import rows
    for (var i = 1; i < data.length; i++) {
      var row = data[i],
          row_import = {},
          $tr = false,
          row_upload = [];

      // Get row content in the right order
      for (var j = 0; j < row.length; j++) {
        if (headers[j] == -1) {
          continue;
        }
        var txt = row[j].trim();
        if (!txt) {
          continue;
        }

        // Create a new row
        if (!$tr) {
          $tr = $(new_row).appendTo($adding).prev().addClass('disabled');
        }

        // Add its value
        if (types[j] == "text") {
          row_import[headers[j]] = txt;

          var $td = $tr.children('[data-key="' + headers[j] + '"]');
          $td.find('input').val(txt);

          // Upload its attachments once added
        } else {
          var list = txt.split(",");

          for (var l = 0; l < list.length; l++) {
            var item = list[l],
                match = item.match(/^([^(]+)\(([^)]+)\)$/);

            if (!match) {
              continue;
            }
            var filename = match[1].trim(),
                mime = "",
                ext = filename.substring(filename.lastIndexOf('.') + 1);

            switch (ext) {
              case "png":
                mime = "image/png";break;
              case "jpg":
                mime = "image/jpeg";break;
              case "jpeg":
                mime = "image/jpeg";break;
              case "gif":
                mime = "image/gif";break;
              case "mp3":
                mime = "audio/mpeg";break;
              case "mp4":
                mime = "video/mp4";break;
              case "aac":
                mime = "audio/aac";break;
            }
            if (!mime) {
              continue;
            }
            row_upload.push([headers[j], filename, match[2].trim(), mime]);
          }
        }
      }

      // Create a new table row
      addRow($tr, row_import, row_upload);
    }
  }
}

/**
 * @param array row
 * @return string
 */
function exportCsv(row) {
  var txt = "";

  for (var i = 0; i < row.length; i++) {
    if (i > 0) {
      txt += ",";
    }
    if (row[i].indexOf(',') == -1) {
      txt += row[i];
    } else {
      txt += '"' + row[i].replace(/\\/g, "\\\\").replace(/"/g, '\"') + '"';
    }
  }
  return txt + "\n";
}

/**
 * Trigger a file download of the given mimeType
 * ex: download(csvContent, 'dowload.csv', 'text/csv;encoding:utf-8');
 * 
 * @param string content
 * @param string fileName
 * @param mimeType
 */
var download = function (content, fileName, mimeType) {
  var a = document.createElement('a');
  mimeType = mimeType || 'application/octet-stream';

  // IE10
  if (navigator.msSaveBlob) {
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
//# sourceMappingURL=edit.js.map