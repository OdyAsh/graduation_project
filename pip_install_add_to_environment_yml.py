import subprocess
import sys
import yaml

def get_package_name_only(package):
    return package.split('<')[0].split('>')[0].split('=')[0] # Makes sure only the package name is obtained

def get_output_and_version_number(package):
    package = get_package_name_only(package)
    output = subprocess.run(['pip', 'show', package], capture_output=True, text=True)
    try:
        version_number = next((line for line in output.stdout.split('\n') if line.startswith('Version: ')), None)
        if version_number is not None:
            version_number = version_number.split(': ')[1]
    except:
        version_number = None
    return output, version_number

def install_package(package):
    subprocess.run(['pip', 'install', package])

def install_packages_and_update_env(packages):
    installed_packages = []
    for package in packages:
        install_package(package)
        pip_show_output, version_number = get_output_and_version_number(package)
        if version_number is None:
            print(f"the package name \"{package}\" is not correct or found by pip. Installing next package (if any) ...")
            continue
        package = get_package_name_only(package)

        installed_package = f'{package}=={version_number}'
        installed_packages.append(installed_package)
        # Check if the installed package has dependencies
        requires = next((line for line in pip_show_output.stdout.split('\n') if line.startswith('Requires:')), None)
        if requires:
            dependencies = [dependency.strip() for dependency in requires.replace('Requires: ', '').split(',')]
            for dependency in dependencies:
                _, dependency_version = get_output_and_version_number(dependency)
                installed_dependency = f'{dependency}=={dependency_version}'
                installed_packages.append(installed_dependency)

    with open("environment.yml", "r") as f:
        env = yaml.safe_load(f)

    if 'dependencies' not in env:
        env['dependencies'] = []
    if 'pip' not in env['dependencies'][-1]:
        env['dependencies'][-1]['pip'] = []

    env['dependencies'][-1]['pip'] += installed_packages
    env['dependencies'][-1]['pip'] = list(set(env['dependencies'][-1]['pip'])) # remove duplicate entries
    env['dependencies'][-1]['pip'].sort()

    with open('environment.yml', 'w') as f:
        yaml.dump(env, f)

    print(f"Installed/Checked package(s):")
    print(str(packages))

if __name__ == '__main__':
    packages = sys.argv[1:]
    install_packages_and_update_env(packages)
