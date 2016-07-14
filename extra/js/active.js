
function setActive(baseName) {
    var id = 'button_' + baseName;
    var myIframe = window.frameElement;          if (myIframe === null) alert("I should be embedded in an iframe");
    var parentDocument = myIframe.ownerDocument;
    var lnk = parentDocument.getElementById(id); if (lnk === null || checkElement(lnk, 'A') !== 0) alert("Error 1");

    if (lnk.hasAttribute("class")) {
        if (lnk.getAttribute("class") !== "active") alert("Error 2");
        // do nothing: I'm already the active
        return;
    }

    // change the buttons' classes without loading the page
    processButtons(baseName, lnk);

 }

function processButtons(baseName, lnk) {
    var id = 'button_' + baseName;
    var parentLI = lnk.parentElement;       if (parentLI === null || checkElement(parentLI, 'LI') !== 0) {return "Error -3";}
    var grandpaUL = parentLI.parentElement; if (checkElement(grandpaUL, 'UL') !== 0) {return "Error -4";}
    var nItems = grandpaUL.childElementCount;
    //  ..last item is the "Quick search" dropdown that is never "active", so upper limit: `i < nItems-1'!
    for (i = 0; i < nItems-1; i++) {
        var nextLI = grandpaUL.children[i]; if (checkElement(nextLI, 'LI') !== 0 || nextLI.childElementCount !== 1) {return "Error -5";}
        var nextA = nextLI.children[0];     if (checkElement(nextA, 'A') !== 0) {return "Error -6";}
        if (nextA.id === id) {
            // make it active
            if (lnk.hasAttribute("class")) {return "Error -7";}
            lnk.setAttribute("class", "active");
        } else {
            if (nextA.hasAttribute("class")) {
                nextA.removeAttribute("class");
            }
        }
    }
}

function checkElement(node, name) {
    if (node.nodeType !== 1) {return 1;}
    if (node.nodeName !== name) {return 2;}
    return 0;
}
