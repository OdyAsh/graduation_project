import subprocess
import yaml
import argparse


def uninstall_packages(packages):
    for package in packages:
        subprocess.run(['pip', 'uninstall', package]) # output = subprocess.check_output(...)
        # print(output.decode('ascii'))

def remove_packages_from_env_file(packages):
    with open('environment.yml', 'r') as env_file:
        env = yaml.safe_load(env_file)
    for package in packages:
        pip_dep_names = [dep_name for dep_name in env['dependencies'][-1]['pip']]
        pip_dep_names_without_version_num = [dep_name.split('=')[0] for dep_name in pip_dep_names]
        if package in pip_dep_names_without_version_num:
            index = pip_dep_names_without_version_num.index(package)
            env['dependencies'][-1]['pip'].remove(pip_dep_names[index])

    with open('environment.yml', 'w') as env_file:
        yaml.safe_dump(env, env_file, default_flow_style=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('packages', nargs='+')
    args = parser.parse_args()
    
    uninstall_packages(args.packages)
    remove_packages_from_env_file(args.packages)
