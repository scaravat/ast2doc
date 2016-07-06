 function getActive() {
    var activePage = document.getElementById('OverviewFrame').src;
    var fileName = activePage.split("/").pop();
    if ( !(fileName.endsWith(".html")) ) {return "Error 1";}
    var baseName = fileName.slice(0, -5);
    setActive(baseName);
 }

 function setActive(baseName) {
    var id = 'button_' + baseName
    var lnk = document.getElementById(id);

    if (checkElement(lnk, 'A') !== 0) {
        return "Error -1: Node isn't 'A'!";
    }

    if (lnk.hasAttribute("class")) {
        // do nothing
        if (lnk.getAttribute("class") !== "active") {
            return "Error -2: class: `" + lnk.getAttribute("class") + "'??";
        }
    } else {

        // process all the buttons one by one
        var parentLI = lnk.parentElement;       if (checkElement(parentLI, 'LI') !== 0) {return "Error -3";}
        var grandpaUL = parentLI.parentElement; if (checkElement(grandpaUL, 'UL') !== 0) {return "Error -4";}
        var nItems = grandpaUL.childElementCount;
        for (i = 0; i < nItems; i++) {
            var nextLI = grandpaUL.children[i]; if (checkElement(nextLI, 'LI') !== 0 || nextLI.childElementCount !== 1) {return "Error -5";}
            var nextA = nextLI.children[0];     if (checkElement(nextA, 'A') !== 0) {return "Error -6";}
            if (nextA.id === id) {
                // make it active
                if (lnk.hasAttribute("class")) {return "Error -7";}
                lnk.setAttribute("class", "active");
                // follow link
                document.getElementById('OverviewFrame').src = baseName + ".html";
            } else {
                if (nextA.hasAttribute("class")) {
                    nextA.removeAttribute("class");
                }
            }
        }

    }
    return;
 }

 function checkElement(node, name) {
    if (node.nodeType !== 1) {return 1;}
    if (node.nodeName !== name) {return 2;}
    return 0;
 }
