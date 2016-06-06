#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

external_modules = ['ISO_FORTRAN_ENV', 'ISO_C_BINDING']
external_symbols = ['MPI_COMM_SELF', 'MPI_COMM_NULL', 'MPI_COMM_WORLD']
#=============================================================================
def cache_symbol_lookup(ast, ast_dir, sym_lookup_table, level=-1):

    level += 1
    my_name = ast['name']
    if(my_name in sym_lookup_table):
        return

    my_sym_map = {}
    my_sym_cat = {}
    if verbose(): print '%sCaching: "%s"' % ('  '*level, my_name)

    # consider its own symbols, by category
    if 'publics' in ast:
        my_pubs = [p['name'] for p in ast['publics']]
        for cat in 'functions', 'subroutines', 'interfaces', 'types', 'variables':
            names = set(f['name'] for f in ast[cat])
            for sym in names.intersection(my_pubs):
                my_sym_map[sym] = ':'.join(['__HERE__', sym])
                my_sym_cat[sym] = cat
            # private symbols as well
            for sym in names.difference(my_pubs):
                my_sym_map[sym] = ':'.join(['__PRIV__', sym])
                my_sym_cat[sym] = cat
    else:
        my_pubs = []

    # consider the USE statements
    uses_map = modules_symbols(ast['uses'])
    umap = map_symbol_to_module(ast['uses'])
    for module, imported_syms in uses_map.iteritems():

        if module in external_modules:
            # the AST for external modules is not available!
            for sym in imported_syms:
                assert(sym == imported_syms[sym])
                my_sym_map[sym] = ':'.join([module, sym])

        else:
            if not sym_lookup_table.has_key(module):
                module_file = os.path.join(ast_dir, module.lower()+".ast")
                m = read_ast(module_file, do_doxycheck=False)
                cache_symbol_lookup(m, ast_dir, sym_lookup_table, level)
            assert(module in sym_lookup_table) # TODO redundant

            imported_module_map = sym_lookup_table[module]
            next_sym_map, next_sym_cat = get_sym_map(module, imported_module_map, imported_syms)

            my_sym_map.update(next_sym_map)
            my_sym_cat.update(next_sym_cat)

    symbols_forwarded = process_forwarded(my_name, my_pubs, umap, my_sym_map, sym_lookup_table)

    sym_lookup_table[my_name] = {
        'symbols_map':my_sym_map,
        'symbols_cat':my_sym_cat,
        'umap':umap,
        'symbols_forwarded':symbols_forwarded
    }

#=============================================================================
def get_sym_map(mod_name, mod_map, syms):
    mod_sym_map = mod_map['symbols_map']
    out_map, out_cat = {}, {}
    for sym in syms:
        sym_therein = syms[sym]
        if sym_therein in external_symbols:
            assert(sym_therein == sym)
            out_map[sym] = ':'.join(['__EXTERNAL__', sym])
        else:
            assert(sym_therein in mod_sym_map)
            m, s = mod_sym_map[sym_therein].split(':',1)
            if m == '__HERE__':  # __PRIV__ symbols cannot be reached via USE statements...
                m = mod_name
            out_map[sym] = ':'.join([m, s])
            out_cat[sym] = mod_map['symbols_cat'][sym_therein]

    return out_map, out_cat

#=============================================================================
def process_forwarded(mod_name, pubnames, umap, symmap, sym_lookup_table):

    fwd = {}
    for sym in pubnames:

        if not sym in external_symbols:
            if(not sym in symmap):
                raise Exception('MOD: "%s", SYM: "%s"'%(mod_name, sym))
            m, s = symmap[sym].split(':',1)
            if m != '__HERE__':

                chain = trace_symbol(sym, umap, symmap, sym_lookup_table)
                assert(chain[-1] == symmap[sym])
                if len(chain)>1:
                    fwd[sym] = chain

    return fwd

#=============================================================================
def trace_symbol(sym, umap, symmap, sym_lookup_table):
    assert(sym in umap)

    usym = umap[sym]
    chain = [usym]
    if usym != symmap[sym]:
        used_module, sym_therein = usym.split(':',1)

        next_umap   = sym_lookup_table[used_module]['umap']
        next_symmap = sym_lookup_table[used_module]['symbols_map']
        chain.extend( trace_symbol(sym_therein, next_umap, next_symmap, sym_lookup_table) )

    return chain

#=============================================================================
def modules_symbols(uses):
    """ Convert the 'uses' ast key content (a list of dictionaries)
        to a dictionary with:
        - keys: module names
        - values: for each module a dictionary mapping the internal_symbol_name to external_symbol_name."""
    mmap = {}
    for u in uses:
        module = u['from']
        if('only' in u):
            symbols = u['only']
            mmap.setdefault(module, {}).update(symbols)
    return mmap

#===============================================================================
def reverse_sym_map(symbols_map):
    mmap = {}
    for s in symbols_map:
        module, external_sym = symbols_map[s].split(':')
        mmap.setdefault(module, {}).update({s:external_sym})
    return mmap

#=============================================================================
def map_symbol_to_module(uses):
    """ Convert the 'uses' ast key content (a list of dictionaries)
        to a dictionary with:
        - keys: internal symbol name
        - values: strings of the form "owner_module:external_symbol_name"."""
    d = []
    for u in uses:
        module = u['from']
        if('only' in u):
            symbols = u['only']
            d.extend( zip(symbols.keys(), [':'.join([module, external_sym]) for external_sym in symbols.values()]) )
    return(dict(d))

#===============================================================================
def read_ast(fn_in, wanted=None, category=None, do_doxycheck=True):
    assert(fn_in.endswith(".ast"))
    f = open(fn_in,'ro')
    content = f.read()
    ast = eval(content)
    f.close()

    if(do_doxycheck):
        check_html_in_doxydescr(ast)

    if(wanted):
        # only extract a symbol, but we need to know the category...
        assert(category)
        s = next( (item for item in ast[category] if item['name']==wanted), None )
        assert(s)
        return s

    else:
        return ast

#===============================================================================
def check_html_in_doxydescr(ast):
    for d in traverse_ast(ast, key='descr'):
        descr = d['descr']
        if descr:
            fixed_descr = html_checker(descr)
            if(fixed_descr != descr):
               #print '"%r" "%r"' % (descr, fixed_descr)
                d['descr'] = fixed_descr

#===============================================================================
def html_checker(input_html):

    if(isinstance(input_html, list)):
        fixed_html = []
        for line in input_html:
            fixed_html.append(html_checker(line))
        return fixed_html

    else:
        assert(isinstance(input_html, basestring))
        parser = MyHTMLParser()
        line = input_html + ' '
        parser.feed(line)

        if not parser.errors:
            return input_html

        for error, row, col in reversed(parser.errors):
            assert(row==1)
            if verbose():
                print 'Error %d starting at: %s{%c}%s' %(error, line[:col], line[col], line[col+1:])

            # handle error cases
            if error==1:
                assert(False)
                # Some tag closing missing... No attempt to fix it, a warning is issued...
                fixed_line = line
            elif error==2 or error==3:
                # an ampersand that must be escaped
                fixed_line = line[:col] + '&amp;' + line[col+1:]
            else:
                assert(False) # Unknown error code

            line = fixed_line

        return line.strip()

#===============================================================================
def traverse_ast(o, key, tree_types=(list, tuple)):

    if not o:
        return
    elif isinstance(o, dict):
        if key in o:
            yield o
        next_iterable = o.itervalues()
    elif isinstance(o, tree_types):
        next_iterable = o
    elif isinstance(o, (bool, basestring)):
        return
    else:
        raise Exception(type(o))

    for value in next_iterable:
        for d in traverse_ast(value, key, tree_types):
            yield d

#===============================================================================
def traverse(o, tree_types=(list, tuple)):
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value, tree_types):
                yield subvalue
    else:
        yield o

#===============================================================================
def verbose():
    verbose = os.getenv('VERBOSE')
    if verbose:
        return True

#===============================================================================
from HTMLParser import HTMLParser, HTMLParseError
from htmlentitydefs import entitydefs

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):

    def __init__(self, *args):
        self.last_opened_tag = None
        self.errors = []
        HTMLParser.__init__(self, *args)

    def handle_starttag(self, tag, attrs):
        self.last_opened_tag = tag
        if( verbose() ):
            print "Warning: encountered a start tag '%s'!" % self.get_starttag_text()
            for a in attrs:
                if a: print '\tAttribute:', a

    def handle_endtag(self, tag):
        last_opened_tag = self.get_starttag_text()
        if(not last_opened_tag.startswith("<"+tag)):
            assert(last_opened_tag.startswith("<"+self.last_opened_tag))
            print "Warning: not closing the right tag! About to close '<%s>' while '%s' opened!" % (tag, last_opened_tag)

    def handle_entityref(self, name):
       #if verbose(): print "Encountered an entity  :", name
        if(not name in entitydefs):
            if verbose():
                print "Error: found unknown entity! '%s'" % name
            row, col = self.getpos()
            self.errors.append((2, row, col))

    def handle_data(self, data):
       #print "Encountered some data  :", data
        if('&' in data):
            assert(data == '&')
            if verbose():
                print "Something to be escaped: '%s'" % data
            row, col = self.getpos()
            self.errors.append((3, row, col))

    def handle_charref(name):
        self.error('charref %r'%name)
    def handle_comment(name):
        self.error('comment %r'%name)
    def handle_decl(name):
        self.error('decl %r'%name)
    def handle_pi(name):
        self.error('pi %r'%name)

#EOF
