    var myModules = JSON.parse(modules),
        mySymbolsMod = JSON.parse(symbols),
        mySymbols = Object.keys(mySymbolsMod),
        myModPrivs = JSON.parse(modules_priv_symbols);

    targetPage = "" + window.location.search;

    // discard the `?' char at 0
    if (targetPage != "" && targetPage != "undefined")
        targetPage = targetPage.substring(1);

    if (targetPage.indexOf(":") != -1)
        targetPage = "undefined";
    else if (targetPage != "") {
        url = validURL(targetPage)
        if (!url) targetPage = "undefined";
        else {
            targetPage = url
        }
    }

    function validURL(url) {
        try {
            url = decodeURIComponent(url);
        }
        catch (error) {
            return false;
        }

        var moduleName;
        var pos = url.indexOf(".html");
        if (pos != -1 && pos == url.length - 5) {
            var allowNumber = false;
            var allowSep = false;
            var seenDot = false;
            for (var i = 0; i < url.length - 5; i++) {
                var ch = url.charAt(i);
                if ('a' <= ch && ch <= 'z' ||
                        'A' <= ch && ch <= 'Z' ||
                        ch == '$' ||
                        ch == '_' ||
                        ch.charCodeAt(0) > 127) {
                    allowNumber = true;
                    allowSep = true;
                } else if ('0' <= ch && ch <= '9'
                        || ch == '-') {
                    if (!allowNumber)
                         return false;
                } else if (ch == '/' || ch == '.') {
                    if (!allowSep)
                        return false;
                    allowNumber = false;
                    allowSep = false;
                    if (ch == '.')
                         seenDot = true;
                    if (ch == '/' && seenDot)
                         return false;
                } else {
                    return false;
                }
            }
            moduleName = url.slice(0, -5);
            if (myModules.indexOf(moduleName) === -1)
                return false;
        } else if (pos != -1) {
            var searchObj = searchUrlToObj(url);
            var keyWords = searchObj.keyWords;
            var keysCheck = ["mod", "sym"];
            var is_ok = (keyWords.length == keysCheck.length) && keyWords.every(function(element, index) {
                return element === keysCheck[index];
            });
            if (!is_ok || searchObj.mod.indexOf(".html")==-1) return false;

            var found = false;
            moduleName = searchObj.mod.slice(0, -5);
            // the module must be in the DB
            if (myModules.indexOf(moduleName) !== -1) {

                var symbolName = searchObj.sym;
                if (
                    // the symbol must be either in the publics of the module...
                    (mySymbols.indexOf(symbolName) !== -1 && mySymbolsMod[symbolName].indexOf(moduleName) !== -1) ||
                    // ...or in the referenced private symbols DB
                    (myModPrivs[moduleName].indexOf(symbolName) !== -1)
                   )
                    found = moduleName + ".html" + "#" + symbolName;

            }
            return found;
        } else {
            var searchObj = searchUrlToObj(url);
            var keyWords = searchObj.keyWords;
            var keysCheck = ["whatis", "whois"];
            var is_ok = (keyWords.length == keysCheck.length) && keyWords.every(function(element, index) {
                return element === keysCheck[index]; 
            });
            if (!is_ok) return false;
            if (searchObj.whatis === "module") {
                moduleName = searchObj.whois;
                if (myModules.indexOf(moduleName) !== -1)
                    return moduleName + ".html";
            } else if (searchObj.whatis === "symbol") {
                var symbolName = searchObj.whois;
                if (mySymbols.indexOf(symbolName) !== -1) {
                    var moduleList = mySymbolsMod[symbolName];
                    if (moduleList.length === 1) {
                        moduleName = moduleList[0];
                        return moduleName + ".html" + "#" + symbolName;
                    } else {
                        return "disambiguation.html#" + symbolName;
                    }
                }
            }
            return false;
        }
        return url;
    }

    function searchUrlToObj(url) {
        var searchItems = url.split('&');
        var searchObj = {"keyWords":[]};
        var i, item, key, val;
        for (i in searchItems) {
            item = searchItems[i].split("=");
            if (item == searchItems[i]) {
                key = "mod"; val = item[0];
            } else {
                key = item[0]; val = item[1];
            }
            n = searchObj.keyWords.push(key);
            searchObj[key] = val;
        }
        searchObj.keyWords.sort()
        return searchObj;
    }

    function loadFrames() {
        if (targetPage == "") {
            // do nothing, stay on the landing page
        } else if (targetPage == "undefined") {
            // state that the target page hasn't been found
            top.moduleFrame.document.body.innerHTML = "Not found!";
        } else {
            // load the target page in the proper frame
            top.moduleFrame.location = top.targetPage;
        }
    }
