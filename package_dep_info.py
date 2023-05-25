import argparse
import subprocess
import pprint
import json
import sys

def add_dependencies(cur_package_dict:dict, parent_packages=[]):
    global package_name_to_reqs, package_name_to_req_by, deep_reqs, deep_req_by

    cur_package_name = cur_package_dict['package_name']
    # managing logic of packages required by cur package
    if cur_package_name not in package_name_to_req_by.keys():
        package_name_to_req_by[cur_package_name] = []
    if len(parent_packages) > 0:
        if deep_req_by:
            package_name_to_req_by[cur_package_name].extend(parent_packages)
        else:
            package_name_to_req_by[cur_package_name].append(parent_packages)

    # managing logic of packages that cur package requires (i.e., dependencies of current package)
    if cur_package_name in package_name_to_reqs.keys():
        return package_name_to_reqs[cur_package_name]
    if len(cur_package_dict['dependencies']) == 0:
        package_name_to_reqs[cur_package_name] = []
        return []
    
    # setting deps. of cur package to top level packages
    top_level_deps = [dep_package_dict['package_name'] for dep_package_dict in cur_package_dict['dependencies']]
    package_name_to_reqs[cur_package_name] = top_level_deps

    if deep_req_by:
        child_will_be_req_by = [cur_package_name] + parent_packages
    else:
        child_will_be_req_by = cur_package_name

    for dependency in cur_package_dict['dependencies']:
        # recursively adding top level deps' deps if deep_reqs is True, otherwise, just execute req_by and reqs logic on next child (i.e., dependency)
        if deep_reqs:
            package_name_to_reqs[cur_package_name].extend(add_dependencies(dependency, child_will_be_req_by))
        else:
            add_dependencies(dependency, child_will_be_req_by)

    # all return statements of this function are useful only if deep_reqs is set to true        
    return top_level_deps


def get_pip_package_list():
    command = ['mamba', 'list']
    result = subprocess.run(command, capture_output=True, text=True)
    output_lines = result.stdout.strip().split('\n')[2:]  # Remove header rows

    package_list = []
    for line in output_lines:
        if line.count('pypi') >= 2:
            package_name = line.split()[0]
            package_list.append(package_name)

    return package_list

# draft: use this function if you want to delete packages one by one (from top level to unused dependencies)
def uninstall_package_sequentially(package_name, first_time=True):
    global pip_packages_installed, pkg_inst_mentioned, package_name_to_reqs, package_name_to_req_by
    if not pkg_inst_mentioned or package_name in pip_packages_installed:
        command = ['pip', 'uninstall', package_name]
    else:
        command = ['mamba', 'uninstall', package_name]
    subprocess.run(command)
    if first_time:
        print('\nattempting to uninstall related unused dependencies:\n')
        first_time = False

    # recursively uninstall unused dependency packages
    for unused_dep_pkg in [dep_pkg for dep_pkg in package_name_to_reqs[package_name] if len(package_name_to_req_by[dep_pkg]) <= 1]:
        uninstall_package_sequentially(unused_dep_pkg)


def uninstall_package(package_name, first_time=False):
    print(f'attempting to uninstall {package_name} along with its unused dependencies:')
    global pip_packages_installed, pkg_inst_mentioned, package_name_to_reqs, package_name_to_req_by
    pip_descs, mamba_descs = [], []
    unused_dep_pkgs = [dep_pkg for dep_pkg in package_name_to_reqs[package_name] if len(package_name_to_req_by[dep_pkg]) <= 1]

    if len(unused_dep_pkgs) == 0:
        if first_time:
            subprocess.run([('pip' if package_name in pip_packages_installed else 'mamba'), 'uninstall', package_name])
            return
        if package_name in pip_packages_installed:
            pip_descs = [package_name]
        else:
            mamba_descs = [package_name]
        return pip_descs, mamba_descs
    
    for pkg in unused_dep_pkgs:
        pip_child_descs, mamba_child_descs = uninstall_package(pkg)
        pip_descs.extend(pip_child_descs)
        mamba_descs.extend(mamba_child_descs)
    
    if package_name in pip_packages_installed:
        pip_descs = [package_name] + pip_descs
    else:
        mamba_descs = [package_name] + mamba_descs

    if not first_time:
        return pip_descs, mamba_descs
    
    # uninstall recursively obtained unused dependency packages
    print('pip-related packages:')
    print(pip_descs)
    print('mamba-related packages:')
    print(mamba_descs)
    if len(pip_descs) > 0:
        subprocess.run(['pip', 'uninstall', *pip_descs])
    if len(mamba_descs) > 0:
        subprocess.run(['mamba', 'uninstall', *mamba_descs])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--packages', nargs='+', help='passing x package(s) will output x requires/required-by descriptions')
    parser.add_argument('-ld', '--leaves-dependencies', action='store_true', default=False, help='display all leaf packages that don\'t have dependencies')
    parser.add_argument('-lrb', '--leaves-required-by', action='store_true', default=False, help='display all leaf packages which are not required by any packages')
    parser.add_argument('-dd', '--deep-dependencies', action='store_true', default=False, help='recursively output all packages which package(s) requires')
    parser.add_argument('-drb', '--deep-required-by', action='store_true', default=False, help='recursively output all packages which depend on package(s)')
    parser.add_argument('-spi', '--show-package-installer', action='store_true', default=False, help='(slower) in the output, displays the packages installed with pip vs mamba (conda)')
    parser.add_argument('-u', '--uninstall-packages', action='store_true', default=False, help='uninstalls all -p packages \nfrom mamba/pip (if -spi, recommended) \nor pip only (else) \nalong with their unused dependencies \n')
    args = parser.parse_args()
    result = subprocess.run(['pipdeptree', '--json-tree'], capture_output=True, text=True)
    result_json = json.loads(result.stdout)

    # get global variables
    global package_name_to_reqs, package_name_to_req_by, deep_reqs, deep_req_by, pip_packages_installed, pkg_inst_mentioned
    deep_reqs = args.deep_dependencies
    deep_req_by = args.deep_required_by

    pp = pprint.PrettyPrinter(width=80, compact=True, indent=2)

    # Traverse the JSON data recursively to fill in package_name_to_reqs and package_name_to_req_by
    for cur_package_dict in result_json:
        add_dependencies(cur_package_dict)

    if args.show_package_installer:
        pip_packages_installed = get_pip_package_list()
        pkg_inst_mentioned = True
    else:
        pip_packages_installed = []
        pkg_inst_mentioned = False

    if args.leaves_dependencies:
        print('packages with no dependencies:\n')
        pp.pprint([pkg for pkg, val in package_name_to_reqs.items() if len(val) == 0])

    if args.leaves_required_by:
        if args.leaves_dependencies:
            print()
        print('packages not required by other packages:\n')
        pp.pprint([pkg for pkg, val in package_name_to_req_by.items() if len(val) == 0])

    if args.uninstall_packages:
        if not args.packages:
            print('uninstalling all packages not required by any other packages...\n')
            for pkg in [pkg for pkg, val in package_name_to_req_by.items() if len(val) == 0]:
                uninstall_package(pkg, first_time=True)
        else:
            for pkg in args.packages:
                uninstall_package(pkg, first_time=True)
    
    if not args.packages or args.uninstall_packages:
        return

    for package_name in args.packages:
        inst_from = 'pip' if package_name in pip_packages_installed else 'mamba/conda'
        print(f'package name{f" (installed via {inst_from})" if args.show_package_installer else ""}: ', package_name)
        print()

        print('*****required by:*****')
        if args.show_package_installer is False:
            pp.pprint(package_name_to_req_by[package_name])
        else:
            print('pip installed:')
            pp.pprint([pkg for pkg in package_name_to_req_by[package_name] if pkg in pip_packages_installed])
            print('mamba/conda installed:')
            pp.pprint([pkg for pkg in package_name_to_req_by[package_name] if pkg not in pip_packages_installed])
        print()

        print('*****dependencies:*****')
        if args.show_package_installer is False:
            pp.pprint(package_name_to_reqs[package_name])
        else:
            print('pip installed:')
            pp.pprint([pkg for pkg in package_name_to_reqs[package_name] if pkg in pip_packages_installed])
            print('mamba/conda installed:')
            pp.pprint([pkg for pkg in package_name_to_reqs[package_name] if pkg not in pip_packages_installed])
        print()

        print('*****dependencies not required by other packages:*****')
        if args.show_package_installer is False:
            pp.pprint([pkg for pkg in package_name_to_reqs[package_name] if len(package_name_to_req_by[pkg]) <= 1])
        else:
            print('pip installed:')
            pp.pprint([pkg for pkg in package_name_to_reqs[package_name] if len(package_name_to_req_by[pkg]) <= 1 and pkg in pip_packages_installed])
            print('mamba/conda installed:')
            pp.pprint([pkg for pkg in package_name_to_reqs[package_name] if len(package_name_to_req_by[pkg]) <= 1 and pkg not in pip_packages_installed])
        print()

        print()

if __name__ == "__main__":
    # global variables
    package_name_to_reqs = dict()
    package_name_to_req_by = dict()
    deep_reqs = None
    deep_req_by = None
    pip_packages_installed = []
    pkg_inst_mentioned = False

    main()
    

    