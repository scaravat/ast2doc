#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from makeHTML import newTag
from render import filename, printout

#=============================================================================
def print_allModules(prefix, modules_list, pkgname=None):

    if pkgname:
        title_pre = ""
        title_pkg = newTag('span', content=pkgname, attributes={"class":'pkgname'})
        title_post = ""
        subtitle = " modules:"
        title = [title_pre, title_pkg, title_post, subtitle]
    else:
        title = "All Modules:"

    heading = newTag('h2', content=title, newlines=False)

    mod_items = []
    for module in sorted(modules_list):
        link = newTag('a', content=module, attributes={"href":module+".html", "target":'moduleFrame'})
        mod_items.append(newTag('li', content=link))
    mod_list = newTag('ul', content=mod_items, attributes={"class":'nobullet'})
    body = newTag('body', content=[heading, mod_list])

    fileBaseName = pkgname.replace('/','%').upper()+"-frame" if pkgname else "allmodules-frame"
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html'

#=============================================================================
def print_packageFrame(prefix, modules_lists):
    packages = [item for item in modules_lists.keys() if not item in ('__ALL__', '__API__')]

    files = []
    for pkg in sorted(packages):
        pkgname = 'ROOT' if pkg=='.' else pkg
        title = "Modules for package " + pkgname
        heading = newTag('h2', content=title)
        my_modules = modules_lists[pkg]
        my_file = print_allModules(prefix, my_modules, pkgname=pkgname)
        files.append(my_file)
    return files

#=============================================================================
def print_packageListFrame(prefix, allModulesFile, src_tree):
    title = "Overview of CP2K API"
    heading = newTag('h2', content=title)

    link = newTag('a', content="All Modules", attributes={"href":allModulesFile, "target":"packageFrame", "style":'font-style:oblique;'})
    allModLink_div = newTag('div', content=link)

    pkglist = getTree(src_tree)
    rootnode = newTag('a', content="[root]", attributes={"href":"ROOT-frame.html", "target":"packageFrame", "style":'font-style:oblique;'})
    fakelist = newTag('ul', content=newTag('li', content=[rootnode, pkglist]), attributes={"class":"nobullet"})
    list_heading = newTag('h4', content="Packages tree:", attributes={"title":"Packages"})
    listContainer_div = newTag('div', content=[list_heading, fakelist])#, pkglist])

    body = newTag('body', content=[heading, allModLink_div, listContainer_div])

    fileBaseName = "overview-frame"
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html'

#=============================================================================
def getTree(tree, rootnode=None):
    branches = []
    for child in sorted(tree.GetChildren(rootnode)):
        pkgname = child.replace(tree.root,'',1)[1:]
        link = newTag('a', content=pkgname, attributes={"href":pkgname.replace('/','%').upper()+"-frame.html", "target":"packageFrame"})
        list_item = newTag('li', content=link)
        childpkglist = getTree(tree, rootnode=child)
        if childpkglist:
            list_item.addPiece(childpkglist)
        branches.append(list_item)

    if branches:
        pkglist = newTag('ul', content=branches, attributes={"class":"nobullet"})
        return pkglist

#=============================================================================
def get_banner(indices):

    buttons = []
    for i, basename in enumerate(indices.l2sort):
        my_title = getattr(indices, basename)
        button_name = indices.brief[i]
        button_id = 'button_' + basename
        target_href = basename + ".html"
        href = "javascript:setActive('"+basename+"')"
        link = newTag('a', content=button_name, attributes={"id":button_id, "href":href})
        buttons.append( newTag('li', content=link) )
    buttons_list = newTag('ul', content=buttons, attributes={"class":'navlist'})

    CP2kAPIlogo = newTag('img', attributes={"src":'cp2k_apidoc_logo.svg', "alt":'Logo', "class":'logo'})
    header = newTag('h1', content=["CP2K API-Documentation", CP2kAPIlogo], newlines=False)
    spacer = newTag('div', content='&nbsp;', attributes={"class":'clearfix'}, newlines=False)
    banner = newTag('div', content=[header, buttons_list, spacer], newlines=False)
    return banner

#=============================================================================
def print_overview(prefix, src_tree, packages, modules_lists, api, sym_lookup_table):

    my_indices = IofIndices()
    my_indices.Append( 'Tree', *print_logical_tree_index('__ALL__', prefix, src_tree, modules_lists, packages, sym_lookup_table) )
    my_indices.Append( 'Index', *print_alphabetic(modules_lists['__ALL__'], prefix, 'all') )
   #my_indices.Append( 'Mostly used', *print_mostly_used(api, prefix) )
   #my_indices.Append( 'DBCSR tree', *print_logical_tree_index(api, prefix, src_tree, modules_lists, packages) )
    my_indices.Append( 'DBCSR modules', *print_alphabetic(modules_lists['__API__'], prefix, 'DBCSR API') )

    # last `index' is "About"
    my_indices.Append( 'About', *print_about_page(prefix) )

    banner = get_banner(my_indices)
    noframe = newTag('p', content="Your browser does not support iframes.")
    index_iframe = newTag('iframe', content=noframe, attributes={
        "src":my_indices.l2sort[0]+".html", "name":"OverviewFrame", "id":"OverviewFrame", "class":'wideautoheight',
        "onload":"javascript:getActive()", "onpopstate":"javascript:debugActive()"
    })
    body = newTag('body', content=[banner, index_iframe])#, attributes={"onpopstate":"javascript:getActive()"})

    fileBaseName = "overview-summary"
    printout(body, prefix, title="Overview", output_file=fileBaseName, jscript="active.js")
    return fileBaseName+'.html'

#=============================================================================
def print_landingPage(prefix, src_tree, packages, modules_lists, statistics, api, sym_lookup_table):

    allModulesFile  = print_allModules(prefix, modules_lists['__ALL__'])
    pkgModulesFiles = print_packageFrame(prefix, modules_lists)
    packageListFile = print_packageListFrame(prefix, allModulesFile, src_tree)
    overviewFile    = print_overview(prefix, src_tree, packages, modules_lists, api, sym_lookup_table)

    title = 'CP2K API Documentation'

    packageListFrame = newTag('frame', attributes={"src":packageListFile, "name":"packageListFrame", "title":"All Packages"})
    packageFrame     = newTag('frame', attributes={"src":allModulesFile, "name":"packageFrame", "title":"All Modules"})
    moduleFrame      = newTag('frame', attributes={"src":overviewFile, "name":"moduleFrame", "title":"Module descriptions", "scrolling":"yes"})

    noscript = newTag('noscript', content=newTag('div', content="JavaScript is disabled on your browser."))
    heading  = newTag('h2', content="Frame Alert")
    paragrph = newTag('p',  content="This document is designed to be viewed using the frames feature. If you see this message, you are using a non-frame-capable web client.")
    noframes = newTag('noframes', content=[noscript, heading, paragrph])

    inner_frameset = newTag('frameset', content=[packageListFrame, packageFrame], attributes={
        "rows":"30%,70%", "title":"Left frames", "onload":"top.loadFrames()"})
    outer_frameset = newTag('frameset', content=[inner_frameset, moduleFrame, noframes], attributes={
        "cols":"20%,80%", "title":"Documentation frame", "onload":"top.loadFrames()"})

    printout(outer_frameset, prefix, title=title, output_file="index", jscript="searchURL.js")

#=============================================================================
def print_about_page(prefix):
    title = 'About CP2K API documentation'
    fileBaseName = 'about.html'
    body = newTag('body', content=title)
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html', title

#=============================================================================
def get_package_stuff(modules_lists, packages, pkg_path='__ROOT__'):
    root = path.normpath(path.commonprefix(packages.keys())) 
    be_root = pkg_path=='__ROOT__'
    node = root if be_root else pkg_path
    rel_path = path.relpath(node, root)
    pkg_name = '[root]' if be_root else pkg_path.replace(root, '', 1)[1:]
    pkg_id = node + '%mlist'
    pkg_files = [f.rsplit(".", 1)[0] for f in packages[node]['files']]
    pkg_modules = [f for f in pkg_files if f in modules_lists[rel_path]]
    mlinks = [newTag('a', content=m, attributes={"href":m+".html", "target":'moduleFrame'}) for m in sorted(pkg_modules)]
    mitems = [newTag('li', content=l) for l in mlinks]
    mlist = newTag('ul', content=mitems, attributes={"class":'horizontal', "style":'padding:5px;'})
    modules_container = newTag('div', content=mlist, attributes={"id":pkg_id, "class":'togglevis'})
    node_button = newTag('a', content=pkg_name, attributes={"href":"javascript:showhide('"+pkg_id+"')"})
    if be_root:
        node_button.addAttribute("style", 'font-style:oblique;')
    description = packages[node]['description']
    return [node_button, ' &#8212; ', description, modules_container]

#=============================================================================
def print_logical_tree_index(api, prefix, src_tree, modules_lists, packages, sym_lookup_table=None, fmt='html'):

    if api == '__ALL__':
        title = 'Logical tree of ALL packages'
    else:
        title = 'Logical tree index of DBCSR API symbols'

    if(fmt=='html'):

        heading = newTag('h2', content=title, attributes={"class":'index_title'})

        root_item = newTag('li', content=get_package_stuff(modules_lists, packages))

        branches = get_tree(api, src_tree, modules_lists, packages, sym_lookup_table)
        assert(branches)
        root_item.addPiece(branches)

        outer_list = newTag('ul', content=root_item, attributes={"class":'nobullet'})
        body = newTag('body', content=[heading, outer_list])

        fn = "tree_index" if api == '__ALL__' else "API_tree_index"
        printout(body, prefix, title=title, output_file=fn, jscript="showhide.js")

    else:
        assert(False) # Unknown format

    return fn+".html", title

#=============================================================================
def get_tree(api, tree, modules_lists, packages, sym_lookup_table, rootnode=None):

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
            children_item = newTag('li', content=get_package_stuff(modules_lists, packages, child))

            # recurse ...
            branches = get_tree(api, tree, modules_lists, packages, sym_lookup_table, rootnode=child)
            if branches:
                children_item.addPiece(branches)

            children_list.addPiece(children_item)

    return children_list

#=============================================================================
def print_alphabetic(mod_list, prefix, descr, fmt='html'):
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
                link = newTag('a', content=mod, attributes={"href":filename(mod), "target":'moduleFrame'})
                inner_item = newTag('li', content=link)
                inner_items.append(inner_item)

            inner_list = newTag('ul', content=inner_items)
            columns = newTag('div', content=inner_list, attributes={"class":'columns'})
            back_link = newTag('a', content=ini.upper(), attributes={"href":'#initials'})
            head = newTag('h4', content=back_link, id=ini.upper())
            item = newTag('li', content=[head, columns])
            items.append(item)
        outer_list = newTag('ul', content=items, attributes={"class":'nobullet'})

        body_parts = [heading, ini_list, outer_list]
        body = newTag('body', content=body_parts)

        fn = "alphabetic_index_"+'_'.join(descr.split())
        printout(body, prefix, title=title, output_file=fn)

    else:
        assert(False) # Unknown format

    return fn+".html", title

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
