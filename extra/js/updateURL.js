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

function updateURL(moduleName) {

    var mainWindow;
    try {
        mainWindow = getMainWindow();
    }
    catch (error) {
        return;
    }
    if (mainWindow === null) {
        alert("Should be in a frame!");
        return;
    }

    var urlReplacement = mainWindow.prefix.concat(moduleName, ".html");
    var myHash = window.location.hash, symName,
        docTitle = window.document.title;
    if (myHash) {
        symName = myHash.slice(1);
        urlReplacement = urlReplacement.concat("&sym=", symName);
        docTitle = window.document.title.concat(" (symbol: ", symName, ")");
    }

    // update the URL
    var stateObj = {myLoc:moduleName};
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);

    // update the main window title with that of the inner document
    mainWindow.root.document.title = docTitle;

}

function updateURLhash(moduleName) {

    var mainWindow;
    try {
        mainWindow = getMainWindow();
    }
    catch (error) {
        return;
    }
    if (mainWindow === null) {
        alert("Should be in a frame!");
        return;
    }

    var mainDocBaseName = mainWindow.winDocURLbaseName;
    if (!mainDocBaseName.startsWith("?" + moduleName + ".html") &&
        !mainDocBaseName.startsWith("index.html?" + moduleName + ".html"))
        alert("Error(updateURLhash): mainDocBaseName=`"+mainDocBaseName+"'");

    var myHash = window.location.hash;
    if (!myHash) {
        if (window.location.href.endsWith('#')) {
            // prevent back-to-top hash from messing up using replaceState
            return;
        }
        alert("Error: window.location=`"+window.location+"'");
    }
    var symName = myHash.slice(1);
    var urlReplacement = mainWindow.prefix.concat(moduleName, ".html", "&sym=", symName);

    // update the URL
    var stateObj = {myLoc:moduleName};
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);

    // update the main window title
    mainWindow.root.document.title = window.document.title.concat(" (symbol: ", symName, ")");

}
