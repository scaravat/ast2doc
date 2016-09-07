#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, json
import utils
from landing_page import print_landingPage, print_disambiguationPage, encode_package_name
from render import printout, render_module, render_external, missing_description

#=============================================================================
def main():
    if(len(sys.argv) < 4):
        print("Usage: print_doc.py <src-dir> <ASTs-dir> <HTML-output-dir>")
        sys.exit(1)

    src_dir = sys.argv[1]
    ast_dir = sys.argv[2]
    out_dir = sys.argv[3]
    wanted_api = "dbcsr"

    if(len(sys.argv)>4):
        # single module file mode: no indices generation
        assert(len(sys.argv)==5)
        wanted_module = sys.argv[4]
        skip_indices = True
    else:
        wanted_module = '__ALL__'
        skip_indices = False

    # pre compute the lookup table of imported symbols
    sym_lookup_table = lookup_imported_symbols(ast_dir, wanted_module, wanted_api)

    # dump modules and own publics lists in JSON
    symbols_db = dump_modules_publics(sym_lookup_table, out_dir)

    # get API symbols & modules
    api = get_api(wanted_api, ast_dir, sym_lookup_table)

    # build a packages tree
    packages = scan_packages(src_dir)
    dump_packages_json(packages, out_dir)
    src_tree = build_tree(packages)

    # module/symbol usage statistics
    statistics = usage_statistics(sym_lookup_table, packages)

    # document all modules public symbols
    modules_lists, modules_description, privates_referenced = document_all_modules(packages, ast_dir, out_dir, api, wanted_module, sym_lookup_table)

    # dump private referenced symbols in JSON
    dump_privates_referenced(privates_referenced, out_dir)

    # mention external/intrinsic modules
    render_external(out_dir)

    if skip_indices:
        return

    # Landing page
    print_landingPage(out_dir, src_tree, packages, modules_lists, modules_description, statistics, api, sym_lookup_table)

    # Disambiguation page
    print_disambiguationPage(symbols_db, modules_description, out_dir)

#=============================================================================
def usage_statistics(sym_lookup_table, packages):

    counter = {'__SYMBOLS__':{}, '__MODULES__':{}}
    for module in sym_lookup_table:
        symmap = sym_lookup_table[module]['symbols_map']
        my_used_modules = set()
        for sym, smap in symmap.iteritems():
            ext_mod, ext_sym = smap.split(':')
            if(not ext_mod in ('__PRIV__', '__HERE__', '__EXTERNAL__')):
                my_used_modules.add(ext_mod)
                counter['__SYMBOLS__'].setdefault(smap, 0)
                counter['__SYMBOLS__'][smap] += 1
        for ext_mod in my_used_modules:
            counter['__MODULES__'].setdefault(ext_mod, 0)
            counter['__MODULES__'][ext_mod] += 1

    statistics = {}
    for key in ('__MODULES__', '__SYMBOLS__'):
        statistics[key] = sorted([(k,v) for k,v in counter[key].iteritems() if v>1], key=lambda item: item[1])
        statistics[key].reverse()

    # statistics per package
    pkgfiles = dict( (k, packages[k]['files']) for k in packages.keys() )
    filepkg = {}
    for k, flist in pkgfiles.iteritems():
        filepkg.update( dict( (f[:-2].upper(), k) for f in flist ) )
        statistics[k] = {'__MODULES__':[], '__SYMBOLS__':[]}
    for k in ('__MODULES__', '__SYMBOLS__'):
        for item in statistics[k]:
            mod = item[0].split(':',1)[0] # this works in both k cases!
            if not mod in utils.external_modules:
                pkg = filepkg[mod]
                statistics[pkg][k].append(item)

    return statistics

#=============================================================================
def lookup_imported_symbols(ast_dir, wanted_module, wanted_api):

    sym_lookup_table = {}

    for root, dirs, files in os.walk(ast_dir):
        assert(root == ast_dir)
        assert(not dirs)

        if wanted_module=='__ALL__':
            ast_files = [f for f in files if f.endswith('.ast')]
        else:
            ast_files = [wanted_module + '.ast', wanted_api + '_api.ast']

        for f in ast_files:
            ast = utils.read_ast(os.path.join(ast_dir, f), do_doxycheck=False)
            utils.cache_symbol_lookup(ast, ast_dir, sym_lookup_table)

    return(sym_lookup_table)

#=============================================================================
def get_api(wanted_api, ast_dir, sym_lookup_table):
    api_file = os.path.join(ast_dir, wanted_api + '_api.ast')
    ast = utils.read_ast(api_file)
    assert(not
       (ast['interfaces'] or
        ast['types'] or
        ast['functions'] or
        ast['subroutines'])
    )

    api_symbols_map = sym_lookup_table[wanted_api.upper()+'_API']['symbols_map']
    api_symbols_cat = sym_lookup_table[wanted_api.upper()+'_API']['symbols_cat']
    api_modules_map = utils.reverse_sym_map(api_symbols_map)

    ast['symbols_cat'] = api_symbols_cat
    ast['symbols_map'] = api_symbols_map
    ast['modules_map'] = api_modules_map

    return(ast)

#=============================================================================
def document_all_modules(packages, ast_dir, output_dir, api, wanted_module, sym_lookup_table):

    src_root = os.path.normpath(os.path.commonprefix(packages.keys()))

    modules_lists = {'__ALL__':[], '__API__':[]}
    modules_description = {}
    privates_referenced = {}
    for d, p in packages.iteritems():
        rel_path = os.path.relpath(d, src_root)
        modules_lists[rel_path] = []
        for f in p['files']:
            mod_name = f.rsplit(".", 1)[0]
            ast_file = os.path.join(ast_dir, mod_name + ".ast")
            if(os.path.isfile(ast_file)):
                ast = utils.read_ast(ast_file)
                if(ast['tag'] == 'module' and (wanted_module=='__ALL__' or wanted_module==mod_name)):
                    if(utils.verbose()): print '>>>> Module: %s [%s]' % (mod_name, rel_path)
                    modules_lists[rel_path].append(mod_name)
                    modules_lists['__ALL__'].append(mod_name)
                    modules_description[mod_name] = ast['descr'][0] if ast['descr'] else missing_description # Only 1st \brief is retained here
                    if(mod_name.upper() in api['modules_map']):
                        modules_lists['__API__'].append(mod_name)
                    body, my_privates_referenced = render_module(ast, rel_path, ast_dir, output_dir, sym_lookup_table)
                    printout(body, output_dir, mod_name=mod_name, jscript=['packages_modules.json', 'js/common.js', 'js/updateURL.js'])
                    if my_privates_referenced:
                        privates_referenced[mod_name.upper()] = my_privates_referenced
    return modules_lists, modules_description, privates_referenced

#=============================================================================
def dump_modules_publics(sym_lookup_table, out_dir):

    # modules DB
    mdump = json.dumps(sym_lookup_table.keys(), sort_keys=True).lower()

    # symbols DB
    syms = {}
    dummy = [syms.setdefault(s, []).append(m) for m in sym_lookup_table for s in sym_lookup_table[m]['my_symbols']]
    sdump = json.dumps(syms).lower()

    f = open(os.path.join(out_dir, 'modules_publics.json'), 'w')
    f.write("modules = '" + mdump + "'\n")
    f.write("symbols = '" + sdump + "'\n")
    f.close()

    return syms

#=============================================================================
def dump_privates_referenced(privates_referenced, out_dir):
    syms = {}
    dummy = [syms.setdefault(s, []).append(m) for m in privates_referenced for s in privates_referenced[m]]
    sdump = json.dumps(privates_referenced).lower()
    f = open(os.path.join(out_dir, 'privates_referenced.json'), 'w')
    f.write("modules_priv_symbols = '" + sdump + "'\n")
    f.write("priv_symbols = '" + json.dumps(syms).lower() + "'\n")
    f.close()

#=============================================================================
def scan_packages(src_dir):
    packages = {}
    for root, dirs, files in os.walk(src_dir):
        if("PACKAGE" in files):
            content = open(os.path.join(root,"PACKAGE")).read()
            package = eval(content)
            package['files'] = [f for f in files if f.endswith(".F")]
            rel_path = os.path.relpath(root, src_dir)
            packages[rel_path] = package
    return(packages)

#=============================================================================
def dump_packages_json(packages, out_dir):

    # packages DB
    pdump = json.dumps([encode_package_name(p) for p in packages], sort_keys=True)

    # modules DB
    mdump = json.dumps(dict( (f[:-2], encode_package_name(p)) for p in packages for f in packages[p]['files'] ))

    f = open(os.path.join(out_dir, 'packages_modules.json'), 'w')
    f.write("packages = '" + pdump + "'\n")
    f.write("modules = '" + mdump + "'\n")
    f.close()

#=============================================================================
def build_tree(packages):

    src_root = os.path.normpath(os.path.commonprefix(packages.keys()))
    tree = Tree(src_root)

    for folder in packages.iterkeys():

        # only include the forlders that have some .F files within
        if(packages[folder]['files']):
            rel_path = os.path.relpath(folder, src_root)
            tree.NewPath(rel_path)

    return(tree)

#=============================================================================
class Tree():

    def __init__(self, root_dir):
        self.tree = {root_dir:{'parent':None, 'children':[]}}
        self.root = root_dir

    def NewPath(self, rel_path):
        parent = self.root
        for me in rel_path.split("/"):
            self.NewNode(me, parent)
            parent = os.path.normpath(os.path.join(parent, me))

    def NewNode(self, me, parent):
        my_id = os.path.normpath(os.path.join(parent, me))
        if(not my_id in self.tree):
            self.tree[my_id] = {'parent':parent, 'children':[]}
            assert(not my_id in self.tree[parent]['children'])
            self.tree[parent]['children'].append(my_id)

    def GetChildren(self, rootnode=None):
        if(not rootnode):
            rootnode = self.root
        return self.tree[rootnode]['children']

    def Print(self, rootnode=None, indent=''):
        if(not rootnode):
            rootnode = self.root
        for d in self.tree[rootnode]['children']:
            me = os.path.split(d)[1]
            print indent + me
            my_indent = indent + " "*len(me)
            self.Print(d,my_indent)

#=============================================================================
if __name__ == '__main__':
    main()

#EOF
