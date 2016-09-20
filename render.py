#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from makeHTML import newTag, Comment
import re
import utils

missing_description = '...'
separator = ' :: '
ruler = newTag('hr')
back_to_top_char = newTag('b', content="^", attributes={"class":'back_to_top'})
top_link = newTag('div', content=newTag('a', content=back_to_top_char, attributes={"href":"#", "title":"[back to top]"}), attributes={"class":"toplink"})

#=============================================================================
#   M O D U L E   (main rendering function)
#=============================================================================
def render_module(ast, rel_path, ast_dir, prefix, sym_lookup_table):

    # prefetch some info
    mod_name   = ast['name']
    my_name    = mod_name.lower()
    my_file    = my_name + '.F'
    my_role    = ast['tag'].upper()
    my_title   = ' '.join(['Documentation for', my_role, my_name])
    my_publics = set(f['name'] for f in ast['publics'])
    my_descr   = ast['descr'] if ast['descr'] else [missing_description]
    comment    = " ".join([my_role, my_name]).strip()

    # prefetch public symbols names
    pars, types, intfs = (my_publics.intersection(s['name'] for s in ast[cat]) for cat in ('variables', 'types', 'interfaces'))
    all_subs_funs  = ast['subroutines']+ast['functions']
    functs_names = [s['name'] for s in all_subs_funs]
    functs_publics = sorted(my_publics.intersection(functs_names))

    my_symbols_map = sym_lookup_table[mod_name]['symbols_map']
    my_symbols_cat = sym_lookup_table[mod_name]['symbols_cat']

    # ...header
    logo = newTag('img', attributes={"src":'cp2k_apidoc_logo.svg', "alt":'Logo', "class":'logo', "title":"[back to start page]"})
    body_header = newTag('h2', content='Documentation for module')
    body_header.addPart('span', content=my_name, attributes={"class":"symname"})
    body_header.addPart('a', content=logo, attributes={"href":"index.html", "target":"_top"})
    body_parts = [Comment(comment), body_header]

    # ...module description
    body_parts.extend( [newTag('p', content=l) for l in my_descr] )

    # ...link to the source code (@github)
    href = make_external_url(rel_path, file_name=my_file)
    src_link = newTag("a", attributes={"href":href, "target":'_blank', "class":"external_href_nourl"}, content=my_file)
    body_parts.extend(['source:', src_link, ruler])

    # init the queue of refereced private symbols to be printed
    referenced_private_syms = {"TYPES":[], "PARAMS":[]}

    # SUMMARIES...

    # ...forwarded symbols
    forwarded = my_publics.difference(pars, types, intfs, functs_names)
    if forwarded:
        fwded_symbols = render_forwarded(forwarded, my_symbols_map, sym_lookup_table[mod_name]['symbols_forwarded'], sym_lookup_table, ast['uses'])
        if fwded_symbols:
            body_parts.append(fwded_symbols)

    # ...types
    if types:
        summary = types_summary(types, ast['types'])
        body_parts.append(summary)

    # ...interfaces summary (generic procedures)
    if intfs:
        summary, specifics = interfaces_summary(intfs, ast['interfaces'], my_symbols_map)
        if summary:
            summary.addID('interfaces_list')
            body_parts.append(summary)

    # ...subroutines & functions (brief signatures)
    if functs_publics:
        summary = routines_summary(functs_publics, ast['subroutines'], ast['functions'], my_symbols_map, referenced_private_syms)
        summary.addID('routines_list')
        body_parts.append(summary)

    # DETAILED INFO...

    # ...parameters & static vars
    if pars:
        body_parts.append(ruler)
        paramts, statics, other = render_module_vars(ast['variables'], pars)
        if(paramts):
            p = render_parameters(paramts, my_symbols_map, referenced_private_syms)
            p.addID('parameters')
            body_parts.append(p)
        if(statics):
            s = render_staticvars(statics, my_symbols_map, referenced_private_syms)
            s.addID('staticvars')
            body_parts.append(s)
        if(other):
            o = render_othervars(other, my_symbols_map, referenced_private_syms)
            o.addID('othervars')
            body_parts.append(o)

    # ...types
    if types:
        pubtypes = render_types_set('public', types, ast['types'], my_symbols_map, referenced_private_syms, rel_path)
        body_parts.extend([ruler] + pubtypes)

    # ...specific functions for interfaces (compact view)
    if intfs:
        body_parts.append(ruler)
        for sym in sorted(intfs):
            if(sym in specifics): # this is due to explicit interfaces
                iface = render_interface(sym, ast, rel_path, ast_dir, specifics[sym], sym_lookup_table, referenced_private_syms)
                body_parts.append(iface)

    # ...subroutines & functions
    if functs_publics:
        for sym in functs_publics:
            # ... function details
            subr = render_routine(all_subs_funs[functs_names.index(sym)], my_symbols_map, referenced_private_syms, rel_path, ast_dir)
            body_parts.append(subr)

    # ...abstract & explicit interfaces
    if intfs:
        ifaces = render_explicit_interfaces(intfs, ast['interfaces'], my_symbols_map, referenced_private_syms, rel_path, ast_dir)
        body_parts.extend(ifaces)

    # ...specific functions details
    sp_names = []
    if intfs:
        spcf = []
        for sym in sorted(intfs):
            if(sym in specifics): # this is due to explicit interfaces
                my_spcf, my_spnames = render_specifics(sym, specifics[sym], my_symbols_map, referenced_private_syms, all_subs_funs, rel_path, ast_dir)
                spcf.extend(my_spcf)
                sp_names.extend(my_spnames)
        body_parts.extend(spcf)

    # ...private but referenced stuff
    todolists = get_referenced_privates(referenced_private_syms, my_symbols_map, ast, rel_path)
    privates_referenced = sp_names + todolists['PARAMS'] + todolists['TYPES']

    # ...private parameters
    priv_pars = todolists["PARAMS"]
    paramts, statics, other = render_module_vars(ast['variables'], priv_pars)
    assert(not (statics or other))
    prvpars = render_parameters(paramts, my_symbols_map, referenced_private_syms)

    # ...private types
    priv_types = todolists["TYPES"]
    prvtypes = render_types_set('private', priv_types, ast['types'], my_symbols_map, referenced_private_syms, rel_path)

    # ...private parameters & types
    if prvpars or prvtypes:
        body_parts.extend([ruler, newTag('h4', content='private Parameters/Types:')])
        if prvpars: body_parts.append(prvpars)
        body_parts.extend(prvtypes)

    # categories end
    body_parts.append(ruler)

    body = newTag('body', content=body_parts, attributes={
        "onload":"javascript:updateURL('"+my_name+"')",
        "onhashchange":"javascript:updateURLhash('"+my_name+"')",
    })
    return body, privates_referenced

#===============================================================================
#   I N T E R F A C E S   (generic procedures)
#===============================================================================
def render_specifics(ifname, my_specifics, my_symmap, referenced_private_syms, fun_asts, rel_path, ast_dir):
    fnames = [f['name'] for f in fun_asts]
    sp_out, sp_names = [], []
    l2sort = my_specifics.pop('l2sort')
    for spname in l2sort:
        owner_mod, ext_name = my_specifics[spname].split(':')
        if(owner_mod == '__PRIV__'):
            assert(ext_name == spname)
            my_ast = fun_asts[fnames.index(spname)]
            fpriv = render_routine(my_ast, my_symmap, referenced_private_syms, rel_path, ast_dir)
            sp_out.append(fpriv)
            sp_names.append(spname)
        elif(owner_mod == '__HERE__'):
            pass # both the details and the link are already there!
        elif(spname in my_symmap):
            pass # both the details and the link can be found in another html file
        else:
            raise Exception('IFNAME: "%s", SPNAME: "%s", _%r_'%(ifname, spname, my_specifics[spname]))
    return sp_out, sp_names

#===============================================================================
def render_interface(iname, ast, rel_path, ast_dir, specifics, sym_lookup_table, referenced_private_syms):

    inames  = [s['name'] for s in ast['interfaces']]
    my_ast  = ast['interfaces'][inames.index(iname)]
    mod_name = ast['name']
    ext_href = make_external_url(rel_path, beg_end_loci=my_ast['beg_end_loci'])

    my_name = iname.lower()
    comment = " ".join(['INTERFACE', my_name])

    sp, sp_symmap = import_specifics(specifics, ast, ast_dir, sym_lookup_table)

    # tweak attributes to pop the info on INTENT and DIMENSION
    args_list = [s['args'] for s in sp]
    tweak_attrs_inplace(args_list)

    specifics = render_specifics_compact(sp, sp_symmap, sym_lookup_table[mod_name]['symbols_map'], referenced_private_syms, my_name, ast_dir)

    name_span = newTag('span', content=my_name, attributes={"class":"symname"})
    src_link = newTag('a', content=name_span, attributes={"href":ext_href, "target":'_blank'})
    header = newTag('h4', content=['Generic procedure ', src_link, top_link])
    descr = sym_lookup_table[mod_name]['symbols_descr'][iname]
    descr_p = newTag('p', content=descr[0] if descr else missing_description)
    my_body = newTag('div', content=[Comment(comment), header, descr_p, specifics], attributes={"class":'box', "style":'overflow-x:auto;'}, id=my_name)

    return my_body

#===============================================================================
def render_specifics_compact(sp, sp_symmap, symmap, referenced_private_syms, my_name, ast_dir):

    # prefetch some specifics info
    tags, names, args_list = ([s[k] for s in sp] for k in ('tag', 'name', 'args'))
    assert(len(set(tags)) == 1)
    tag = tags.pop()

    # prepare rows for compact view
    l2sort = []; data = {}
    for i, args in enumerate(args_list): # i runs over specifics (columns)
        for j, a in enumerate(args):     # j runs over arguments (rows)
            aname = a['name']
            a['attrs_str'] = ':'.join(sorted(a['attrs']))
            a['name+dim'] = a['name'] + a['dim']
            signature = ':'.join([a[k] for k in 'type', 'intent', 'attrs_str', 'name+dim' if a[k]])
            if signature in l2sort:
                data[signature]['routines'].append(names[i])
            else:
                data[signature] = {'aname':a['name'], 'routines':[names[i]], 'orig_definition':(i,j)}
                name_is_there = next((k for k in reversed(l2sort) if data[k]['aname'] == aname), None)
                if name_is_there:
                    index = l2sort.index(name_is_there)
                    l2sort.insert(index+1, signature)
                else:
                    l2sort.append(signature)

    # merge specifics symmaps with the module's one
    merged_symmap = symmap.copy()
    for my_symmap in sp_symmap:
        merged_symmap.update(my_symmap)

    # table header (specific routines names)
    empty_col = [newTag('th', content='')]
    names_th = []
    for name in names:
        sp_name = name.lower()
        assert(name in symmap)
        owner_mod, ext_sym = symmap[name].split(':')
        if(owner_mod in ('__HERE__', '__PRIV__')):
            assert(name == ext_sym)
            href = '#'+sp_name
        else:
            assert(not re.match('__\w+__',owner_mod))
            href = filename(owner_mod.lower(), hashtag=ext_sym.lower())
        link = newTag('a', content=sp_name, attributes={"href":href})
        rot_div = newTag('div', content=newTag('span', content=link)) # , id=':'.join([my_name, sp_name])
        names_th.append( newTag('th', content=rot_div, attributes={"class":'rotate'}) )
    rows = [newTag('tr', content=empty_col*5 + names_th)]

    # table data (arguments)
    for signature in l2sort:
        my_data = data[signature]
        who_has = my_data['routines']
        i, j = my_data['orig_definition']
        a = args_list[i][j]
        vtype = render_vartype(a['type'], merged_symmap, referenced_private_syms); last = vtype
        cols = []
        cols.append( newTag('td', content=vtype, attributes={"class":'vtype', "style":"text-align:right"}) )

        if a['intent']:
            last.addPiece(',')
            intent = newTag('div', content='INTENT(%s)'%a['intent'].lower(), attributes={"style":'padding-left:1ex;'}, newlines=False)
            content = intent
            last = intent
        else:
            content = ''
        cols.append( newTag('td', content=content, attributes={"class":'misc_attrs', "style":'text-align:left;'}) )

        if a['attrs_str']:
            last.addPiece(',')
            attrs = newTag('div', content=', '.join(a['attrs']), attributes={"style":'padding-left:1ex;'}, newlines=False)
            content = attrs
        else:
            content = ''
        cols.append( newTag('td', content=content, attributes={"class":'misc_attrs', "style":'text-align:left;'}) )

        cols.append( newTag('td', content=separator, attributes={"class":'separee'}) )
        cols.append( newTag('td', content=a['name+dim'].lower(), attributes={"class":'argname', "style":"text-align:left; padding-left:1ex;"}) )
        for name in names:
            content = '&times;' if name in who_has else ''
            cols.append( newTag('td', content=content) )
        rows.append( newTag('tr', content=cols, attributes={"class":'alternating'}) )

    table = newTag('table', content=rows, attributes={"border":'0', "style":"text-align:center; border-collapse:collapse;"})
    my_body = newTag('div', content=table)
    return my_body

#===============================================================================
def import_specifics(specifics, ast, ast_dir, sym_lookup_table):
    sp, sp_symmap = [], []
    sp_sorting = specifics['l2sort']
    for k in sp_sorting:
        v = specifics[k]
        module, external_sym = v.split(':',1)
        symmap = {}
        if(module == '__HERE__' or module == '__PRIV__'):
            target_ast = ast
        else:
            mfile = path.join(ast_dir, module.lower()+'.ast')
            target_ast = utils.read_ast(mfile, do_doxycheck=False)

            # copy the symmap (and tweak it when it contains symbols local to the imported module!)
            for key, val in sym_lookup_table[module]['symbols_map'].iteritems():
                m, ext_s = val.split(':')
                if m == '__HERE__':
                    symmap[key] = ':'.join([module, ext_s])
                elif m in ('__PRIV__', '__REFERENCED_PRIV__'):
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
            if not 'intent' in arg:
                arg['intent'] = ""
        dim = next((a for a in attrs if a.startswith("DIMENSION(")), "")
        if(dim):
            attrs.remove(dim)
            if(not arg['dim']):
                arg['dim'] = re.match("DIMENSION(\(.+\))$",dim).group(1)

#===============================================================================
def interfaces_summary(names, intfcs, symmap):
    inames = [s['name'] for s in intfcs]

    yes = False
    specifics = {}
    sym_divs = []
    for ifname in sorted(names):
        iface = intfcs[inames.index(ifname)]
        if(iface['task'] == 'overloading'):

            procedures = iface['procedures']
            specifics[ifname] = {'l2sort':procedures}
            items = []
            for specific in procedures:
                specifics[ifname][specific] = symmap[specific]
                sym_name = specific.lower()

                owner_mod, ext_sym = symmap[specific].split(':')
                if(owner_mod in ('__HERE__', '__PRIV__')):
                    href = '#'+sym_name
                else:
                    assert(not re.match('__\w+__',owner_mod))
                    href = filename(owner_mod.lower(), hashtag=ext_sym.lower())

                link = newTag('a', content=sym_name, attributes={"href":href})
                items.append( newTag('div', content=['&#8226;', link], attributes={"style":'padding-left:1em; display:inline;'}) )

            bg_color  = '#f2f2f2' if yes else 'white'
            yes = not yes
            gen_link = newTag('a', content=ifname.lower(), id='_SUMMARY_'+ifname.lower(), attributes={"href":'#'+ifname.lower()})
            generic_sym  = newTag('div', content=gen_link, newlines=False, attributes={"style":'font-weight:bold; padding:5px;'})
            specific_div = newTag('div', content=items, attributes={"class":'ellipsed', "style":'padding-left:5px;'})
            sym_divs.append( newTag('div', content=[generic_sym, specific_div], attributes={"style":'padding:1ex; background-color:'+bg_color}) )

    if sym_divs:
        container = newTag('div', content=sym_divs, attributes={"class":'box', "style":'font-family:monospace;'})
        body_parts = [newTag('h4', content='Generic procedures:'), container]
        my_body = newTag('div', content=body_parts, attributes={"class":'box', "style":'border:none;'})
    else:
        my_body = None
    return my_body, specifics

#===============================================================================
#   I N T E R F A C E S   (abstract & explicit ones)
#===============================================================================
def render_explicit_interfaces(names, intfcs, symmap, referenced_private_syms, rel_path, ast_dir):
    inames = [s['name'] for s in intfcs]
    divs = []
    # abstract ones
    for ifname in sorted(names):
        iface = intfcs[inames.index(ifname)]
        if(iface['task'] == 'abstract_interface'):
            ast = iface['procedures'][0]
            divs.append(render_routine(ast, symmap, referenced_private_syms, rel_path, ast_dir))
            divs[-1].pieces.insert(0, 'Abstract interface')
    # explicit ones
    for ifname in sorted(names):
        iface = intfcs[inames.index(ifname)]
        if(iface['task'] == 'explicit_interface'):
            assert(len(iface['procedures']))
            ast = iface['procedures'][0]
            div = render_routine(ast, symmap, referenced_private_syms, rel_path, ast_dir)
            target_name = div.popID()
            div.addID(ifname.lower())
            div.pieces.insert(0, 'Explicit interface to '+target_name)
            divs.append(div)
    if divs:
        divs.insert(0, newTag('h5', content="Abstract/Explicit interfaces", id='explicit_interfaces'))
    return divs

#===============================================================================
#   S U B R O U T I N E S   and   F U N C T I O N S
#===============================================================================
def routines_summary(names, subs, funs, symmap, referenced_private_syms):
    snames = [s['name'] for s in subs]
    fnames = [s['name'] for s in funs]

    # symbols list
    sym_divs = []
    for i, sym in enumerate(names):
        my_ast = subs[snames.index(sym)] if sym in snames else funs[fnames.index(sym)]

        preattrs  = ' '.join(my_ast['attrs']+[''])
        retval    = my_ast['retval']['type'] if my_ast['retval'] else ''
        tag       = my_ast['tag'].upper() + ' '
        sym_name  = sym.lower()
        arglist   = [a['name'].lower() for a in my_ast['args']]
        postattrs = ' '.join(my_ast['post_attrs']) if 'post_attrs' in my_ast else ''
        descr     = '. '.join(my_ast['descr']) if my_ast['descr'] else missing_description
        bg_color  = '#f2f2f2' if i%2==1 else 'white'
        attrs     = ' '.join([preattrs, postattrs]).strip()

        if retval or attrs:
            if retval and attrs:
                retval_type = render_vartype(retval, symmap, referenced_private_syms)
                retval_type.addPieces([' ', attrs])
                tooltiptext = newTag('span', content=retval_type)
            elif retval:
                tooltiptext = newTag('span', content=render_vartype(retval, symmap, referenced_private_syms))
            elif attrs:
                tooltiptext = newTag('span', content=attrs)
            tooltiptext.addAttributes({"class":'tooltiptext', "style":'font-style:oblique;'})
            tooltip = newTag('div', content=[tag, tooltiptext], attributes={"class":'tooltip'})
        else:
            tooltip = newTag('div', content=tag, attributes={"style":'display:inline-block;'})
        div_pieces = [tooltip, ' ', newTag('a', content=sym_name, id='_SUMMARY_'+sym_name, attributes={"href":'#'+sym_name}), ' ']

        if(arglist):
            div_pieces.append('(')
            for arg in arglist:
                a_attributes = {"href":'#'+sym_name, "onclick":"javascript:highlightArgument('"+':'.join([sym_name, arg])+"')"}
                arg_attrs = my_ast['args'][arglist.index(arg)]['attrs']
                if 'OPTIONAL' in arg_attrs:
                    a_attributes["class"] = 'optional_argument'
                div_pieces.extend( [newTag('a', content=arg, attributes=a_attributes), ', '] )
            assert(div_pieces.pop() == ', ')
            div_pieces.append(')')

        f_signature = newTag('div', content=div_pieces, attributes={"class":'ellipsed ellipsed_arglist', "style":'font-weight:bold; padding:5px;'}, newlines=False)
        description = newTag('div', content=newTag('span', content=descr), attributes={"class":'ellipsed', "style":'padding-left:5px;'})

        sym_divs.append( newTag('div', content=[f_signature, description], attributes={"style":'padding:1ex; background-color:'+bg_color}) )

    container = newTag('div', content=sym_divs, attributes={"class":'box', "style":'font-family:monospace;'})

    body_parts = [newTag('h4', content='public Subroutines/Functions:'), container]
    my_body = newTag('div', content=body_parts, attributes={"class":'box', "style":'border:none;'})
    return my_body

#===============================================================================
def render_routine(subr, module_symmap, referenced_private_syms, rel_path, ast_dir):

    # fetch routine's info
    my_name    = subr['name'].lower()
    my_role    = subr['tag'].upper()
    pre_attrs  = " ".join(subr['attrs'])
    post_attrs = " ".join(subr['post_attrs']) if 'post_attrs' in subr else ''
    my_arglist = [arg['name'] for arg in subr['args']]
    my_args    = '(' + ", ".join(my_arglist).lower() + ')'
    my_retval  = subr['retval']
    my_title   = ' '.join(['DBCSR', my_role, my_name])
    my_descr   = subr['descr'] if subr['descr'] else [missing_description]

    comment = " ".join([pre_attrs, my_role, my_name, my_args, post_attrs]).strip()
    if(my_retval and subr['name']!=my_retval['name']):
        comment += " RESULT(%s)"%my_retval['name'].lower()

    if subr['uses']:
        # TODO: tweak cache_symbol_lookup to process also these USEs statements
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
   #agroups = group_arguments(subr['args'])

    # heading
    head_pfx = ' '.join([pre_attrs, my_role])
    ext_href = make_external_url(rel_path, beg_end_loci=subr['beg_end_loci'])
    name_span = newTag('span', content=my_name, attributes={"class":"symname"})
    src_link = newTag('a', content=name_span, attributes={"href":ext_href, "target":'_blank'})
    args_span = newTag('span', content=my_args, attributes={"class":'argname'})
    body_header = newTag('h4', content=[head_pfx, src_link, args_span], newlines=False)
    if(post_attrs):
        body_header.addPart('span', content=post_attrs, attributes={"class":'argname'})
    body_header.addPiece(top_link)

    body_parts = [Comment(comment), body_header]

    # routine description
    body_parts.extend( [newTag('p', content=l) for l in my_descr] )

    # return value (if function)
    if(my_retval):
        r = newTag('tr')
        dh = newTag('table', attributes={"class":'argdescrheading'})
        dt = newTag('dt')
        d = newTag('dl', attributes={"class":'argsdescr'})
        dh.addPiece(r)
        dt.addPiece(dh)
        d.addPiece(dt)
        body_parts.append(d)

        r.addPart('td', content='Return Value')
        r.addPart('td', content=separator, attributes={"class":'separee'})
        r.addPart('td', content=render_vartype(my_retval['type'], my_symbols_map, referenced_private_syms), attributes={"class":'vtype'})
        d.addPart('dd', content=my_retval['descr'], attributes={"class":'argdescr'})

    # arguments description
    if(subr['args']):

        if '__grouped_args_descr__' in subr:
            for group in subr['__grouped_args_descr__']:
                for aname in group['grouped_args']:
                    # just copy the description into all the arguments of this group
                    a = subr['args'][my_arglist.index(aname)]
                    assert(not a['descr'])
                    a['descr'] = group['descr']

        tweak_attrs_inplace([subr['args']])
        rows = []
        for a in subr['args']:
            my_attrs = ", ".join(a['attrs'])
            my_intnt = a['intent'].lower()
            aname = a['name'].lower()
            adim  = (a['dim'] or '').lower()
            descr = a['descr'] if a['descr'] else missing_description

            r = newTag('tr', attributes={"style":'font-family:courier;'})
            vtype = render_vartype(a['type'], my_symbols_map, referenced_private_syms)
            r.addPart('td', content=vtype, attributes={"class":'vtype'})
            last  = vtype
            if my_intnt:
                last.addPiece(',')
                intent = newTag('div', content='INTENT(%s)'%my_intnt, attributes={"style":'padding-left:1ex;'}, newlines=False)
                r.addPart('td', content=intent)
                last = intent
            else:
                r.addPart('td', content='')
            if my_attrs:
                last.addPiece(',')
                attrs = newTag('div', content=my_attrs, attributes={"style":'padding-left:1ex;'})
                r.addPart('td', content=attrs)
            else:
                r.addPart('td', content='')
            r.addPart('td', content=separator, attributes={"class":'separee'})
            r.addPart('td', content=newTag('span', content=aname+adim, id=':'.join([my_name, aname])))

            r.addPart('td', content=descr, attributes={"style":'padding-left:2em; font-family:Liberation Serif;'})
            rows.append(r)

        t = newTag('table', content=rows, attributes={"style":'border:0px'})
        body_parts.extend( [newTag('h5', content='Arguments:'), t] )

    my_body = newTag('div', content=body_parts, id=my_name, attributes={"class":'box'})
    return my_body

#===============================================================================
#   P A R A M E T E R S   or   S T A T I C   V A R I A B L E S
#===============================================================================
def render_module_vars(variables, vpublics):
    # 'variables' can be only static variables or parameters
    vnlist = [v['name'] for v in variables]
    paramts, statics, other = [], [], []
    for vname in vpublics:
        v = variables[vnlist.index(vname)]
        if('PARAMETER' in v['attrs']):
            assert(not 'SAVE' in v['attrs'])
            paramts.append(v)
        elif('SAVE' in v['attrs']):
            assert(not 'PARAMETER' in v['attrs'])
            statics.append(v)
        else:
            other.append(v)

    return paramts, statics, other

#===============================================================================
def render_parameters(paramts, my_symbols_map, referenced_private_syms, hint='PARAMETER'):
    names = [v['name'] for v in paramts]
    rows = []
    for sym in sorted(names):

        assert(sym in my_symbols_map)
        owner_mod, ext_sym = my_symbols_map[sym].split(':')

        if owner_mod in ('__HERE__', '__REFERENCED_PRIV__'):
            v = paramts[names.index(sym)]
            sym_name = sym.lower()

            attrs  = v['attrs'][:]
            if hint:
                attrs.remove(hint)
            for vis in 'PUBLIC', 'PRIVATE':
                if vis in attrs:
                    attrs.remove(vis)
            dim = next((a for a in attrs if a.startswith("DIMENSION(")), "")
            if(dim):
                assert(v['dim'])
                attrs.remove(dim)
            last_attr = attrs.pop() if attrs else ""

            v_name = sym_name + v['dim']
            if 'init' in v:
                v_name += ' = ' + v['init'][1:].lower()
            v_type = render_vartype(v['type'], my_symbols_map, referenced_private_syms)

            td = newTag('td', content=v_type, attributes={"class":'vtype'})
            row = newTag('tr', content=td, attributes={"class":'alternating'})
            if last_attr:
                assert(last_attr in ('POINTER', 'TARGET', 'ALLOCATABLE'))
                assert(hint!='PARAMETER')
                assert(not attrs)
                v_type.addPiece(',')
                row.addPart('td', content=last_attr, attributes={"style":'padding-left:1ex;', "class":'misc_attrs'})
            else:
                row.addPart('td', content='')
            row.addPart('td', content=separator, attributes={"class":'separee'})
            row.addPart('td', content=v_name, id=sym_name, attributes={"class":"parname"})
            rows.append(row)
        else:
            raise Exception('"%s"'%my_symbols_map[sym])

    if rows:
        what = 'Other:'
        if(hint):
            what = 'Parameters:' if hint=='PARAMETER' else 'Module variables:'
        heading = newTag('h4', content=what)
        table = newTag('table', content=rows, attributes={"class":"arglist"})
        html = newTag('div', content=[heading, table], attributes={"class":"box", "style":'overflow:auto;'})
        return html

#===============================================================================
def render_staticvars(*args):
    return render_parameters(*args, hint='SAVE')

#===============================================================================
def render_othervars(*args):
    return render_parameters(*args, hint=None)

#===============================================================================
#   T Y P E S
#===============================================================================
def types_summary(typenames, ast):
    alltypenames = [t['name'] for t in ast]
    sym_divs = []
    for i, sym in enumerate(typenames):
        t = ast[alltypenames.index(sym)]
        assert(sym == t['name'])
        my_descr = t['descr'] if t['descr'] else missing_description
        link = newTag('a', content=sym.lower(), id='_SUMMARY_'+sym.lower(), attributes={"href":'#'+sym.lower()})

        bg_color  = '#f2f2f2' if i%2==1 else 'white'
        type_div  = newTag('div', content=link, newlines=False, attributes={"style":'font-weight:bold; padding:5px;'})
        descr_div = newTag('div', content=newTag('span', content=my_descr), attributes={"class":'ellipsed', "style":'padding-left:5px;'})
        sym_divs.append( newTag('div', content=[type_div, descr_div], attributes={"style":'padding:1ex; background-color:'+bg_color}) )

    container = newTag('div', content=sym_divs, attributes={"class":'box', "style":'font-family:monospace;'})
    body_parts = [newTag('h4', content='public Types:'), container]
    my_body = newTag('div', content=body_parts, attributes={"class":'box', "style":'border:none;'})
    return my_body

#===============================================================================
def render_types_set(tag, names, ast, my_symbols_map, referenced_private_syms, rel_path):
    type_names = [s['name'] for s in ast]

    t_pieces = []
    for sym in sorted(names):

        assert(sym in my_symbols_map)
        owner_mod, ext_sym = my_symbols_map[sym].split(':')
        if owner_mod in ('__HERE__', '__REFERENCED_PRIV__'):
            my_ast = ast[type_names.index(sym)]
            t = render_type(my_ast, my_symbols_map, referenced_private_syms, rel_path)
            box = newTag('div', content=t, id=sym.lower(), attributes={"class":'box'})
            t_pieces.append( box )
        elif owner_mod == '__PRIV__':
            pass
        else:
            raise Exception('"%s"'%my_symbols_map[sym])

    if t_pieces:
        t_pieces.insert(0, newTag('h5', content=tag+" Types:", id='types_'+tag))
    return t_pieces

#===============================================================================
def render_type(tp, my_symbols_map, referenced_private_syms, rel_path):
    my_name = tp['name'].lower()
    my_descr = tp['descr'] if tp['descr'] else missing_description
    my_attrs = tp['attrs'] if 'attrs' in tp else ""
    comment = " ".join([tp['tag'].upper(), my_name])

    title = 'TYPE'
    if my_attrs:
        assert(my_attrs=="BIND(C)")
        title += ", " + my_attrs
    title += separator
    name_span = newTag('span', content=my_name, attributes={"class":"symname"})
    ext_href = make_external_url(rel_path, beg_end_loci=tp['beg_end_loci'])
    src_link = newTag('a', content=name_span, attributes={"href":ext_href, "target":'_blank'})
    body_header = newTag('h4', content=[title, src_link, top_link])
    body_parts = [Comment(comment), body_header, newTag('p', content=my_descr)]

    body_parts.append(ruler)
   #body_parts.append(newTag('p', content='Members:'))
    rows = []
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
        v_descr = v['descr'] if v['descr'] else missing_description
        v_type = render_vartype(v['type'], my_symbols_map, referenced_private_syms)
        v_attr = ', '.join(v['attrs'])
        if v_attr:
            v_type.addPiece(',')

        td = newTag('td', content=v_type, attributes={"class":'vtype'}, newlines=False)
        row = newTag('tr', content=td, attributes={"class":'alternating'})
        row.addPart('td', content=v_attr, attributes={"class":'misc_attrs', "style":'white-space:nowrap;'})
        row.addPart('td', content=separator, attributes={"class":'separee'})
        row.addPart('td', content=v_name, attributes={"class":'argname'})
        row.addPart('td', content=v_descr, attributes={"style":'font-family:Liberation Serif; padding-left:2em;'})
        rows.append(row)
    table = newTag('table', content=rows, attributes={"class":'arglist'})
    body_parts.extend([table, ruler])

    my_body = newTag('div', content=body_parts, attributes={ "style":'overflow-x:auto;'})
    return my_body

#===============================================================================
#   U T I L I T I E S
#===============================================================================
external_stuff = {}
def render_vartype(vtype, symmap, referenced_private_syms):
    global external_stuff
    if(not vtype):
        return ''
    var_type, spec = re.match("([A-Z]+)(?:\((.+)\))?", vtype).groups()
    pieces = [var_type]
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
            pieces.append('(')
            for item in inner_split:
                do_href = bool(re.match('\w+$', item)) and item in symmap
                do_href = do_href and (not item.isdigit())
                if do_href:
                    owner_module, remote_sym = symmap[item].split(':')
                    if owner_module in utils.external_modules:
                        external_stuff.setdefault(owner_module.lower(), set()).add(remote_sym.lower())
                    elif owner_module=='__PRIV__':
                        assert(item == remote_sym)
                        symmap[item] = ':'.join(["__REFERENCED_PRIV__", remote_sym])
                        what = "TYPES" if var_type == "TYPE" else "PARAMS"
                        referenced_private_syms[what].append(item)
                    attributes = {"href":filename(owner_module.lower(), hashtag=remote_sym.lower())}
                    if (item != remote_sym):
                        attributes["title"] = "target: "+"::".join([owner_module, remote_sym]).lower()
                    pieces.append(newTag('a', content=item.lower(), attributes=attributes))
                else:
                    pieces.append(item.lower())
            pieces.append(')')
        else:
            pieces.append('('+s_lowcase+')')
    h = newTag('div', content=pieces, newlines=False)
    return h

#===============================================================================
def render_external(prefix):
    for ext_module, symbols in external_stuff.iteritems():

        heading = newTag('h3', content='Symbols from External/Intrinsic module')
        heading.addPiece( newTag('span', content=ext_module.upper(), attributes={"class":"symname"}) )

        items = [ newTag('li', content=sym_name, id=sym_name) for sym_name in sorted(symbols) ]
        sym_list = newTag('ul', content=items, attributes={"style":'list-style-type:square; padding-bottom:1em;'})
        body_parts = [heading, sym_list]
        body = newTag('body', content=body_parts)

        printout(body, prefix, title=ext_module, output_file=ext_module)

#===============================================================================
def render_forwarded(forwarded, my_symbols_map, my_forwardings, sym_lookup_table, uses):

    # precalculate the symbols to be printed
    sym_list = sorted([sym for sym in forwarded if not sym in utils.external_symbols])

    # precalculate external modules involved
    sym_to_mod = utils.map_symbol_to_module(uses)
    todolist = {}
    for sym in sym_list:
        imported_module, remote_sym = sym_to_mod[sym].split(':')
        todolist.setdefault(imported_module, []).append(sym)
    if not todolist:
        return
    used_modules = [u['from'].lower() for u in uses if 'only' in u and u['from'] in todolist]

    mod_divs = []
    for imported_module in used_modules:
        yes = False
        sym_divs = []
        for sym in todolist[imported_module.upper()]:

            # my_forwardings is used only when multiple steps are needed to reach the original location of the symbol
            chain = my_forwardings[sym] if sym in my_forwardings else [my_symbols_map[sym]]
            import_steps = []
            for ring in chain:
                owner_module, remote_sym = ring.lower().split(':')
                href = filename(owner_module, hashtag=remote_sym)
                link = newTag('a', content='::'.join([owner_module, remote_sym]), attributes={"href":href})
                import_steps.append( newTag('div', content=[' &RightArrow; ', link], attributes={"style":'padding-left:1em; display:inline-block;'}) )

            bg_color  = '#f2f2f2' if yes else 'white'
            yes = not yes
            sym_name = sym.lower()
            sym_span = newTag('span', content=sym_name, id=sym_name, attributes={"style":'font-weight:bold;'})
            forwarded_sym  = newTag('div', content=[sym_span]+import_steps, newlines=False, attributes={"style":'padding:5px;'})

            # the last ring in chain gives this (owner_module, remote_sym)
            descr = sym_lookup_table[owner_module.upper()]['symbols_descr'][remote_sym.upper()]
            descr_div = newTag('div', content=descr[0] if descr else missing_description, attributes={"class":'ellipsed', "style":'padding-left:5px;'})

            sym_divs.append( newTag('div', content=[forwarded_sym, descr_div], attributes={"style":'font-family:monospace; padding:1ex; background-color:'+bg_color}) )

        mod_briefs = sym_lookup_table[imported_module.upper()]['description']
        mod_descr = mod_briefs[0] if mod_briefs else missing_description # Only the 1st \brief is retained here
        mod_header = ["from ", newTag('a', content=imported_module, attributes={"href":filename(imported_module), "title":mod_descr}), ":"]
        mod_div = newTag('div', content=mod_header, newlines=False, attributes={"class":'module_in_fwdsyms'})
        mod_divs.append(mod_div); mod_divs.extend(sym_divs)

    container = newTag('div', content=mod_divs, attributes={"class":'box'})
    body_parts = [newTag('h4', content='Forwarded symbols:'), container]
    my_body = newTag('div', content=body_parts, attributes={"class":'box', "style":'border:none;'})
    return my_body

#===============================================================================
def get_referenced_privates(referenced_so_far, my_symbols_map, ast, rel_path):

    referenced = referenced_so_far.copy()
    params_todo, types_todo = [], []

    while( list(utils.traverse(referenced.values())) ):

        #   P A R A M E T E R S

        # select what to process
        priv_pars = [item for item in referenced["PARAMS"] if item not in params_todo]

        # dummy call only to accumulate all the referenced private parameters
        paramts, statics, other = render_module_vars(ast['variables'], priv_pars)
        assert(not (statics or other))
        prvp_div = render_parameters(paramts, my_symbols_map, referenced)

        # update lists
        for item in priv_pars:
            referenced["PARAMS"].remove(item)
            params_todo.append(item)

        #   T Y P E S

        # select what to process
        priv_types = [item for item in referenced["TYPES"] if item not in types_todo]

        # dummy call only to accumulate all the referenced private parameters
        prvt_divs = render_types_set('private', priv_types, ast['types'], my_symbols_map, referenced, rel_path)

        # update lists
        for item in priv_types:
            referenced["TYPES"].remove(item)
            types_todo.append(item)

    todolists = zip(("PARAMS", "TYPES"), [params_todo, types_todo])
    return dict(todolists)

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
#prefix_sourceforge = 'https://sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/src'
prefix_github = 'https://github.com/cp2k/cp2k/blob/master/cp2k/src'
n_lines_cutoff = 20
def make_external_url(rel_path, **kwargs):

    beg_end_loci = kwargs['beg_end_loci'] if 'beg_end_loci' in kwargs else None
    file_name = kwargs['file_name'] if 'file_name' in kwargs else None

    if beg_end_loci:

        # unpack everything from beg_end_loci when provided
        (my_file, beg_line), (my_file_, end_line) = [locus.split(':') for locus in beg_end_loci]

        # build URL with beg_line at least
        url = path.join( path.join(prefix_github, rel_path), my_file )
        url += "#L" + beg_line

        # when number of lines is small enough: end_line as well!
        if my_file==my_file_ and int(end_line)-int(beg_line)+1 <= n_lines_cutoff:
            url += "#L" + end_line

    else:
        assert(file_name)
        url = path.join( path.join(prefix_github, rel_path), file_name )

    return url

#===============================================================================
def printout(body, prefix, mod_name=None, title=None, output_file=None, jscript=None):

    # HTML heading
    head = newTag('head')
    head.addPart('link', attributes={"rel":"stylesheet", "href":"styles.css"})
    head.addPart('link', attributes={"rel":"shortcut icon", "type":"image/png", "href":"favicon.png"})
    if mod_name:
        title = 'Documentation for module '+mod_name
        output_file = mod_name
    else:
        assert(title and output_file)
    head.addPart('title', content=title)
    head.addPart('meta', attributes={"charset":"UTF-8"})

    # jscript when provided
    if jscript:
        if isinstance(jscript, basestring):
            head.addPart('script', content='', attributes={"type":"text/javascript", "src":jscript})
        elif isinstance(jscript, list):
            for script in jscript:
                head.addPart('script', content='', attributes={"type":"text/javascript", "src":script})
        else:
            assert(False)

    # main page
    html = newTag('html', content=[head, body])
    stuff = ["<!DOCTYPE html>", html.make(tab='  ')]
    f = open(filename(output_file, prefix=prefix), 'w' )
    f.write('\n'.join(stuff))
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
