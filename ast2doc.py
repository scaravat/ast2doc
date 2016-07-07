#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import utils
from landing_page import print_landingPage
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

    # get API symbols & modules
    api = get_api(wanted_api, ast_dir, sym_lookup_table)

    # build a packages tree
    packages = scan_packages(src_dir)
    src_tree = build_tree(packages)

    # module/symbol usage statistics
    statistics = {} # TODO usage_statistics(sym_lookup_table, packages)

    # document all modules public symbols
    modules_lists, modules_description = document_all_modules(packages, ast_dir, out_dir, api, wanted_module, sym_lookup_table)

    # mention external/intrinsic modules
    render_external(out_dir)

    if skip_indices:
        return

    # Landing page
    print_landingPage(out_dir, src_tree, packages, modules_lists, modules_description, statistics, api, sym_lookup_table)

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
                    body = render_module(ast, rel_path, ast_dir, output_dir, sym_lookup_table)
                    printout(body, output_dir, mod_name=mod_name)
    return modules_lists, modules_description

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
