function highlightArgument (symbolName, anchorArgName) {

    // eventually clear other highlighted items
    currentlyHighlighted = window.document.getElementsByClassName("highlighted_argument");
    for (var i = 0; i < currentlyHighlighted.length; i++) {
        var node = currentlyHighlighted[i];
        var nodeIsSpan = (node.nodeType === 1 && node.nodeName === "SPAN");
        if (nodeIsSpan)
            node.removeAttribute("class");
        else
            alert(node);
    }

    // now highlight the element we're interested in
    elementToHighlight = window.document.getElementById(symbolName.concat(":", anchorArgName));
    elementToHighlight.setAttribute("class", "highlighted_argument");

}
