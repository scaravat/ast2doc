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
        alert("Error(getMainWindow): winDocURLbaseName=`"+winDocURLbaseName+"'");
    mainWindow["prefix"] = prefix;

    // frames in the main window
    mainWindow["packageFrameWindow"] = root.document.getElementById("packageFrame").contentWindow;

    return mainWindow;
}

function updateURL(moduleName) {

    var mainWindow = getMainWindow();
    if (mainWindow === null) {
        alert("Should be in a frame!");
        return;
    }

    var urlReplacement = mainWindow.prefix.concat(moduleName, ".html");
    var myHash = window.location.hash;
    if (myHash)
        urlReplacement = urlReplacement.concat("&sym=", myHash.slice(1));

    // update the URL
    var stateObj = {myLoc:moduleName};
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);

}

function updateURLhash(moduleName) {

    var mainWindow = getMainWindow();
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
    var urlReplacement = mainWindow.prefix.concat(moduleName, ".html", "&sym=", myHash.slice(1));

    var stateObj = {myLoc:moduleName};
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);

}
