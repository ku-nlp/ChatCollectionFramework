//
// The code here is loaded after default_chat_prologue.js and 
// before default_chat_epilogue.js
//
console.log('Loading default_chat.js...');

var isTooShortDialogShown = false;
var isTooLongDialogShown = false;

var chatroomTimestamp = null;

var confirmBeforeStopChat = true;            
var needsLeavingChatroom = true;

// Prevent subsequent polls when the user is leaving.
var isLeaving = false;

var stopChatConfirmed = false;
var events = [];
var pollXhr = null;
var dialog = null;
var waitStartTime = null;
var waitingInterval = null;
var isDialogStarted = false;
var isDialogOver = false;

function updateProgress(data) {
    var color;
    var progressTitleMsg;
    var msgCountSelf = getMessageCountFor('self');
    var msgCountOther = getMessageCountFor('other');
    if (msgCountSelf < MSG_COUNT_LOW && msgCountOther < MSG_COUNT_LOW) {
        color = 'red';
        progressTitleMsg = 'チャットがまだ十分な長さに達していません。チャットをまだ続けて下さい。';
    }
    else if (msgCountSelf < MSG_COUNT_HIGH - 5 && msgCountOther < MSG_COUNT_HIGH - 5) {
        color = 'yellow';
        progressTitleMsg = 'もう少しでチャットが規定の長さに達します。あと少しチャットを続けて下さい。';
    }
    else if (msgCountSelf < MSG_COUNT_HIGH && msgCountOther < MSG_COUNT_HIGH) {
        color = 'green';
        progressTitleMsg = 'チャットが規定の長さになりました。数回のやり取りで自然な形で対話を終了させて下さい。';
    }
    else {
        color = 'red';
        progressTitleMsg = 'チャットが長過ぎるようです。チャットを終了して下さい。';
    }
    var width = (msgCountSelf + msgCountOther) / (MSG_COUNT_HIGH * 2);
    width = width * 90;
    $('img#chat-progressbar').attr('src', 'default_static/images/' + color + '.png');
    $('img#chat-progressbar').attr('title', progressTitleMsg);
    $('img#chat-progressbar').attr('width', width + '%');
}

function getMessageCountFor(user) {
    var n = 0;
    for (var i = 0; i < events.length; i++) {
        if (events[i].type == 'msg' && events[i].from == user)
            n++;
    }
    return n;
}

function updateModel(data) {
    if (!data) {
        console.log('data is null!');
        return;
    }
    chatroomTimestamp = data.modified;
    var latestEvents = data.latestEvents;
    if (!latestEvents) {
        console.log('latestEvents is null!');
        return;
    }
    for (var i = 0, j = 0; i < latestEvents.length; i++) {
        while (j < events.length && events[j].timestamp < latestEvents[i].timestamp) 
            j++;
        if (j < events.length) {
            if (events[j].timestamp == latestEvents[i].timestamp && events[j].from == latestEvents[i].from)
                j++;
            else 
                events.splice(j + 1, 0, latestEvents[i]);
        }
        else
            events.push(latestEvents[i]);
    }
    updateProgress(data);
}

function buildEntry(msg) {
    var msgClass = 'msg ' + (msg.from == 'self' && isFirstUser || msg.from != 'self' && !isFirstUser ? 'msg-left' : 'msg-right');
    var user = (msg.from == 'self' ? 'あなた' : '相手');
    var timestamp = new Date(msg.timestamp.substring(0, msg.timestamp.indexOf('.')) + 'Z');
    var time = (timestamp.getHours() < 10 ? '0' + timestamp.getHours() : timestamp.getHours()) + ':' + 
        (timestamp.getMinutes() < 10 ? '0' + timestamp.getMinutes() : timestamp.getMinutes()) + ':' + 
        (timestamp.getSeconds() < 10 ? '0' + timestamp.getSeconds() : timestamp.getSeconds());
    var body = msg.body;
    if (msg.type == 'msg') {
        var reUrl = /(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))/g;
        msg.body.replace(reUrl, '<a href="$1" target="_blank">$1</a>');
        body = escapeHtml(body);
        body = body.replace(/\n/g, '<br/>');
    }

    var entry = '<div class="' + msgClass + '">';
    entry += '<div class="msg-avatar"></div>';
    entry += '<div class="msg-bubble msg-type-' + msg.type + '">';
    entry += '<div class="msg-header">';
    entry += '<div class="msg-from">' + msg.from + '</div>';
    entry += '<div class="msg-timestamp">' + msg.timestamp + '</div>';
    entry += '<div class="msg-user">' + user + '</div>';
    entry += '<div class="msg-time">' + time + '</div>';
    entry += '</div>';
    entry += '<div class="msg-body">' + body + '</div>';
    entry += '</div>';
    entry += '</div>';
    return entry; 
}

function updateView() {
    var needsScrolling = false;
    var shownMsgContainer = $('div#messages');
    evtLoop:
    for (var i = 0, j = 0; i < events.length; i++) {
        var evt = events[i];
        
        while (j < shownMsgContainer.children().length) {
            var child = shownMsgContainer.children().eq(j);
            var timestamp = child.find('.msg-timestamp').text();
            var from = child.find('.msg-from').text();

            j++;
            if (evt.timestamp < timestamp) {
                var entry = buildEntry(evt);
                $(entry).insertBefore(child);
                continue evtLoop;
            }
            else {
                if (evt.timestamp == timestamp)
                    continue evtLoop;
            }
        }
        var entry = buildEntry(evt);
        shownMsgContainer.append(entry);
        needsScrolling = true;
        j++;
    }
    if (needsScrolling)
        $('#messages').prop('scrollTop', 1000000);
    if (events.length > 0 && events[events.length - 1].from != 'self')
        $('#notification').css({visibility: 'hidden'});
}

function startDialog() {
    if (!isDialogStarted) {
        isDialogStarted = true;
        if (waitingInterval != null) {
            clearInterval(waitingInterval);
            waitingInterval = null;
        }
    }
    $('#message-waiting').hide();
    $('#chatbox-wrapper').show();
    if (isFirstUser) {
        $('#recommender').show();
        $('#first-user-left-panel').show();
        $('#console').show();
    }
    else {
        $('#first-user-left-panel').hide();
        $('#recommended').show();
    }
    if (dialog == null)
        $('#new-msg').focus();
}

function stopDialog() {
    $('#notification').css({visibility: 'hidden'});
    $('#controls').hide();
    $('#chatroom-infobox').show();
    $('#first-user-left-panel input').attr('disabled', true);
    $('#notification').hide();
    $('#message-try-later').hide();
    $('#chatbox').removeClass('shadowed');
    var mainBoxHeight = $('#main-box').css('height');
    $('#main-box').css('height', 'calc(' + mainBoxHeight + ' - ' + mainBoxMargin + ')');
    $('#messages').prop('scrollTop', 1000000);
    isDialogOver = true;
}

function pollServer() {
    pollXhr = $.ajax({
        url: "chatroom",
        data: {
            clientTabId: clientTabId,
            id: chatroomId,
            timestamp: chatroomTimestamp
        },
        timeout: timeoutInMs,
        success: function(result) {
            var data = JSON.parse(result);
            console.dir(data);
            // In the case that the polling request is done just after that the chatroom has been
            // deallocated on the server, the result might be empty so just ignore it.
            if (jQuery.isEmptyObject(data)) 
                return;

            // if ('chosenTopic' in data)
            //     $('.topic').text(data['chosenTopic']);

            var needsPolling = true;
            if ('msg' in data && data.msg == "poll expired") {
                // The poll request has expired and has not produced anything.
                // Let's poll again.
                if (!isLeaving)
                    pollServer();
                return;
            }
            else if (data.users.length > 1) {
                if (!isDialogStarted)
                    startDialog();
            }
            else {
                console.log('data.closed='+data.closed+ ' stopChatConfirmed='+stopChatConfirmed);
                if (data.closed) {
                    isLeaving = true;
                    $('#message-waiting').hide();
                    $('#notification').css({visibility: 'hidden'});
                    $('#controls').hide();
                    $('#chatbox').removeClass('shadowed');
                    var mainBoxHeight = $('#main-box').css('height');
                    $('#main-box').css('height', 'calc(' + mainBoxHeight + ' - ' + mainBoxMargin + ')');
                    if (!stopChatConfirmed) {
                        $('#stop-chat').hide();
                        $('#message-chat-over').show();
                        $('#chatroom-infobox').show();
                        $('#first-user-left-panel input').attr('disabled', true);
                        //if ($('#table-movie-selector').is(':visible'))
                        //    $('#console').hide();
                        $('#notification').hide();
                        $('#messages').prop('scrollTop', 1000000);
                    }
                    // Show the chatbox in the case where the page is reloaded
                    // when the conversation is over.
                    $('#chatbox-wrapper').show();
                    // Leave the chatroom immediately.
                    $.ajax({
                        url: "leave",
                        data: {
                            clientTabId: clientTabId,
                            chatroom: chatroomId,
                            call: 1
                        },
                        success: function(data) {
                            needsPolling = false;
                            if (pollXhr != null) {
                                pollXhr.abort();
                                pollXhr = null;
                            }
                        }
                    });
                }
            }
            
            updateModel(data);
            updateView();
        
            if (!isLeaving)
                pollServer();
        },
        error: function(xhr, status, msg) {
            console.log('error xhr='+xhr+' status='+status+' msg='+msg + ' isLeaving='+isLeaving);
            if (status == 'timeout' || status == 'error')
                if (!isLeaving)
                    pollServer();
        }
    });
}

function sendMsg() {
    var msg = $('#new-msg').val().trim();
    // Ignore empty message.
    if (msg == '')
        return;
    
    if (events.length > 0 && events[events.length - 1].from == 'self' && events[events.length - 1].type == 'msg') {
        showSimpleDialog('注意', '相手の返信を待ってからメッセージを送信してください。');
        return;
    }

    $('#new-msg').val('');
    if (pollXhr != null) {
        pollXhr.abort();
        pollXhr = null;
    }
    $('#notification').css({visibility: 'visible'});
    $.ajax({
        url: "post",
        data: {
            clientTabId: clientTabId,
            chatroom: chatroomId,
            message: msg
        },
        type: 'POST',
        success: function(result) {
            var data = JSON.parse(result);
            console.dir(data);
            updateModel(data);
            updateView();
            $('#messages').prop('scrollTop', 1000000);
            $('#send').attr('disabled', false);
            if (dialog == null)
                $('#new-msg').attr('disabled', false).focus();
            if (!isTooLongDialogShown && getMessageCountFor('self') >= MSG_COUNT_HIGH && getMessageCountFor('other') >= MSG_COUNT_HIGH) {
                showSimpleDialog('注意', '対話が十分な長さになりました。数回のやり取りで自然な形で対話を終了させて下さい。');
                isTooLongDialogShown = true;
            }
            pollServer();
        }
    });
};

function stopChat() {
    if (!confirmBeforeStopChat) {
        $('#stop-chat').hide();
        $('#message-chat-over').hide();
        if (needsLeavingChatroom) {
            isLeaving = true;
            $.ajax({
                url: "leave",
                data: {
                    clientTabId: clientTabId,
                    chatroom: chatroomId,
                    call: 3
                },
                success: function(result) {
                    if (pollXhr != null) {
                        pollXhr.abort();
                        pollXhr = null;
                    }
                    stopDialog();
                }
            });
            return;
        }
        else {
            if (isDialogStarted) {
                stopDialog();
                return;
            }
        }
    }
    if (isDialogStarted &&
        (!isTooShortDialogShown && (getMessageCountFor('self') < MSG_COUNT_LOW || getMessageCountFor('other') < MSG_COUNT_LOW))) {
        showSimpleDialog('注意', 'チャットがまだ十分な長さに達していません。チャットをまだ続けて下さい。');
        isTooShortDialogShown = true;
        return;
    }

    dialog = $('#dialog-confirm');
    dialog.attr('title', '注意');
    dialog.text('チャットを終了しますか？');
    dialog.dialog({
        resizable: false,
        height: 'auto',
        width: 400,
        modal: true,
        buttons: {
            'はい': function() {
                isLeaving = true;
                $('#message-waiting').hide();
                stopChatConfirmed = true;
                $('#send').attr('disabled', true);
                $('#new-msg').attr('disabled', true);
                $('#send').hide();
                $('#stop-chat').hide();
                $('#message-chat-over').hide();
                dialog.dialog('close');
                dialog = null;
                $.ajax({
                    url: "leave",
                    data: {
                        clientTabId: clientTabId,
                        chatroom: chatroomId,
                        call: 4
                    },
                    success: function(result) {
                        if (pollXhr != null) {
                            pollXhr.abort();
                            pollXhr = null;
                        }
                        $('#controls').hide();
                        if (isDialogStarted) {
                            $('#chatroom-infobox').show();
                            $('#first-user-left-panel input').attr('disabled', true);
                            $('#notification').hide();
                            if ($('#console').is(':visible'))
                                $('#console').hide();
                            $('#chatbox').removeClass('shadowed');
                            var mainBoxHeight = $('#main-box').css('height');
                            $('#main-box').css('height', 'calc(' + mainBoxHeight + ' - ' + mainBoxMargin + ')');
                            $('#messages').prop('scrollTop', 1000000);
                        }
                        else
                            $('#message-thanks').show("slow");
                    }
                });
            },
            'いいえ': function() {
                dialog.dialog('close');
                dialog = null;
                $('#new-msg').focus();
            }
        }
    });
}

function updateWaitingTimer() {
    var now = Date.now();
    var delay = now - waitStartTime;
    if (delay > WAITING_FOR_PARTNER_DELAY) {
        isLeaving = true;
        if (waitingInterval != null) {
            clearInterval(waitingInterval);
            waitingInterval = null;
        }
        $('#message-waiting').hide();
        $('#message-try-later').show("slow");
        $('#stop-chat').hide();
        needsPolling = false;
        if (pollXhr != null) {
            pollXhr.abort();
            pollXhr = null;
        }
        confirmBeforeStopChat = false;
        // Leave the chatroom immediately.
        $.ajax({
            url: "leave",
            data: {
                clientTabId: clientTabId,
                chatroom: chatroomId,
                call: 2
            },
            success: function(result) {
                needsLeavingChatroom = false;
            }
        });
    }
    else {
        if (stopChatConfirmed)
            $('#message-waiting').hide();
        else {
            var msg = $('#message-waiting p:first-of-type').text();
            var delayInSecs = Math.round((WAITING_FOR_PARTNER_DELAY - delay)/1000); 
            if (msg.indexOf('(') == -1)
                $('#message-waiting p:first-of-type').text(msg + ' (' + delayInSecs + ' s.)');
            else
                $('#message-waiting p:first-of-type').text(msg.replace(/\(.*\)/, '(' + delayInSecs + ' s.)'));
        }
    }
}

window.addEventListener('beforeunload', function (e) {
    e.returnValue = 'リロードしないでください';
});

$(document).ready(function() {
    $('#message-chat-over').hide();

    $('.new-msg-field').on('keypress', function(e) {
        if (e.keyCode == 13 && !e.shiftKey) {
            sendMsg();
            return false;
        }
        return true;
    });

    if (WAITING_FOR_PARTNER_DELAY > 0) {
        $('#chatbox-wrapper').hide();
        $('#message-waiting').show();
        waitStartTime = Date.now();
        waitingInterval = setInterval(updateWaitingTimer, 1000);
    }
    else if (!isFirstUser)
        startDialog();

    pollServer();
});

console.log('default_chat.js loaded.');
