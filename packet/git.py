import json
import os
import subprocess


def get_short_sha(commit_ish: str = "HEAD") -> str:
    """
    Get the short hash of a commit-ish

    Args:
        commit_ish: The commit-ish to get the short hash for.

    Returns:
        The short hash of the commit-ish, or '' if unfound.
    """

    try:
        rev_parse = subprocess.run(
            f"git rev-parse --short {commit_ish}".split(),
            capture_output=True,
            check=True,
        )

        return rev_parse.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""


def get_tag(commit_ish: str = "HEAD") -> str:
    """
    Get the name of the tag at a given commit-ish

    Args:
        commit_ish: The commit-ish to get the tag for.

    Returns:
        The name of the tag at the commit-ish, or '' if untagged.
    """

    try:
        describe = subprocess.run(
            f"git describe --exact-match {commit_ish}".split(),
            capture_output=True,
            check=True,
        )

        return describe.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""


def get_version(commit_ish: str = "HEAD") -> str:
    """
    Get the version string of a commit-ish

    Args:
        commit_ish: The commit-ish to get the version for.

    Returns:
        The version string of the commit-ish, or the version field of package.json if not found.

    Notes:
        If we have a commit and the commit is tagged, version is `tag (commit-sha)`
        If we have a commit but not a tag, version is `commit-sha`
        If we have neither, version is the version field of package.json
    """

    if sha := get_short_sha(commit_ish):
        if tag := get_tag(commit_ish):
            return f"{tag} ({sha})"

        return sha

    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    with open(os.path.join(root_dir, "package.json")) as package_file:
        return json.load(package_file)["version"]


if __name__ == "__main__":
    print(get_version())
