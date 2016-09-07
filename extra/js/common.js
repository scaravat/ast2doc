function getMainWindow() {

    // root...
    var root = window.parent;
    if (root === null)
        return;
    var mainWindow = {"root":window.parent};

    // prefix...
    var prefix,
        winLocSearch = root.location.search,
        winDocumentURL = root.document.URL,
        winDocURLbaseName = winDocumentURL.split('/').pop();
    mainWindow["winDocURLbaseName"] = winDocURLbaseName;
    if (winDocURLbaseName.length === 0 || winDocURLbaseName === winLocSearch)
        prefix = "?";
    else if (winDocURLbaseName === "index.html"+winLocSearch)
        prefix = "index.html?";
    else
        throw "Error(getMainWindow): winDocURLbaseName=`"+winDocURLbaseName+"'";
    mainWindow["prefix"] = prefix;

    // frames in the main window
    mainWindow["packageFrameWindow"] = root.document.getElementById("packageFrame").contentWindow;

    return mainWindow;
}
