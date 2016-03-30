#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from html import HTML
import re
import utils

missing_description = '...'
separator = ' :: '

#=============================================================================
def html_document_heading(title, comment=None, hlevel=0, htext=None, hklass=None, plain=False):

    if(plain):
        html = None
        body = HTML()

    else:

        # the main html object
        html = HTML('html')

        # head
        head = html.head
        head.link(rel="stylesheet",href="styles.css")
        head.title(title)

        # body
        body = html.body(newlines=True)

    if(comment):
        body.raw_text('\n<!--\n'+comment+'\n-->')

    if(hlevel>0):
        assert(htext)
        heading = getattr(body, 'h'+str(hlevel))
        if(hklass):
            heading(htext, klass=hklass, escape=False)
        else:
            heading(htext, escape=False)

    return html, body

#=============================================================================
def document_module(ast, rel_path, ast_dir, prefix, api, sym_lookup_table):

    # prefetch some info
    mod_name   = ast['name']
    my_name    = mod_name.lower()
    my_file    = my_name + '.F'
    my_role    = ast['tag'].upper()
    my_title   = ' '.join(['SUMMARY for', my_role, my_name])
    my_publics = set(f['name'] for f in ast['publics'])
    my_descr = ast['descr'] if ast['descr'] else [missing_description]
    comment = " ".join([my_role, my_name]).strip()

    api_symbols = api['symbols_map'].keys()
    my_symbols_map = sym_lookup_table[mod_name]['symbols_map']
    my_symbols_cat = sym_lookup_table[mod_name]['symbols_cat']

    # HTML printout
    h_title = 'Documentation for module ' + str(HTML().kbd(my_name, klass="symname"))
    html, body = html_document_heading(my_title, comment=comment, hlevel=2, htext=h_title)

    # ...module description
    for l in my_descr:
        body.p(l, escape=False)

    # ...link to the source code (@sourceforge)
    href = path.join( path.join('https://sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/src', rel_path), my_file )
    body.p('(source: ' + str(HTML().a(my_file, href=href)) + ')', escape=False)

    # prefetch public symbols names
    pars, types, intfs = (my_publics.intersection(s['name'] for s in ast[cat]) for cat in ('variables', 'types', 'interfaces'))

    # ...parameters & static vars
    if pars:
        body.hr
        paramts, statics = document_module_vars(ast['variables'], pars, api_symbols, my_symbols_map)
        if(paramts):
            body.div(klass='box', id='parameters').raw_text(str(paramts))
        if(statics):
            body.div(klass='box', id='staticvars').raw_text(str(statics))
#   priv_pars = set(s['name'] for s in ast['variables']).difference(pars)
#   if priv_pars:
#       paramts, statics = document_module_vars(ast['variables'], priv_pars, [], my_symbols_map)
#       if(paramts):
#           body.div(klass='box', id='parameters').raw_text(str(paramts))
#       if(statics):
#           body.div(klass='box', id='staticvars').raw_text(str(statics))

    #   ... types
    if types:
        body.hr
        document_types_set_inplace(body, 'public',  types,      ast['types'], api_symbols, my_symbols_map, prefix)
    priv_types = set(s['name'] for s in ast['types']).difference(types)
    if priv_types:
        # private types are documented as well!
        document_types_set_inplace(body, 'private', priv_types, ast['types'], [],          my_symbols_map, prefix)

    #   ... interfaces summary (generic procedures)
    if intfs:
        body.hr
        summary, specifics = interfaces_summary(intfs, ast['interfaces'], my_symbols_map)
        body.div(klass='box', id='interfaces_list').raw_text(str(summary))

    #   ... subroutines & functions
    all_subs_funs  = ast['subroutines']+ast['functions']
    functs_names = [s['name'] for s in all_subs_funs]
    functs_publics = sorted(my_publics.intersection(functs_names))
    if functs_publics:
        body.hr
        summary = routines_summary(functs_publics, ast['subroutines'], ast['functions'], my_symbols_map, api_symbols)
        body.div(klass='box', id='routines_list').raw_text(str(summary))
        for sym in functs_publics:
            subr = document_routine(all_subs_funs[functs_names.index(sym)], my_symbols_map, ast_dir)
            body.div(klass='box', id=sym.lower()).raw_text(str(subr))

    #   ... specific functions for interfaces
    if intfs:
        body.hr
        for sym in sorted(intfs):
            if(sym in specifics):
                iface = document_interface(sym, ast, ast_dir, specifics[sym], sym_lookup_table)
                body.div(klass='box', id=sym.lower()).raw_text(str(iface))

    # categories end
    body.hr

    # printout
    stuff = ["<!DOCTYPE html>", str(html), '']
    f = open(filename(my_name, prefix=prefix), 'w' )
    f.write('\n'.join(stuff))
    f.close()

#===============================================================================
def document_interface(iname, ast, ast_dir, specifics, sym_lookup_table):

    inames  = [s['name'] for s in ast['interfaces']]
    my_ast  = ast['interfaces'][inames.index(iname)]
    mod_name = ast['name']

    my_name = iname.lower()
    comment = " ".join(['INTERFACE', my_name])

    h_title = 'Generic procedure ' + str(HTML().kbd(my_name, klass="symname"))
    dummy_html, body = html_document_heading(None, comment=comment, hlevel=4, htext=h_title, plain=True)

    sp, sp_symmap = import_specifics(specifics, ast, ast_dir, sym_lookup_table)

    # tweak attributes to pop the info on INTENT and DIMENSION
    args_list = [s['args'] for s in sp]
    tweak_attrs_inplace(args_list)

    body.raw_text(process_specifics(sp, sp_symmap, sym_lookup_table[mod_name]['symbols_map'], my_name, ast_dir))

    return body

#===============================================================================
def process_specifics(sp, sp_symmap, symmap, my_name, ast_dir):

    nsp = len(sp)
    tags, names, args_list = ([s[k] for s in sp] for k in ('tag', 'name', 'args'))
    assert(len(set(tags)) == 1)
    tag = tags.pop()

    # set up tests to check if the compact view is possible
    tests = []
    nargs = [len(args) for args in args_list]
    tests.append( len(set(nargs))==1 )
    na = sorted(nargs)[0]
    for k in ('name', 'intent', 'dim'):
        tests.append(all( len(set([args[i][k] for args in args_list]))==1 for i in range(na) ))
    dim_test = tests.pop()

    body = HTML()
    if all(tests):
        # compact view
        body.p('(')
        t = body.div(style='overflow: auto; overflow-y: hidden;').table(klass="arglist", style='text-align: center;')
        table_header = t.tr(klass='tabheader')
        table_header.td('') # skip arg name
        table_header.td('') # skip intent
        for name in names:
            sp_name = name.lower()
            table_header.td(klass='tabheader').a(sp_name, id=':'.join([my_name, sp_name]))# TODO: href to the binding?

        for i in range(na):
            common_name = (args_list[0][i]['name'] + args_list[0][i]['dim']).lower()
            common_intent = args_list[0][i]['intent'].lower()

            # is the arg. type (and attributes) equal among the different specific functions?
            args_dims  = [args[i]['dim']  for args in args_list]
            args_types = [args[i]['type'] for args in args_list]
            args_attrs = [", ".join(sorted(args[i]['attrs'])) for args in args_list]
            do_merge = len(set(args_types))==len(set(args_attrs))==len(set(args_dims))==1

            r = t.tr(klass='alternating')
            r.td(common_name,   klass="argname", style='text-align: left;')
            r.td(common_intent, klass="intent")
            if(do_merge):
                common_type = args_types[0]
                dim = args_dims[0]
                attrs = args_attrs[0]
                cell = r.td(klass='vtype', colspan=str(nsp))
                cell.raw_text(get_vtype_href(common_type, symmap))
                if dim:
                    cell.raw_text(',<br>'+'DIMENSION'+dim)
                if attrs:
                    cell.raw_text(',<br>'+attrs)
            else:
                for j, args in enumerate(args_list):
                   #print 'SPP', sp[j]['name']
                    attrs = args_attrs[j]
                    dim = args_dims[j]
                    cell = r.td(klass='vtype')
                    my_symmap = sp_symmap[j] if sp_symmap[j] else symmap
                    cell.raw_text(get_vtype_href(args[i]['type'], my_symmap))
                    if dim:
                        cell.raw_text(',<br>'+'DIMENSION'+dim)
                    if attrs:
                        cell.raw_text(',<br>'+attrs)
        body.p(')')

    else:
        i = find_anytype(names)
        if isinstance(i,int):
            sp_any = sp.pop(i)
            my_symmap = sp_symmap.pop(i)
            documentation = document_routine(sp_any, my_symmap if my_symmap else symmap, ast_dir)
            body.h5('"AnyType" specific procedure:')
            sp_any_div = body.div(klass='box', id=':'.join([my_name, names.pop(i).lower()]))
            sp_any_div.raw_text(documentation) 
            body.h5('Other specific procedures:')
            body.raw_text(process_specifics(sp, sp_symmap, symmap, my_name, ast_dir))
        else:
            # giving up: simple list of bindings...
            for i, s in enumerate(sp):
                div = body.div(klass='box', id=':'.join([my_name, names[i].lower()]))
                documentation = document_routine(s, sp_symmap[i] if sp_symmap[i] else symmap, ast_dir)
                div.raw_text(documentation)

    return body

#===============================================================================
def find_anytype(names):
    for i, name in enumerate(names):
        spl = name.split('_')
        if any(part.startswith('ANY') for part in spl):
            return i

#===============================================================================
def import_specifics(specifics, ast, ast_dir, sym_lookup_table):
    sp, sp_symmap = [], []
    sp_sorting = specifics['l2sort']
    for k in sp_sorting:
        v = specifics[k]
        module, external_sym = v.split(':',1)
        if(module == '__HERE__' or module == '__PRIV__'):
            target_ast = ast
            symmap = None
        else:
            mfile = path.join(ast_dir, module.lower()+'.ast')
           #print 'EXT', k, mfile, ast['name']
            target_ast = utils.read_ast(mfile)
           #symmap = dict(sym_lookup_table[module]['symbols_map'])

            # copy the symmap (and tweak it when it contains symbols local to the imported module!)
            symmap = {}
            for key, val in sym_lookup_table[module]['symbols_map'].iteritems():
                m, ext_s = val.split(':',1)
                if m == '__HERE__':
                    symmap[key] = ':'.join([module, ext_s])
                elif m == '__PRIV__':
                    pass
                else:
                    assert(not re.match('__\w+__', m))
                    symmap[key] = val
    
        cat = sym_lookup_table[ast['name']]['symbols_cat'][k]
        sp.append(next( (item for item in target_ast[cat] if item['name'] == external_sym), None ))
        sp_symmap.append(symmap)
    return sp, sp_symmap

#===============================================================================
def tweak_attrs_inplace(args_list):
    for arg in utils.traverse(args_list):
        attrs = arg['attrs']
        intent = next((a for a in attrs if a.startswith("INTENT(")), "")
        if(intent):
            attrs.remove(intent)
            intent = re.match("INTENT\((.+)\)$",intent).group(1)
            assert(not 'intent' in arg)
            arg['intent'] = intent
        else:
            arg['intent'] = ""
        dim = next((a for a in attrs if a.startswith("DIMENSION(")), "")
        if(dim):
            attrs.remove(dim)
            if(not arg['dim']):
                arg['dim'] = re.match("DIMENSION(\(.+\))$",dim).group(1)

#===============================================================================
def interfaces_summary(names, intfcs, symmap):
    inames = [s['name'] for s in intfcs]
    dummy_html, body = html_document_heading(None, hlevel=4, htext='Generic procedures:', plain=True)
    container = body.div(id='flex-container')
    specifics = {}
    for ifname in sorted(names):
        iface = intfcs[inames.index(ifname)]
        if(iface['task'] == 'overloading'):
            outer_list_item = container.div(klass='linkbox', style='width: 32em;')
            outer_list_item.h2.a(ifname.lower(), href='#'+ifname.lower())
            inner_list = outer_list_item.ul(style='list-style-type:square; padding-bottom:1em;')
            procedures = iface['procedures']
            specifics[ifname] = {'l2sort':procedures}
            for specific in procedures:
                specifics[ifname][specific] = symmap[specific]
                sym_name = specific.lower()
                inner_list.li.a(sym_name, href='#'+':'.join([ifname.lower(), sym_name]))
        else:
            print 'SKIPPING INTERFACE ', iface['name'], iface['procedures']

    return body, specifics

#===============================================================================
def routines_summary(names, subs, funs, symmap, api_syms):
    snames = [s['name'] for s in subs]
    fnames = [s['name'] for s in funs]

    dummy_html, body = html_document_heading(None, hlevel=4, htext='Subroutines/Functions:', plain=True)

    # symbols list
    container = body.div(klass='box')
    for i, sym in enumerate(names):
        my_ast = subs[snames.index(sym)] if sym in snames else funs[fnames.index(sym)]

        is_api    = sym in api_syms
        api_class = 'api_symbol' if is_api else 'other_symbol'
        APIness   = 'API ' if is_api else ''
        attrs     = ' '.join(my_ast['attrs']+[''])
        retval    = my_ast['retval']['type'] if my_ast['retval'] else ''
        tag       = my_ast['tag'].upper() + ' '
        sym_name  = sym.lower()
        arglist   = [a['name'].lower() for a in my_ast['args']]
        postattrs = ' '.join(my_ast['post_attrs']) if 'post_attrs' in my_ast else ''
        descr     = '. '.join(my_ast['descr']) if my_ast['descr'] else missing_description
        bg_color  = '#f2f2f2' if i%2==1 else 'white'

        div = container.div(style='background-color:'+bg_color)
        t = div.table(klass="argdescrheading", style='font-family:monospace;')
        row = t.tr
        prefix = row.td(klass='sign_prefix')
        prefix.div(APIness, klass='apiness', style='display:inline;')
        prefix.text(attrs)
        row.td(klass='sign_retval').raw_text(get_vtype_href(retval, symmap))
        signtr = row.td(tag)
        signtr.a(sym_name, href='#'+sym_name)
        if(arglist):
            signtr.text('( ')
            for arg in arglist[:-1]:
                signtr.a(arg, href='#'+':'.join([sym_name, arg]))
                signtr.text(', ')
            else:
                arg = arglist[-1]
                signtr.a(arg, href='#'+':'.join([sym_name, arg]))
            signtr.text(' )')
            
        else:
            signtr.text('( )')
        if(postattrs):
            signtr.text(postattrs)

        row = t.tr
        row.td('') # skip prefix
        row.td('') # skip retval
        row.td(descr, escape=False, klass="argdescr", style='padding-bottom:1em;')

    return body

#===============================================================================
def document_module_vars(variables, vpublics, api_symbols, my_symbols_map):
    # 'variables' can be only static variables or parameters
    vnlist = [v['name'] for v in variables]
    paramts, statics = [], []
    for vname in vpublics:
        v = variables[vnlist.index(vname)]
        if('PARAMETER' in v['attrs']):
            assert(not 'SAVE' in v['attrs'])
            paramts.append(v)
        elif('SAVE' in v['attrs']):
            assert(not 'PARAMETER' in v['attrs'])
            statics.append(v)

    p = document_parameters(paramts, api_symbols, my_symbols_map) if paramts else ''
    s = document_staticvars(statics, api_symbols, my_symbols_map) if statics else ''

    return(p, s)

#===============================================================================
def document_parameters(paramts, api_symbols, my_symbols_map, hint='PARAMETER'):
    assert(paramts)
    html = HTML()
    html.p('Parameters:' if hint=='PARAMETER' else 'Static variables:')
    t = html.table(klass="arglist")
    names = [v['name'] for v in paramts]
    for sym in sorted(names):
        v = paramts[names.index(sym)]
        sym_name = sym.lower()
        api_class = 'api_symbol' if sym in api_symbols else 'argname'
        APIness   = '(API)' if sym in api_symbols else ''
        attrs  = v['attrs'][:]
        attrs.remove(hint)
        v_name = sym_name + v['dim']
        if 'init' in v:
            v_name += ' = ' + v['init'][1:].lower()
        v_type = get_vtype_href(v['type'], my_symbols_map)
        v_alst = ', '.join(attrs)

        r = t.tr(klass='alternating')
        r.td(klass='vtype').raw_text(v_type)
        r.td(v_alst,    klass="misc_attrs")
        r.td(separator, klass="separee", escape=False)
        r.td(v_name,    klass="parname", id=sym_name)
        r.td(APIness,   klass="apiness")
    return html

#===============================================================================
def document_staticvars(*args):
    return document_parameters(*args, hint='SAVE')

#===============================================================================
def document_types_set_inplace(body, tag, names, ast, api_symbols, my_symbols_map, prefix):
    if names:
        type_names = [s['name'] for s in ast]
        body.h5(tag.title() + " types:", id='types_'+tag)
        if len(names)>1:
            ul = body.div(style='width: 100%; font-family: monospace;').ul(klass='horizontal')
            for s in sorted(names):
                sym = s.lower()
                ul.li.a(sym, href='#'+sym)
        for sym in sorted(names):
            my_ast = ast[type_names.index(sym)]
            t = document_type(my_ast, sym in api_symbols, my_symbols_map, prefix)
            body.div(klass='box', id=sym.lower()).raw_text(str(t))

#===============================================================================
def document_type(tp, is_api, my_symbols_map, prefix):
    my_name  = tp['name'].lower()
    comment  = " ".join([tp['tag'].upper(), my_name])
    APIness  = 'API ' if is_api else ''

    h_title = APIness + 'TYPE' + separator + str(HTML().kbd(my_name, klass="symname"))
    dummy_html, body = html_document_heading(None, comment=comment, hlevel=4, htext=h_title, plain=True)

    body.hr
   #body.p('Members:')
    t = body.table(klass="arglist")
    for v in tp['variables']:
        if 'init' in v:
            if v['init'].startswith('=>'):
                v_init = ' => ' + v['init'][2:]
            elif v['init'].startswith('='):
                v_init = ' = ' + v['init'][1:]
            else:
                assert(False)
        else:
            v_init = ''

        v_name = v['name'].lower() + v_init
        v_type = get_vtype_href(v['type'], my_symbols_map)
        v_attr = ', '.join(v['attrs'])

        r = t.tr(klass='alternating')
        r.td(klass='vtype').raw_text(v_type)
        r.td(v_attr,    klass="misc_attrs")
        r.td(separator, klass="separee", escape=False)
        r.td(v_name,    klass="argname")
    body.hr

    return body

#===============================================================================
def document_routine(subr, module_symmap, ast_dir):

    # fetch routine's info
    my_name    = subr['name'].lower()
    my_role    = subr['tag'].upper()
    my_attrs   = " ".join(subr['attrs'])
    post_attrs = " ".join(subr['post_attrs']) if 'post_attrs' in subr else ''
    my_arglist = [arg['name'].lower() for arg in subr['args']]
    my_args    = '(' + ",".join(my_arglist) + ')'
    my_retval  = subr['retval']
    my_title   = ' '.join(['DBCSR', my_role, my_name])
    my_descr   = subr['descr'] if subr['descr'] else [missing_description]

    comment = " ".join([my_attrs, my_role, my_name, my_args, post_attrs]).strip()
    if(my_retval and subr['name']!=my_retval['name']):
        comment += " RESULT(%s)"%my_retval['name'].lower()

    if subr['uses']:
        # TODO; tweak cache_symbol_lookup to process also these USEs statements
        my_sym_lookup_table = {}
        utils.cache_symbol_lookup(subr, ast_dir, my_sym_lookup_table)
        internal_symmap = my_sym_lookup_table[subr['name']]['symbols_map']
        my_symbols_map = dict(module_symmap)
        for sym in internal_symmap:
            if sym in my_symbols_map:
                assert(my_symbols_map[sym] == internal_symmap[sym])
            else:
                my_symbols_map[sym] = internal_symmap[sym]
    else:
        my_symbols_map = module_symmap

    # group adjacent arguments with the same definition
    agroups = group_arguments(subr['args'])

    # heading
    h_title = my_role + str(HTML().kbd(my_name, klass="symname"))
    dummy_html, body = html_document_heading(None, comment=comment, hlevel=4, htext=h_title, plain=True)

    # routine description
    for l in my_descr:
        body.p(l, escape=False)

    # binding
    body.h5('Binding:')
    body.hr
    p = body.p(' '.join([my_attrs, my_role, '']))
    p.kbd(my_name, klass="symname")
    if(post_attrs):
        p.text(post_attrs)

    if(agroups):
        p += ' ('
        # ...arguments
        t = body.table(klass="arglist")
        for group in agroups:
            r = t.tr(klass='alternating')
            r.td('', style='padding-left:1.5em;')
            r.td(group['namelist'], klass="argname")
            r.td(group['intent'],   klass="intent")
            r.td(klass='vtype').raw_text(get_vtype_href(group['type'], my_symbols_map))
            r.td(group['attrs'],    klass="misc_attrs")
        body.p(')')
    else:
        p.text('( )')

    body.hr
    # binding end

    # return value (if function)
    if(my_retval):
        d = body.dl(klass="argsdescr")
        dh = d.dt.table(klass="argdescrheading")
        r = dh.tr
        r.td('Return Value')
        r.td(separator, escape=False)
        r.td(klass='vtype').raw_text(get_vtype_href(my_retval['type'], my_symbols_map))
        d.dd(my_retval['descr'], escape=False, klass="argdescr")

    # arguments description
    if(agroups):
        body.h5('Arguments:')
        d = body.dl(klass="argsdescr")
        for group in agroups:
            vtype = get_vtype_href(group['type'], my_symbols_map)
            attrs = group['attrs']
            for i in group['alist']:
                a = subr['args'][i]
                aname = a['name'].lower()
                adim  = (a['dim'] or '').lower()
                descr = a['descr'] if a['descr'] else missing_description

                dh = d.dt.table(klass="argdescrheading")
                r = dh.tr
                r.td(klass='vtype').raw_text(vtype)
                r.td(attrs,      klass="misc_attrs")
                r.td(separator,  klass="separee", escape=False)
                r.td(aname+adim, klass="argname", id=':'.join([my_name, aname]))

                d.dd(descr,      klass="argdescr", escape=False)

    return body

#===============================================================================
def group_arguments(args):
    alists = []
    prev_def = ""
    for iarg, arg in enumerate(args):
        definition = ",".join([arg['type']] + sorted(arg['attrs']))
        if definition == prev_def:
            alists[-1].append(iarg)
        else:
            # new group!
            alists.append([iarg])
            prev_def = definition

    agroups = []
    for alist in alists:
        arg0  = args[alist[0]]
        type0 = arg0['type']

        attrs = arg0['attrs'][:]
        intent = next((a for a in attrs if a.startswith("INTENT(")), "")
        if(intent):
            attrs.remove(intent)
            intent = re.match("INTENT\((.+)\)$",intent).group(1)
        dim = next((a for a in attrs if a.startswith("DIMENSION(")), "")
        if(dim):
            attrs.remove(dim)

        if(type0 == 'PROCEDURE'):
            namelist = ", ".join( [args[i]['name'] for i in alist] )
        else:
            namelist = ", ".join( [args[i]['name']+args[i]['dim'] for i in alist] )
        agroups.append({
            'namelist':namelist.lower(),
            'type':type0,
            'dim':dim,
            'intent':intent.lower(),
            'attrs':", ".join(attrs),
            'alist':alist
        })

    return agroups

#===============================================================================
external_stuff = {}
def get_vtype_href(vtype, symmap):
    global external_stuff
    if(not vtype):
        return ''
    var_type, spec = re.match("([A-Z]+)(?:\((.+)\))?", vtype).groups()
    h = HTML(newlines=False)
    h.text(var_type)
    if(spec):
        s_lowcase = spec.lower()
        meq = re.match('(\w+)=(.+)$',spec)
        mkw = re.match('(\w+)$',spec)
        assert(not (meq and mkw))
        m = meq or mkw
        if m:
            inner_spec = m.groups()[-1]
            inner_split = re.split('(\W+)', inner_spec)
            assert(''.join(inner_split) == inner_spec)
            h.text('(')
            for item in inner_split:
                do_href = bool(re.match('\w+$', item)) and (not item.isdigit()) and item in symmap
                if do_href:
                    owner_module, remote_sym = symmap[item].lower().split(':')
                    if owner_module.upper() in utils.external_modules:
                        external_stuff.setdefault(owner_module, set()).add(remote_sym)
                    h.a(item.lower(), href=filename(owner_module, hashtag=remote_sym))
                else:
                    h.text(item.lower())
            h.text(')')
        else:
            h.text('('+s_lowcase+')')
    return str(h)

#===============================================================================
def document_external(prefix):
    for ext_module, symbols in external_stuff.iteritems():
        h_title = 'Symbols from External/Intrinsic module ' + str(HTML().kbd(ext_module.upper(), klass="symname"))
        html, body = html_document_heading(ext_module, hlevel=3, htext=h_title)
        sym_list = body.ul(style='list-style-type:square; padding-bottom:1em;')
        for sym_name in sorted(symbols):
            sym_list.li(sym_name, id=sym_name)
        f = open(filename(ext_module, prefix=prefix), 'w')
        f.write("<!DOCTYPE html>\n" + str(html) + '\n')
        f.close()

#===============================================================================
def filename(owner_module, **kwargs):
    suffix  = kwargs.pop('suffix', 'html')
    prefix  = kwargs.pop('prefix', None)
    hashtag = kwargs.pop('hashtag', None)
    assert(not kwargs)
    assert(owner_module)
    if(owner_module.startswith('__') and owner_module.endswith('__')):
        flname = ''
    else:
        assert(not ':' in owner_module)
        flname = '.'.join([owner_module, suffix])
    link = '#'.join([flname, hashtag]) if hashtag else flname
    full_path = path.join(prefix, link) if prefix else link
    return full_path

#EOF
