// https://facelessuser.github.io/pymdown-extensions/extensions/tabbed/#linked-tabs

document$.subscribe(function() {
    var tabs = document.querySelectorAll(".tabbed-set > input");
    if(!location.hash.substring(1)) {
        if(navigator.userAgent.match(/Android|webOS|iPhone|iPad|iPod|BlackBerry|Windows Phone/)) {
            // click on the second input (phone)
            tabs[1].click();
        } else {
            // click on the first input (computer)
            tabs[0].click();
        }
    }
});
