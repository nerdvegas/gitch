#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import os
import sys
import subprocess

import requests


logger = logging.getLogger("gitch")
debugging = (os.getenv("GITCH_DEBUG", "").lower() in ("1", "t", "true"))


class GitchError(Exception):
    pass


class SectionNotExistsError(GitchError):
    """A changelog section does not exist."""
    pass


class ReleaseExistsError(GitchError):
    """A Github release already exists."""
    pass


class ChangelogSyncer(object):
    """Sync changelog to github release notes.

    https://developer.github.com/v3/repos/releases/
    """
    def __init__(self, token, path=None, overwrite=False):
        """Create a syncer.

        Args:
            token (str): Github personal access token.
            path (str): Path on disk within target git repo.
            overwrite (bool): If True, overwrite existing gh releases.
        """
        self.token = token
        self.overwrite = overwrite

        self.changelog_filepath = None
        self.github_user = None
        self.github_repo_name = None
        self.changelog_sections = None
        self.gh_releases = None

        path or os.getcwd()

        # find root dir of local git repo checkout
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.PIPE,
                cwd=path
            )
            root_path = out.strip()
        except subprocess.CalledProcessError:
            raise GitchError("Not in a git repository")

        # find changelog
        self.changelog_filepath = os.path.join(root_path, "CHANGELOG.md")
        if not os.path.isfile(self.changelog_filepath):
            raise GitchError("Expected changelog at %s", self.changelog_filepath)

        # Check remote is a github repo, and parse out user and repo name
        # Expecting output like 'git@github.com:nerdvegas/gitch.git'
        #
        out = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.PIPE,
            cwd=path
        )

        # drop leading 'git@' and trailing '.git'
        txt = out.strip().split('@', 1)[-1]
        txt = txt.rsplit('.', 1)[0]
        domain, uri = txt.split(':')

        if domain != "github.com":
            raise GitchError("Not a github repository")

        self.github_user, self.github_repo_name = uri.split('/')

    @property
    def github_url(self):
        return (
            "https://api.github.com/repos/%s/%s"
            % (self.github_user, self.github_repo_name)
        )

    def get_changelog_tags(self):
        """Get tags in changelog, in order they appear.
        """
        sections = self._get_changelog_sections()
        return [x["tag"] for x in sections]

    def sync(self, tag):
        """Sync a changelog section to github release notes.

        Args:
            tag (str): changelog section to sync.
        """
        section = None

        # get changelog section for this tag
        sections = self._get_changelog_sections()
        for sec in sections:
            if sec["tag"] == tag:
                section = sec
                break

        if not section:
            raise SectionNotExistsError(
                "No such tag %r in %s"
                % (tag, self.changelog_filepath)
            )

        # determine if release already exists
        existing_release = None
        for release in self._get_gh_releases():
            if release["tag_name"] == tag:
                existing_release = release

        # avoid overwrite if gh release already exists
        if not self.overwrite and existing_release:
            raise ReleaseExistsError(
                "Github release %r already exists" % tag
            )

        # create the gh release
        data = {
            "tag_name": tag,
            "name": section["header"],
            "body": section["content"]
        }

        if existing_release:
            endpoint = "releases/" + str(existing_release["id"])
            resp = self._send_github_request("PATCH", endpoint, json=data)
        else:
            resp = self._send_github_request("POST", "releases", json=data)

        resp.raise_for_status()
        return resp.json()["html_url"]

    def _get_changelog_sections(self):
        """
        Note that this does very dumb parsing. There don't seem to be good
        solutions to getting AST from markdown in python out there, but we don't
        really need that anyway.
        """
        if self.changelog_sections is not None:
            return self.changelog_sections

        with open(self.changelog_filepath) as f:
            lines = f.read().split('\n')

        sections = []
        curr_tag = None
        curr_header = None
        curr_lines = []

        def consume_section():
            if curr_tag:
                sections.append({
                    "tag": curr_tag,
                    "header": curr_header,
                    "content": '\n'.join(curr_lines).rstrip()
                })

        for line in lines:
            parts = line.split()

            if len(parts) > 1 and parts[0] == "##":  # H2
                consume_section()
                curr_tag = parts[1]
                curr_header = ' '.join(parts[1:])
                curr_lines = []

            elif curr_tag:
                curr_lines.append(line)

        consume_section()

        self.changelog_sections = sections
        return self.changelog_sections

    def _get_gh_releases(self):
        if self.gh_releases is not None:
            return self.gh_releases

        resp = self._send_github_request("GET", "releases")
        resp.raise_for_status()
        self.gh_releases = resp.json()
        return self.gh_releases

    def _send_github_request(self, method, endpoint, **kwargs):
        url = self.github_url + '/' + endpoint
        headers = {
            "Content-Type": "application/json",
            "Authorization": "token " + self.token
        }

        return requests.request(method, url, headers=headers, **kwargs)


def parse_args():
    parser = argparse.ArgumentParser(
        "Sync github release notes with your project's changelog"
    )

    parser.add_argument(
        "-a", "--all", action="store_true",
        help="Sync all tags; TAG is ignored"
    )
    parser.add_argument(
        "-o", "--overwrite", action="store_true",
        help="Overwrite github release if it exists"
    )
    parser.add_argument(
        "-l", "--list", action="store_true",
        help="List tags present in changelog, and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Dry run mode"
    )
    parser.add_argument(
        "TAG", nargs='?',
        help="Tag to sync github release to. If not provided, the latest tag "
        "is used"
    )

    opts = parser.parse_args()

    if opts.TAG and opts.all:
        parser.error("Do not provide TAG with --all option")

    return opts


def error(msg, *nargs):
    print(msg % nargs, file=sys.stderr)
    sys.exit(1)


def init_logging():
    global logger

    formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    if debugging:
        # enable debug-level logging in all packages
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
    else:
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


def sync_to_github(opts, syncer):
    tags_to_sync = []
    changelog_tags = syncer.get_changelog_tags()

    # get list of changelog entries to push to github
    if opts.TAG:
        tags_to_sync = [opts.TAG]

    elif opts.all:
        tags_to_sync = changelog_tags

    elif changelog_tags:  # latest tag
        tags_to_sync = [changelog_tags[0]]

    if not tags_to_sync:
        error("No changelog entries")

    for tag in tags_to_sync:
        logger.info("Syncing %r to github...", tag)

        try:
            url = syncer.sync(tag)
            logger.info("%r synced, see %s", tag, url)
        except ReleaseExistsError:
            logger.warning("Skipped %r, github release already exists" % tag)


def _main():
    init_logging()
    opts = parse_args()

    token = os.getenv("GITCH_GITHUB_TOKEN")
    if not token:
        error("Expected $GITCH_GITHUB_TOKEN")

    syncer = ChangelogSyncer(
        token=token,
        overwrite=opts.overwrite
    )

    # list tags in changelog
    if opts.list:
        tags = syncer.get_changelog_tags()
        if tags:
            for tag in tags:
                print(tag)
        else:
            error("No tags in changelog")

    # sync changelog to github
    else:
        sync_to_github(opts, syncer)


if __name__ == "__main__":
    try:
        _main()
    except GitchError as e:
        if debugging:
            raise
        else:
            error(str(e))
