var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

function escapeHtml (string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
    });
}

function showSimpleDialog(title, msg, elementToHighlight, callback) {
    if (elementToHighlight)
        elementToHighlight.effect('highlight', { color: 'yellow' }, 3000);

    var simpleDialog = $('#dialog-simple');
    simpleDialog.attr('title', title);
    simpleDialog.text(msg);
    simpleDialog.dialog({
        modal: true,
        width: 430,
        buttons: {
            'OK': function() {
                $(this).dialog('close');
                if (callback)
                    callback();
            }
        }
    });
}

