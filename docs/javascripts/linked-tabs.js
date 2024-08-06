// https://facelessuser.github.io/pymdown-extensions/extensions/tabbed/#linked-tabs

document$.subscribe(function() {
    var tabs = document.querySelectorAll(".tabbed-set > input");
    var changing = false;
    for (var tab of tabs) {
        tab.addEventListener("change", evt => {
            if(changing || !evt.target.checked) return;
            changing = true;
            console.log(evt.target, "changed");

            var current = evt.target.labels[0];
            var pos = current.getBoundingClientRect().top;
            var labelContent = current.textContent;
            var labels = document.querySelectorAll(".tabbed-alternate > .tabbed-labels > label");
            for (var label of labels) {
                if (evt.target != label.control && label.textContent === labelContent)
                    label.firstChild.click();
            }

            // Preserve scroll position
            var delta = (current.getBoundingClientRect().top) - pos;
            window.scrollBy(0, delta);

            changing = false;
        });
    }

    var id = location.hash.substring(1);
    var item = id ? document.getElementById(id) : null;
    if(item && [].includes.apply(document.querySelectorAll(".tabbed-set > .tabbed-labels > label"), item)) {
        var openTabs = document.querySelectorAll(".tabbed-set > input:checked");
        for(var tab of openTabs) {
            tab.labels[0].click();
        }
    } else if(tabs.length && (tabs[0].id == "ordinateur" || tabs[0].id == "telephone")) {
        if(navigator.userAgent.match(/Android|webOS|iPhone|iPad|iPod|BlackBerry|Windows Phone/)) {
            // click on the second input (phone)
            tabs[1].click();
        } else {
            // click on the first input (computer)
            tabs[0].click();
        }
    }
});
