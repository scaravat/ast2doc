function resetModuleFrameWithPkgDescr(pkgDir, pkgName) {

    var pkgOverviewURI = pkgName + "-overview.html";
    top.moduleFrame.window.location.replace(pkgOverviewURI);

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

    // cleanup the URL
    var stateObj = {myLoc:pkgName},
        urlReplacement = "index.html";
    mainWindow.root.history.replaceState(stateObj, "", urlReplacement);
        
    // update the main window title with that of the inner document
    mainWindow.root.document.title = "Overview of package "+pkgDir;
}
