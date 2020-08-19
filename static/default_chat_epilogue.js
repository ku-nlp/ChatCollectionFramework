//
// The code here is loaded after default_chat.js
//

console.log('Loading default_chat_epilogue.js...');

function addEventHandlers() {
    $('#send').on('click', sendMsg);
    $('#stop-chat').on('click', stopChat);
}

function fm_addEventHandlers() {
    if (typeof preAddEventHandlers != 'undefined')
        preAddEventHandlers();
    if (typeof addEventHandlers != 'undefined')
        addEventHandlers();
    if (typeof postAddEventHandlers != 'undefined')
        postAddEventHandlers();
}

$(document).ready(function() {
    fm_addEventHandlers();
});

console.log('default_chat_epilogue.js loaded.');
