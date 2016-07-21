#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from makeHTML import newTag
from render import filename, printout, separator, back_to_top_char

#=============================================================================
def print_allModules(prefix, modules_list, modules_description, pkgname=None):

    if pkgname:
        title = " ".join([pkgname, "package"])
        pre = ""
        pkg = newTag('span', content=pkgname, attributes={"class":'pkgname'})
        post = " modules:"
        heading_content = [pre, pkg, post]
    else:
        title = "All Modules:"
        heading_content = title

    heading = newTag('h2', content=heading_content, newlines=False)

    mod_items = []
    for module in sorted(modules_list):
        link = newTag('a', content=module, attributes={"href":module+".html", "target":'moduleFrame', "title":modules_description[module]})
        mod_items.append(newTag('li', content=link))
    mod_list = newTag('ul', content=mod_items, attributes={"class":'nobullet'})
    body = newTag('body', content=[heading, mod_list])

    fileBaseName = pkgname.replace('/','__').upper()+"-frame" if pkgname else "allmodules-frame"
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html'

#=============================================================================
def print_packageFrame(prefix, modules_lists, modules_description):
    packages = [item for item in modules_lists.keys() if not item in ('__ALL__', '__API__')]

    files = []
    for pkg in sorted(packages):
        pkgname = 'ROOT' if pkg=='.' else pkg
        title = "Modules for package " + pkgname
        heading = newTag('h2', content=title)
        my_modules = modules_lists[pkg]
        my_file = print_allModules(prefix, my_modules, modules_description, pkgname=pkgname)
        files.append(my_file)
    return files

#=============================================================================
def print_packageListFrame(prefix, allModulesFile, src_tree, packages):
    title = "Overview of CP2K API"
    heading = newTag('h2', content=title)

    link = newTag('a', content="All Modules", attributes={"href":allModulesFile, "target":"packageFrame", "style":'font-style:oblique;'})
    allModLink_div = newTag('div', content=link)

    pkglist = getTree(src_tree, packages)
    rootnode = newTag('a', content="[root]", attributes={"href":"ROOT-frame.html", "target":"packageFrame", "title":packages["."]['description'], "style":'font-style:oblique;'})
    fakelist = newTag('ul', content=newTag('li', content=[rootnode, pkglist]), attributes={"class":"nobullet"})
    list_heading = newTag('h4', content="Packages:", attributes={"title":"Packages"})
    listContainer_div = newTag('div', content=[list_heading, fakelist])

    body = newTag('body', content=[heading, allModLink_div, listContainer_div])

    fileBaseName = "packages-frame"
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html'

#=============================================================================
def getTree(tree, packages, rootnode=None):
    branches = []
    for child in sorted(tree.GetChildren(rootnode)):
        pkgname = child
        link = newTag('a', content=pkgname, attributes={"href":pkgname.replace('/','__').upper()+"-frame.html", "target":"packageFrame", "title":packages[child]['description']})
        list_item = newTag('li', content=link)
        childpkglist = getTree(tree, packages, rootnode=child)
        if childpkglist:
            list_item.addPiece(childpkglist)
        branches.append(list_item)

    if branches:
        pkglist = newTag('ul', content=branches, attributes={"class":"nobullet_noindent"})
        return pkglist

#=============================================================================
def get_banner(indices, prefix):

    buttons = []
    for i, basename in enumerate(indices.l2sort):
        my_title = getattr(indices, basename)
        button_name = indices.brief[i]
        button_id = 'button_' + basename
        target_href = basename + ".html"
        link = newTag('a', content=button_name, id=button_id, attributes={"href":target_href, "target":"OverviewFrame", "title":my_title})
        buttons.append( newTag('li', content=link) )

    # last two buttons are swapped since they're right-flushed!
    #  .. about
    target_href, my_title = print_about_page(prefix)
    basename = target_href.rsplit('.',1)[0]
    button_id = 'button_' + basename
    link = newTag('a', content="About", id=button_id, attributes={"href":target_href, "target":"OverviewFrame", "title":my_title})
    buttons.append( newTag('li', content=link) )
    #  .. quick search
    link = newTag('a', content="Quick search", attributes={"href":"javascript:showhide('qsearch_dropdown')", "class":"dropbtn"})
    form_items = [
        newTag('input', attributes={"type":"text", "name":"whois", "placeholder":"e.g.: dbcsr_filter", "class":"qsearch_text"}), newTag('br'),
        newTag('input', attributes={"type":"radio", "name":"whatis", "value":"symbol", "checked":None}), "symbol", newTag('br'),
        newTag('input', attributes={"type":"radio", "name":"whatis", "value":"module"}), "module", #newTag('br'),
        newTag('input', attributes={"type":"submit", "value":"GO!", "style":"float: right;"})
    ]
    form = newTag('form', content=form_items, attributes={"action":"index.html", "method":'get', "target":"_top"}, newlines=False)
    dropdown_content = newTag('div', content=form, id="qsearch_dropdown", attributes={"class":"dropdown-content"}, newlines=False)
    buttons.append( newTag('li', content=[link, dropdown_content], attributes={"class":'dropdown'}) )

    buttons_list = newTag('ul', content=buttons, attributes={"class":'navlist'})

    CP2kAPIlogo = newTag('img', attributes={"src":'cp2k_apidoc_logo.svg', "alt":'Logo', "class":'logo'})
    header = newTag('h1', content=["CP2K API-Documentation", CP2kAPIlogo], newlines=False)
    banner = newTag('div', content=[header, buttons_list], attributes={"class":'wideautoheightbanner'})
    return banner

#=============================================================================
def print_overview(prefix, src_tree, packages, modules_lists, modules_description, statistics, api, sym_lookup_table):

    my_indices = IofIndices()
    my_indices.Append( 'Tree', *print_logical_tree_index('__ALL__', prefix, src_tree, modules_lists, modules_description, packages, sym_lookup_table) )
    my_indices.Append( 'Index', *print_alphabetic(modules_lists['__ALL__'], modules_description, prefix, 'all') )
    my_indices.Append( 'Mostly used', *print_mostly_used(statistics, modules_description, prefix) )
   #my_indices.Append( 'DBCSR tree', *print_logical_tree_index(api, prefix, src_tree, modules_lists, modules_description, packages) )
    my_indices.Append( 'DBCSR modules', *print_alphabetic(modules_lists['__API__'], modules_description, prefix, 'DBCSR API') )
    initial_index_index = 0

    banner = get_banner(my_indices, prefix)
    noframe = newTag('p', content="Your browser does not support iframes.")
    index_iframe = newTag('iframe', content=noframe, id="OverviewFrame",
        attributes={"src":my_indices.l2sort[initial_index_index]+".html", "name":"OverviewFrame", "class":'wideautoheight'}
    )
    body = newTag('body', content=[banner, index_iframe])

    fileBaseName = "overview-summary"
    printout(body, prefix, title="Overview", output_file=fileBaseName, jscript=["js/active.js", "js/showhide.js"])
    return fileBaseName+'.html'

#=============================================================================
def print_landingPage(prefix, src_tree, packages, modules_lists, modules_description, statistics, api, sym_lookup_table):

    allModulesFile  = print_allModules(prefix, modules_lists['__ALL__'], modules_description)
    pkgModulesFiles = print_packageFrame(prefix, modules_lists, modules_description)
    packageListFile = print_packageListFrame(prefix, allModulesFile, src_tree, packages)
    overviewFile    = print_overview(prefix, src_tree, packages, modules_lists, modules_description, statistics, api, sym_lookup_table)

    title = 'CP2K API Documentation'

    packageListFrame = newTag('frame', attributes={"src":packageListFile, "name":"packageListFrame", "title":"All Packages"})
    packageFrame     = newTag('frame', attributes={"src":allModulesFile, "name":"packageFrame", "title":"All Modules"})
    moduleFrame      = newTag('frame', attributes={"src":overviewFile, "name":"moduleFrame", "title":"Module descriptions"})

    noscript = newTag('noscript', content=newTag('div', content="JavaScript is disabled on your browser."))
    heading  = newTag('h2', content="Frame Alert")
    paragrph = newTag('p',  content="This document is designed to be viewed using the frames feature. If you see this message, you are using a non-frame-capable web client.")
    noframes = newTag('noframes', content=[noscript, heading, paragrph])

    inner_frameset = newTag('frameset', content=[packageListFrame, packageFrame], attributes={
        "rows":"50%,50%", "title":"Left frames", "onload":"top.loadFrames()"})
    outer_frameset = newTag('frameset', content=[inner_frameset, moduleFrame, noframes], attributes={
        "cols":"20%,80%", "title":"Documentation frame", "onload":"top.loadFrames()"})

    printout(outer_frameset, prefix, title=title, output_file="index", jscript=["modules_publics.json", "js/searchURL.js"])

#=============================================================================
import time
def print_about_page(prefix):

    title = 'About CP2K API documentation'
    body_parts = [newTag('h3', content=title, attributes={"class":'index_title'})]

    p = newTag('p', content="Documentation automatically generated via:")
    # fparse
    href = "https://github.com/oschuett/fparse"
    link = newTag('a', content="", attributes={"class":"external_href my_tools", "href":href, "target":'_blank', "rel":'nofollow'})
    fparse = newTag('li', content=["fparse", link])
    # ast2doc
    href = "https://github.com/scaravat/ast2doc"
    link = newTag('a', content="", attributes={"class":"external_href my_tools", "href":href, "target":'_blank', "rel":'nofollow'})
    ast2doc = newTag('li', content=["ast2doc", link])
    l = newTag('ul', content=[fparse, ast2doc])
    body_parts.extend([p, l])

    time_now  = time.strftime("%c")
    time_zone = time.tzname[time.daylight]
    time_info = " ".join(["Last update:", time_now, time_zone]) #Last modified: 2016/04/08 12:11
    body_parts.append(time_info)

    fileBaseName = 'about'
    body = newTag('body', content=body_parts, attributes={"onload":"javascript:setActive('"+fileBaseName+"')"})
    printout(body, prefix, title=title, output_file=fileBaseName, jscript="js/active.js")
    return fileBaseName+'.html', title

#=============================================================================
def get_mostly_used(statistics, modules_description, top_howmany, title_prefix):

    hlevel = 'h4'
    myTop10 = top_howmany
    my_ranking = {'__MODULES__':statistics.pop('__MODULES__')[:myTop10], '__SYMBOLS__':statistics.pop('__SYMBOLS__')[:myTop10]}
    if all( [len(my_ranking[k])==0 for k in '__MODULES__', '__SYMBOLS__'] ):
        return

    # mostly used modules
    k = '__MODULES__'
    span = newTag('span', content=title_prefix, attributes={"class":'pkgname'})
    head = newTag(hlevel, content="modules:", newlines=False)
    rows = [
        newTag('tr', content=newTag('th', content='&nbsp;', attributes={"colspan":"2"})),
        newTag('tr', content=newTag('th', content=head, attributes={"colspan":"2", "style":"float: left;"}))
    ]
    first = True
    for what, nhits in my_ranking[k]:
        mod = what.lower()
        descr = modules_description[mod] if mod in modules_description else "[external module]"
        link = newTag('a', content=mod, attributes={"href":filename(mod), "target":'moduleFrame', "title":descr})
        hits = "hits: " if first else ""
        hits += str(nhits) 
        first = False
        data = [newTag('td', content=content) for content in link, hits]
        rows.append( newTag('tr', content=data, attributes={"class":'alternating'}) )
    m_table = newTag('table', content=rows, attributes={"class":'ranking'})

    # mostly used symbols
    k = '__SYMBOLS__'
    head = newTag(hlevel, content="symbols:")
    rows = [
        newTag('tr', content=newTag('th', content='&nbsp;', attributes={"colspan":"2"})),
        newTag('tr', content=newTag('th', content=head, attributes={"colspan":"2", "style":"float: left;"}))
    ]
    first = True
    for what, nhits in my_ranking[k]:
        mod, sym = what.lower().split(':')
        descr = modules_description[mod] if mod in modules_description else "[external module]"
        mod_link = newTag('a', content=mod, attributes={"href":filename(mod), "target":'moduleFrame', "title":descr})
        sym_link = newTag('a', content=sym, attributes={"href":filename(mod, hashtag=sym), "target":'moduleFrame'})
        links = [mod_link, separator, sym_link]
        hits = "hits: " if first else ""
        hits += str(nhits) 
        first = False
        data = [newTag('td', content=content) for content in links, hits]
        rows.append( newTag('tr', content=data, attributes={"class":'alternating'}) )
    s_table = newTag('table', content=rows, attributes={"class":'ranking'})

    hlevel = 'h3'
    data = [ newTag('td', content=item) for item in newTag(hlevel, content=span), m_table, s_table ]
    outer_row = newTag('tr', content=data, attributes={"class":"mostly_used_table_row"})

    return(outer_row)

#=============================================================================
def print_mostly_used(statistics, modules_description, prefix):

    head0 = newTag('h3', content="Overall statistics:")
    row0 = newTag('tr', content=newTag('th', content=head0, attributes={"colspan":"3", "style":"float: left;"}))
    row = get_mostly_used(statistics, modules_description, top_howmany=20, title_prefix="")
    rows = [row0, row]

    head1 = newTag('h3', content="Per-package statistics:")
    row1 = newTag('tr', content=newTag('th', content=head1, attributes={"colspan":"3", "style":"float: left;"}))
    rows.append(row1)
    for pkg in sorted(statistics.keys()):
        title_prefix="[root]" if pkg=="." else pkg
        row = get_mostly_used(statistics[pkg], modules_description, top_howmany=5, title_prefix=title_prefix)
        if row:
            rows.append(row)

    table = newTag('table', content=rows, attributes={"class":"mostly_used_table"})

    title = "Mostly used modules/symbols statistics"
    heading = newTag('h2', content=title, attributes={"class":'index_title'})
    fileBaseName = 'mostly_used'
    body = newTag('body', content=[heading, table], attributes={"onload":"javascript:setActive('"+fileBaseName+"')"})
    printout(body, prefix, title=title, output_file=fileBaseName, jscript="js/active.js")
    return fileBaseName+'.html', title

#=============================================================================
def get_package_stuff(modules_lists, modules_description, packages, pkg_path='__ROOT__'):
    root = path.normpath(path.commonprefix(packages.keys())) 
    be_root = pkg_path=='__ROOT__'
    node = root if be_root else pkg_path
    rel_path = path.relpath(node, root)
    pkg_name = '[root]' if be_root else pkg_path
    pkg_id = node + '__mlist'
    pkg_files = [f.rsplit(".", 1)[0] for f in packages[node]['files']]
    pkg_modules = [f for f in pkg_files if f in modules_lists[rel_path]]
    mlinks = [newTag('a', content=m, attributes={"href":m+".html", "target":'moduleFrame', "title":modules_description[m]}) for m in sorted(pkg_modules)]
    mitems = [newTag('li', content=l) for l in mlinks]
    mlist = newTag('ul', content=mitems, attributes={"class":'horizontal', "style":'padding:5px;'})
    modules_container = newTag('div', content=mlist, attributes={"id":pkg_id, "class":'togglevis'})
    node_button = newTag('a', content=pkg_name, attributes={"href":"javascript:showhide('"+pkg_id+"')", "title":'[show/hide package modules]'})
    if be_root:
        node_button.addAttribute("style", 'font-style:oblique;')
    description = packages[node]['description']
    return [node_button, ' &#8212; ', description, modules_container]

#=============================================================================
def print_logical_tree_index(api, prefix, src_tree, modules_lists, modules_description, packages, sym_lookup_table=None, fmt='html'):

    if api == '__ALL__':
        title = 'Logical tree of ALL packages'
    else:
        title = 'Logical tree index of DBCSR API symbols'

    if(fmt=='html'):
        heading = newTag('h2', content=title, attributes={"class":'index_title'})

        root_item = newTag('li', content=get_package_stuff(modules_lists, modules_description, packages))

        branches = get_tree(api, src_tree, modules_lists, modules_description, packages, sym_lookup_table)
        assert(branches)
        root_item.addPiece(branches)

        fileBaseName = "tree_index" if api == '__ALL__' else "API_tree_index"
        outer_list = newTag('ul', content=root_item, attributes={"class":'nobullet'})
        body = newTag('body', content=[heading, outer_list], attributes={"onload":"javascript:setActive('"+fileBaseName+"')"})
        printout(body, prefix, title=title, output_file=fileBaseName, jscript=["js/active.js", "js/showhide.js"])

    else:
        assert(False) # Unknown format

    return fileBaseName+".html", title

#=============================================================================
def get_tree(api, tree, modules_lists, modules_description, packages, sym_lookup_table, rootnode=None):

    children = sorted(tree.GetChildren(rootnode))

    # no need to open a new ordered list if there are no children!
    if(not children):
        return

    children_list = newTag('ul', attributes={"class":'nobullet'})
    for child in children:
        relative_path = child.replace(tree.root,'',1)[1:]
        files = packages[child]['files']

        my_modules_map = {}
        for f in files:
            mod_name = f.rsplit(".", 1)[0].upper()
            if api == '__ALL__':
                if mod_name in sym_lookup_table:
                    my_mmap = {}
                    for k, v in sym_lookup_table[mod_name]['symbols_map'].iteritems():
                        ext_module, external_sym_name = v.split(':')
                        if(ext_module == '__HERE__'): # no forwarded symbols here...
                            assert(k == external_sym_name)
                            my_mmap[k] = k
                    if(my_mmap):
                        my_modules_map[mod_name.lower()] = my_mmap

            # use the API forwarded symbols as a list of things to list
            elif mod_name in api['modules_map']:
                my_modules_map[mod_name.lower()] = api['modules_map'][mod_name]

        if(my_modules_map):
            children_item = newTag('li', content=get_package_stuff(modules_lists, modules_description, packages, child))

            # recurse ...
            branches = get_tree(api, tree, modules_lists, modules_description, packages, sym_lookup_table, rootnode=child)
            if branches:
                children_item.addPiece(branches)

            children_list.addPiece(children_item)

    return children_list

#=============================================================================
def print_alphabetic(mod_list, modules_description, prefix, descr, fmt='html'):
    items_list = sorted(mod_list)
    initials = sorted(set(item[0] for item in items_list))
    items_dict = dict((ini, [item for item in items_list if item.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of '+descr+' modules'

    if(fmt=='html'):

        heading = newTag('h2', content=title, attributes={"class":'index_title'})

        # initials
        items = []
        for ini in initials:
            link = newTag('a', content=ini.upper(), attributes={"href":'#'+ini.upper()})
            item = newTag('li', content=link)
            items.append(item)
        ini_list = newTag('ul', content=items, id="initials", attributes={"class":'menu'})

        items = []
        for ini in initials:
            inner_items = []
            for mod in items_dict[ini]:
                link = newTag('a', content=mod, attributes={"href":filename(mod), "target":'moduleFrame', "title":modules_description[mod]})
                inner_item = newTag('li', content=link)
                inner_items.append(inner_item)

            inner_list = newTag('ul', content=inner_items)
            columns = newTag('div', content=inner_list, attributes={"class":'columns'})
            back_link = newTag('a', content=back_to_top_char, attributes={"href":'#initials', "title":'[back to top]'})
            head = newTag('h4', content=[back_link, ini.upper()], id=ini.upper(), newlines=False)
            item = newTag('li', content=[head, columns])
            items.append(item)
        outer_list = newTag('ul', content=items, attributes={"class":'nobullet'})

        fileBaseName = "alphabetic_index_"+'_'.join(descr.split())
        body = newTag('body', content=[heading, ini_list, outer_list], attributes={"onload":"javascript:setActive('"+fileBaseName+"')"})
        printout(body, prefix, title=title, output_file=fileBaseName, jscript="js/active.js")

    else:
        assert(False) # Unknown format

    return fileBaseName+".html", title

#=============================================================================
def print_alphabetic_index_(api, prefix, fmt='html'):
    symbols_list = sorted(api['symbols_map'].keys())
    initials = sorted(set(sym[0] for sym in symbols_list))
    symbols_dict = dict((ini, [sym for sym in symbols_list if sym.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of DBCSR API symbols'

    if(fmt=='html'):

        heading = newTag('h1', content=title, attributes={"class":'index_title'})

        # initials
        items = []
        for ini in initials:
            link = newTag('a', content=ini, attributes={"href":'#'+ini})
            item = newTag('li', content=link)
            items.append(item)
        ini_list = newTag('ul', content=items, id="initials", attributes={"class":'menu'})

        items = []
        for ini in initials:

            inner_items = []
            for sym in symbols_dict[ini]:
                sym_name = sym.lower()
                owner_module, ext_sym_name = api['symbols_map'][sym].lower().split(':')
                href = filename(owner_module, hashtag=ext_sym_name)
                link = newTag('a', content=sym_name, attributes={"href":href})
                inner_item = newTag('li', content=link)
                inner_items.append(inner_item)

            inner_list = newTag('ul', content=inner_items)
            columns = newTag('div', content=inner_list, attributes={"class":'columns'})
            back_link = newTag('a', content=ini, attributes={"href":'#initials'})
            head = newTag('h4', content=back_link, id=ini)
            item = newTag('li', content=[head, columns])
            items.append(item)
        outer_list = newTag('ul', content=items, attributes={"class":'nobullet'})

        body_parts = [heading, ini_list, outer_list]
        body = newTag('body', content=body_parts)

        fn = "alphabetic_index"
        printout(body, prefix, title=title, output_file=fn)

    else:
        assert(False) # Unknown format

    return fn+".html", title

#=============================================================================
def print_disambiguationPage(symbols_db, modules_description, prefix):

    title = "Disambiguation Page"
    heading = newTag('h2', content=title)
    subhead = newTag('h4', content="This disambiguation page lists modules that share the same name for a public symbol")
    body_parts = [heading, subhead]

    todo_list = sorted(s for s in symbols_db if len(symbols_db[s])>1)
    for s in todo_list:
        symbol = s.lower()
        owner_modules = symbols_db[s]
        items = []
        for m in owner_modules:
            module = m.lower()
            link = newTag('a', content=module, attributes={"href":filename(module, hashtag=symbol), "title":modules_description[module]})
            items.append(newTag('li', content=link))
        sname = newTag('span', content=symbol, id=symbol, attributes={"class":"symname"})
        p = newTag('p', content=[sname, " symbol found in "+str(len(owner_modules))+" modules:"])
        l = newTag('ul', content=items, attributes={"class":"horizontal", "style":'padding-top: 0;'})
        body_parts.extend([p, l])

    body = newTag('body', content=body_parts)
    fileBaseName = "disambiguation"
    printout(body, prefix, title=title, output_file=fileBaseName)

#=============================================================================
class IofIndices():

    def __init__(self, fmt='html'):
        self.l2sort = []
        self.brief  = []
        self.fmt = fmt
        self.dname = None

    def Append(self, brief, fn, t):
        assert(fn.endswith('.' + self.fmt))
        dname = path.dirname(fn)
        if(self.dname):
            assert(dname == self.dname)
        else:
            self.dname = dname
        fname = path.basename(fn)
        k = fname.rsplit('.',1)[0]
        setattr(self, k, t)
        self.l2sort.append(k)
        self.brief.append(brief)

#EOF
