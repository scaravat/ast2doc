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
        var pos = symName.indexOf(":");
        if (pos !== -1)
            // avoid encoding a function argument name
            symName = symName.slice(0, pos);
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
    if (myHash) {

        var symName = myHash.slice(1);
        var pos = symName.indexOf(":");
        if (pos !== -1)
            // avoid encoding a function argument name
            symName = symName.slice(0, pos);
        var urlReplacement = mainWindow.prefix.concat(moduleName, ".html", "&sym=", symName);

    } else {
        if (window.location.href.endsWith('#')) {
            // prevent back-to-top hash from messing up using replaceState
            return;
        }
        if (myHash.length === 0) {
            // going back in history we could meet a state without hashes...
            //  ... so: cleanup the "&sym" stuff!
            var urlReplacement = mainWindow.prefix.concat(moduleName, ".html");
        } else {
            alert("Error: window.location=`"+window.location+"'");
        }
    }

    // update the URL
    var stateObj = {myLoc:moduleName};
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);

    // update the main window title
    mainWindow.root.document.title = window.document.title.concat(" (symbol: ", symName, ")");

}
