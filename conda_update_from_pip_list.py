import subprocess
import sys
import yaml


def install_packages(packages):
    installed_packages = []
    for package in packages:
        subprocess.run(['pip', 'install', package], capture_output=True, text=True)
        version_number = get_version_number(package)
        installed_packages.append(f'{package}=={version_number}')
    return installed_packages


def update_environment_file(installed_packages, overwrite=True):
    with open("environment.yml", "r") as f:
        env = yaml.safe_load(f)

    if 'dependencies' not in env:
        env['dependencies'] = []

    if 'pip' not in env['dependencies'][-1]:
        env['dependencies'][-1]['pip'] = []

    if overwrite:
        env['dependencies'][-1]['pip'] = installed_packages
    else:
        for package in installed_packages:
            if package not in env['dependencies'][-1]['pip']:
                env['dependencies'][-1]['pip'].append(package)

    env['dependencies'][-1]['pip'] = sorted(env['dependencies'][-1]['pip'])

    with open('environment.yml', 'w') as f:
        yaml.dump(env, f)


def get_version_number(package):
    version = subprocess.run(['pip', 'show', package], capture_output=True, text=True)
    version_number = next(line for line in version.stdout.split('\n') if line.startswith('Version:')).split(': ')[1]
    return version_number


def get_installed_packages():
    installed_packages = []
    result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
    for line in result.stdout.split('\n')[2:]:
        if not line:
            continue
        package, version = line.split()
        installed_packages.append(f'{package}=={version}')
    return installed_packages


if __name__ == "__main__":
    packages = sys.argv[1:]
    overwrite = "--dont_overwrite" not in sys.argv
    if len(packages) > 0:
        installed_packages = install_packages(packages)
        update_environment_file(installed_packages)

    all_installed_packages = get_installed_packages()
    update_environment_file(all_installed_packages, overwrite)
