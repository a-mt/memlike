/** @jsx h */
'use strict';

const { h, Component, render } = window.preact;

/* global $ */
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
  }

  // Add events
  componentDidMount() {
    var self = this,
        focused = false;

    // Update cell
    $('#edit-levels').on('click', '.edit-alts', function (e) {
      e.preventDefault();
      self.editAlts(e.target);
    }).on('click', 'div.text', function () {
      if (this.firstElementChild) {
        return;
      }
      var input = document.createElement('input');
      input.value = this.innerHTML;
      input.type = "text";
      input.className = "wide";
      this.appendChild(input);
      input.focus();
    }).on('blur', '.things input.wide', function () {
      var txt = this.value,
          $div = $(this.parentNode);
      $div.text(txt);

      var thingId = $div.closest('.thing').data('thing-id'),
          cellId = $div.closest('.column').data('key');
      self.updateCell(thingId, cellId, txt);

      // New row
    }).on('blur', '.adding input.wide', function () {
      focused = false;

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
      setTimeout(function () {
        if (focused && $(focused).closest('tr').is($tr)) {
          return;
        }
        $tr.addClass('disabled');
        self.addRow($tr, data);
      }, 100);

      // Add new row
    }).on('focus', 'input', function () {
      focused = this;
    }).on('focus', '.adding tr:last-child input.wide', function () {
      $(this).closest('.adding').append(self.new_row);

      // Edit multimedia
    }).on('click', '.multimedia-edit button', function () {
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
    });
  }

  editAlts(btn) {
    var thingId = $(btn).closest('.thing').data('thing-id'),
        cellId = $(btn).closest('.column').data('key'),
        self = this;

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
        self.bindAltEvents();
      }
    });
  }
  bindAltEvents() {
    if (this.altInit) {
      return;
    }
    this.altInit = true;

    $('#modal').on('click', '.alt-cancel', function () {
      window.modal.close();
    }).on('click', '.alt-action', function () {
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
    }).on('click', '.alt-save', function () {
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
    });
  }

  // POST new cell value
  updateCell(thingId, cellId, cellValue) {
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

  // POST new row
  addRow($tr, data) {
    var $level = $tr.closest('.edit-level'),
        levelid = $level.data('level-id');

    $.ajax({
      url: "/ajax/level/" + levelid + "/add",
      method: "POST",
      data: {
        csrftoken: window.course.csrftoken,
        referer: window.course.referer,
        data: JSON.stringify(data)
      },
      success: function (json) {
        var html = json.rendered_thing;

        $('.things', $level).append(html);
        $tr.remove();
      },
      error: function (xhr) {
        console.error(xhr);
        $tr.remove('disabled');
      }
    });
  }

  render() {
    return h(
      'div',
      null,
      window.course.levels.map((level, i) => h(EditLevel, { key: i, level: level, setNewRow: this.setNewRow }))
    );
  }
}

class EditLevel extends Component {
  constructor(props) {
    super(props);

    this.state = { "show": false };
    this.toggle = this.toggle.bind(this);
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
        h('span', { 'class': 'toggle', onClick: this.toggle, dangerouslySetInnerHTML: { __html: '&updownarrow;' } })
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
//# sourceMappingURL=edit.js.map