const wsUri = (window.location.protocol==='https:'&&'wss://'||'ws://')+window.location.host+'/ws';
document.$WEB_SOCKET = new WebSocket(wsUri);

document.$WEB_SOCKET.addEventListener('open', () => {
     console.log('Connected');
     init();
 });

 document.$WEB_SOCKET.addEventListener('close', () => {
      console.log('Disconnected');
  });

 document.$WEB_SOCKET.addEventListener('message', (event) => {
    console.log(event);
    const msg_data = JSON.parse(event.data);
    if (msg_data.action == 'refresh') {
        updateHTML(msg_data.target, msg_data.data);
    }
});

function updateHTML(target, html){
    // const NEW_DATA = target;
    const rangeHTML = document.createRange().createContextualFragment(html);
    document.querySelector(target).innerHTML = '';
    document.querySelector(target).appendChild(rangeHTML);
}

function init(){
    // For each Element with class = widget...
    document.querySelectorAll(".widget").forEach(function(item) {

        if (item.hasAttributes()) {
               var msg = {};
               if (item.id == 'undefined') {
                console.log('widget instance has no id attribute');
                return
               }
               msg["target"] = item.id
               msg["action"] = "init"
               // Run through the item's attributes
               var attrs = item.attributes;
               for(var i = attrs.length - 1; i >= 0; i--) {
                // If the attribute name starts with "data-"
                 if (attrs[i].name.indexOf("data-") == 0) {
                    // Add the attribute to the msg dict
                    msg[attrs[i].name] = attrs[i].value
                 }
               }
               sendMsg(msg);
             }
    })
}

function sendMsg(msg){
    console.log("Sending message:");
    console.log(msg);
    document.$WEB_SOCKET.send(JSON.stringify(msg));
    console.log("Message sent.")
}

/*
Switch to approach that client sends all widget data to server, and then server handles EVERYTHING.
So, client doesn't even periodically refresh. If there's a refresh timer needed, that info is part of the
initial setup params sent to the server, and the sever sends the updates.

Example widget_instance setup message:
{
target = element id
data-widget = widget name
data-* = widget parameters, e.g.
    data-refresh-timer
    data-sonos-name
}
^ could strip off data- from the param names?

BUT! we need need a way to detect if the server has gone down. So still need some sort of regular heartbeat
from the client.

ALSO! would be nice to have something that attempted to re-establish the web socket connection if that goes down.
*/
/*
// TODO: TURN THIS INTO HEART BEAT
function requestRefresh() {
    if (document.$WEB_SOCKET === null) {
        onNotConnected();
        return;
    }
    timeout_counter++;
    console.log(timeout_counter)
    if (timeout_counter > 4) {
        console.log("Server not responding!");
        updateHTML("#sonos-1", "Server not responding!");
    }

    const toSend = {
        "widget": "sonos",
        "action": "refresh",
        "widget_params":{
            "sonos_name": "Kitchen"
        }
    };
    document.$WEB_SOCKET.send(JSON.stringify(toSend));
    console.log("Refresh requested.");
}



function onNotConnected(){
    console.log("No connection established!");
}

// TODO: need to setInterval for each widget? No! THIS BECOMES HEART BEAT
var timeout_counter = 0;
setInterval(requestRefresh, 3000);

*/