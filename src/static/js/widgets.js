
var source = new EventSource("/subscribe");

source.addEventListener('message', function(event) {
    console.log(event.data);
    if (event.data.indexOf("$") == 0) {
        window.subscription_id = event.data;
        init();
    } else {
        message = JSON.parse(event.data);
        $('#' + message.target).html(message.html);
    }
});

function init(){
    // For each Element with class = widget...
    $(".widget").each(function(index) {
        if (this.hasAttributes()) {
               var msg = {};
               if (this.id == 'undefined') {
                console.log('widget instance has no id attribute');
                return
               }
               msg["subscription_id"] = window.subscription_id;
               msg["target"] = this.id;
               msg["action"] = "init";
               // Run through the item's attributes
               var attrs = this.attributes;
               for(var i = attrs.length - 1; i >= 0; i--) {
                // If the attribute name starts with "data-"
                 if (attrs[i].name.indexOf("data-") == 0) {
                    // Add the attribute to the msg dict
                    msg[attrs[i].name] = attrs[i].value;
                 }
               }
               sendMsg(msg);
             }
    })
}

function sendMsg(msg){
    $.post("/widget", JSON.stringify(msg), function(data, status){
        console.log("Data: " + data + "\nStatus: " + status);
      });
}