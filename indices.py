#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from printout import html_document_heading, filename, separator
from mostly_used import l as mostly_used

#=============================================================================
def print_general_index(prefix, indices, fmt='html'):
    title = 'DBCSR API Documentation'
    indices_list = indices.l2sort
    if(fmt=='html'):
        html, body = html_document_heading(title, hlevel=1, htext=title, hklass='index_title')

        list_of_indices = body.ul()
        for i in indices_list:
            list_of_indices.li.h3.a(getattr(indices, i), href='.'.join([i, fmt]))

        f = open( path.join( prefix, "index.html" ), 'w' )
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

    else:
        assert(False) # Unknown format

#=============================================================================
def print_mostly_used_index(api, prefix, fmt='html'):

    title = 'Mostly used DBCSR API symbols by functionality'

    if(fmt=='html'):
        html, body = html_document_heading(title, hlevel=1, htext=title, hklass='index_title')

        container = body.div(id='flex-container')
        for item in mostly_used:
            outer_list_item = container.div(klass='linkbox', style='width: 32em;')
            outer_list_item.h2(item['descr'])
            inner_list = outer_list_item.ul(style='list-style-type:square; padding-bottom:1em;')
            for sym_name in sorted(item['symbols']):
                sym = sym_name.upper()
                owner_module, ext_sym_name = api['symbols_map'][sym].lower().split(':')
                href = filename(owner_module, hashtag=ext_sym_name)
                inner_list.li.a(sym_name, href=href)

        fn = path.join( prefix, "mostly_used_index.html" )
        f = open( fn, 'w' )
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

    else:
        assert(False) # Unknown format

    return fn, title

#=============================================================================
def print_logical_tree_index(api, prefix, src_tree, packages, fmt='html'):

    title = 'Logical tree index of DBCSR API symbols'

    if(fmt=='html'):
        html, body = html_document_heading(title, hlevel=1, htext=title, hklass='index_title')

        print_tree(api, src_tree, packages, body)

        fn = path.join( prefix, "tree_index.html" )
        f = open( fn, 'w' )
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

    else:
        assert(False) # Unknown format

    return fn, title

#=============================================================================
def print_tree(api, tree, packages, body, rootnode=None):

    children = sorted(tree.GetChildren(rootnode))

    # no need to open a new ordered list if there are no children!
    if(not children):
        return

    children_list = body.ol('', klass='autonumb')
    for child in children:
        relative_path = child.replace(tree.root,'',1)[1:]
        files = packages[child]['files']

        my_modules_map = {}
        for f in files:
            mod_name = f.rsplit(".", 1)[0].upper()
            if mod_name in api['modules_map']:
                my_modules_map[mod_name.lower()] = api['modules_map'][mod_name]

        if(my_modules_map):
            children_item = children_list.li(style='padding:15px;')
            children_item.text(relative_path)
            children_item.text(separator, escape=False)
            children_item.text(packages[child]['description'])

            container = children_item.div(id='flex-container')
            for mod_name, symbols in my_modules_map.iteritems():
                modules_item = container.div(klass='linkbox')
                modules_item.h2.a(mod_name, href=filename(mod_name))

                symbols_list = modules_item.ul('', style='list-style-type:square; padding-bottom:1em;')
                for sym in sorted(symbols.keys()):
                    tag = api['symbols_cat'][sym][:-1]
                    sym_name = sym.lower()
                    external_sym_name = symbols[sym].lower()
                    href = filename(mod_name, hashtag=external_sym_name)
                    symbols_list.li.a(sym_name, href=href)

        # recurse ...
        print_tree(api, tree, packages, children_list, rootnode=child)

#=============================================================================
def print_alphabetic(mod_list, prefix, descr='all', fmt='html'):
    items_list = sorted(mod_list)
    initials = sorted(set(item[0] for item in items_list))
    items_dict = dict((ini, [item for item in items_list if item.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of '+descr+' modules'

    if(fmt=='html'):

        html, body = html_document_heading(title, hlevel=1, htext=title, hklass='index_title')

        # initials
        l = body.ul(klass='menu')
        for ini in initials:
            l.li.a(ini.upper(), href='#'+ini)

        outer_list = body.ul(klass='nobullet')
        for ini in initials:
            item = outer_list.li
            item.h4(ini.upper(), id=ini)
            inner_list = item.div(klass='columns').ul
            for mod in items_dict[ini]:
                inner_list.li.a(mod, href=filename(mod))

        fn = path.join( prefix, "alphabetic_index_"+'_'.join(descr.split())+".html" )
        f = open( fn, 'w' )
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

    else:
        assert(False) # Unknown format

    return fn, title

#=============================================================================
def print_alphabetic_index(api, prefix, fmt='html'):
    symbols_list = sorted(api['symbols_map'].keys())
    initials = sorted(set(sym[0] for sym in symbols_list))
    symbols_dict = dict((ini, [sym for sym in symbols_list if sym.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of DBCSR API symbols'

    if(fmt=='html'):

        html, body = html_document_heading(title, hlevel=1, htext=title, hklass='index_title')

        # initials
        l = body.ul(klass='menu')
        for ini in initials:
            l.li.a(ini, href='#'+ini)

        outer_list = body.ul(klass='nobullet')
        for ini in initials:
            item = outer_list.li
            item.h4(ini, id=ini)
            inner_list = item.div(klass='columns').ul
            for sym in symbols_dict[ini]:
                sym_name = sym.lower()
                owner_module, ext_sym_name = api['symbols_map'][sym].lower().split(':')
                href = filename(owner_module, hashtag=ext_sym_name)
                inner_list.li.a(sym_name, href=href)

        fn = path.join( prefix, "alphabetic_index.html" )
        f = open( fn, 'w' )
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

    else:
        assert(False) # Unknown format

    return fn, title

#EOF
