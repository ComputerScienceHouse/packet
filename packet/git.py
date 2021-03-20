import json
import os
import subprocess

def get_short_sha(commit_ish: str = 'HEAD'):
    """
    Get the short hash of a commit-ish
    Returns '' if unfound
    """

    try:
        rev_parse = subprocess.run(f'git rev-parse --short {commit_ish}'.split(), capture_output=True, check=True)
        return rev_parse.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return ''

def get_tag(commit_ish: str = 'HEAD'):
    """
    Get the name of the tag at a given commit-ish
    Returns '' if untagged
    """

    try:
        describe = subprocess.run(f'git describe --exact-match {commit_ish}'.split(), capture_output=True, check=True)
        return describe.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return ''

def get_version(commit_ish: str = 'HEAD'):
    """
    Get the version string of a commit-ish

    If we have a commit and the commit is tagged, version is `tag (commit-sha)`
    If we have a commit but not a tag, version is `commit-sha`
    If we have neither, version is the version field of package.json
    """

    if sha := get_short_sha(commit_ish):
        if tag := get_tag(commit_ish):
            return f'{tag} ({sha})'
        else:
            return sha
    else:
        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        with open(os.path.join(root_dir, 'package.json')) as package_file:
            return json.load(package_file)['version']

if __name__ == '__main__':
    print(get_version())
