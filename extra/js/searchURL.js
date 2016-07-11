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
        } else if (url.startsWith("module=")) {
            var moduleName = url.substring(7);
            if (myModules.indexOf(moduleName) !== -1) return moduleName + ".html";
            return false;
        } else if (url.startsWith("symbol=")) {
            var symbolName = url.substring(7);
            if (mySymbols.indexOf(symbolName) !== -1) {
                var moduleName = mySymbolsMod[symbolName];
                return moduleName + ".html" + "#" + symbolName;
            }
            return false;
        } else {
            return false;
        }
        return url;
    }

    function loadFrames() {
        if (targetPage != "" && targetPage != "undefined")
             top.moduleFrame.location = top.targetPage;
    }
