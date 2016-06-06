#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from mostly_used import l as mostly_used
from makeHTML import newTag
from render import filename, printout

#=============================================================================
def print_general_index(prefix, indices, fmt='html'):
    title = 'DBCSR API Documentation'
    indices_list = indices.l2sort
    if(fmt=='html'):

        heading = newTag('h1', content=title, attributes={"class":'index_title'})

        items = []
        for i in indices_list:
            link = newTag('a', content=getattr(indices, i), attributes={"href":'.'.join([i, fmt])})
            head = newTag('h3', content=link)
            item = newTag('li', content=head)
            items.append(item)
        list_of_indices = newTag('ul', content=items)

        body = newTag('body', content=[heading, list_of_indices])
        printout(body, prefix, title=title, output_file="index")

    else:
        assert(False) # Unknown format

#=============================================================================
def print_mostly_used_index(api, prefix, fmt='html'):

    title = 'Mostly used DBCSR API symbols by functionality'

    if(fmt=='html'):

        heading = newTag('h1', content=title, attributes={"class":'index_title'})

        items = []
        for item in mostly_used:
            inner_items = []
            for sym_name in sorted(item['symbols']):
                sym = sym_name.upper()
                owner_module, ext_sym_name = api['symbols_map'][sym].lower().split(':')
                href = filename(owner_module, hashtag=ext_sym_name)
                link = newTag('a', content=sym_name, attributes={"href":href})
                inner_item = newTag('li', content=link)
                inner_items.append(inner_item)
            inner_list = newTag('ul', content=inner_items, attributes={"style":'list-style-type:square; padding-bottom:1em;'})
            head = newTag('h2', content=item['descr'])
            outer_list_item = newTag('div', content=[head, inner_list], attributes={"class":'linkbox', "style":'width: 32em;'})
            items.append(outer_list_item)
        container = newTag('div', content=items, id='flex-container')

        body = newTag('body', content=[heading, container])

        fn = "mostly_used_index"
        printout(body, prefix, title=title, output_file=fn)

    else:
        assert(False) # Unknown format

    return fn+".html", title

#=============================================================================
def print_logical_tree_index(api, prefix, src_tree, packages, sym_lookup_table=None, fmt='html'):

    if api == '__ALL__':
        title = 'Logical tree index of ALL symbols'
    else:
        title = 'Logical tree index of DBCSR API symbols'

    if(fmt=='html'):

        heading = newTag('h1', content=title, attributes={"class":'index_title'})

        branches = get_tree(api, src_tree, packages, sym_lookup_table)
        assert(branches)
        body = newTag('body', content=[heading, branches])

        fn = "tree_index" if api == '__ALL__' else "API_tree_index"
        printout(body, prefix, title=title, output_file=fn)

    else:
        assert(False) # Unknown format

    return fn+".html", title

#=============================================================================
def get_tree(api, tree, packages, sym_lookup_table, rootnode=None):

    children = sorted(tree.GetChildren(rootnode))

    # no need to open a new ordered list if there are no children!
    if(not children):
        return

    children_list = newTag('ol', attributes={"class":'autonumb'})
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
            content = ' &#8212; '.join([relative_path, packages[child]['description']])
            children_item = newTag('li', content=content, attributes={"style":'padding:15px;'}, newlines=False)
            children_list.addPiece(children_item)

            contained_items = []
            for mod_name, symbols in my_modules_map.iteritems():

                items = []
                for sym in sorted(symbols.keys()):
                    sym_name = sym.lower()
                    external_sym_name = symbols[sym].lower()
                    href = filename(mod_name, hashtag=external_sym_name)
                    link = newTag('a', content=sym_name, attributes={"href":href})
                    item = newTag('li', content=link)
                    items.append(item)
                link = newTag('a', content=mod_name, attributes={"href":filename(mod_name)})
                head = newTag('h2', content=link, attributes={"class":'ellipsed'})
                symbols_list = newTag('ul', content=items, attributes={"style":'list-style-type:square; padding-bottom:1em;'})
                modules_item = newTag('div', content=[head, symbols_list], attributes={"class":'linkbox'})

                contained_items.append(modules_item)

            container = newTag('div', content=contained_items, id='flex-container')
            children_item.addPiece(container)

        # recurse ...
        branches = get_tree(api, tree, packages, sym_lookup_table, rootnode=child)
        if branches:
            children_item.addPiece(branches)

    return children_list

#=============================================================================
def print_alphabetic(mod_list, prefix, descr='all', fmt='html'):
    items_list = sorted(mod_list)
    initials = sorted(set(item[0] for item in items_list))
    items_dict = dict((ini, [item for item in items_list if item.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of '+descr+' modules'

    if(fmt=='html'):

        heading = newTag('h1', content=title, attributes={"class":'index_title'})

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
                link = newTag('a', content=mod, attributes={"href":filename(mod)})
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
def print_alphabetic_index(api, prefix, fmt='html'):
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

#EOF
