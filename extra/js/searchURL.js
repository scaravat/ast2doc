    var myModules = JSON.parse(modules);
    var mySymbolsMod = JSON.parse(symbols);
    var mySymbols = Object.keys(mySymbolsMod);

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
        } else {
            var moduleName, symbolName;
            var searchObj = searchUrlToObj(url);
            var keyWords = searchObj.keyWords;
            var keysCheck = ["whatis", "whois"];
            var is_ok = (keyWords.length == keysCheck.length) && keyWords.every(function(element, index) {
                return element === keysCheck[index]; 
            });
            if (!is_ok) return false;
            if (searchObj.whatis === "module") {
                moduleName = searchObj.whois;
                if (myModules.indexOf(moduleName) !== -1) {
                    return moduleName + ".html";
                }
            } else if (searchObj.whatis === "symbol") {
                symbolName = searchObj.whois;
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
            key = item[0]; val = item[1];
            n = searchObj.keyWords.push(key);
            searchObj[key] = val;
        }
        searchObj.keyWords.sort()
        return searchObj;
    }

    function loadFrames() {
        if (targetPage != "" && targetPage != "undefined")
             top.moduleFrame.location = top.targetPage;
    }
