#!/usr/bin/env python3
#
# Copyright (c) 2016 Catalyst.net Ltd
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import argparse
import yaml
import time
import subprocess
import shutil
import shlex

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------


def get_args():
    parser = argparse.ArgumentParser(
        description='Continuous deployment documentation system based on Sphinx')
    parser.add_argument('-c', '--config', type=str, help='Configuration file', required=True)
    parser.add_argument('-l', '--log', type=str, help='Write output to a log file',
                        action='store', dest='log_file')
    parser.add_argument('-f', '--force',
                        help='Force creation of fresh virtual environments for all projects \
                                (may help pip solving dependency issues)',
                        action='store_true', dest='venv_refresh')
    args = parser.parse_args()
    return args


def log(*args):
    print(time.strftime("%Y/%m/%d %H:%M:%S  "), end="")
    for a in args:
        print(a, end="")
    print("")


def abort(*args):
    print(time.strftime("%Y/%m/%d %H:%M:%S  "), end="")
    for a in args:
        print(a, end="")
    print("")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Main()
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Parse the command line arguments.
    args = get_args()

    # If output to a log file has been requested (-l), overwrite stdout with the
    # file.
    if args.log_file:
        sys.stdout = open(args.log_file, 'a')

    # Parse the config file.
    with open(args.config, 'r') as f:
        config = yaml.load(f)
        projects = config["projects"]
        docs_config = config["docs-cd"]

    # Try to create home directory if one does not exist yet.
    if not os.path.isdir(docs_config["home"]):
        try:
            os.mkdir(docs_config["home"])
        except:
            log("Could not create project directory at ", docs_config["home"])

    for project in projects:
        switch = None
        # Load project config.
        domain = projects[project]["domain"]
        repository = projects[project]["git"]
        if '-b' in repository:
            switch, branch, repository = shlex.split(repository)
        project_path = docs_config["home"] + "/" + domain
        docs_path = project_path + "/docs"
        venv_path = project_path + "/venv"
        html_path = project_path + "/html"
        log("Working on project ", project, ".")

        # If this is the first time we are running for a given project, then we
        # create the directory for that project and git clone the documentation
        # repository for the first time.
        if not os.path.isdir(project_path):
            try:
                os.mkdir(project_path)
            except Exception as error:
                log("Could not create project directory at ", project_path)
                abort(error)
        os.chdir(project_path)

        # If running for the first time, clone the repository. Otherwise, just
        # pull updates.
        if not os.path.isdir(docs_path):
            try:
                log("Cloning git repository " + repository)
                if switch:
                    subprocess.check_output(["git", "clone", switch, branch, repository, docs_path])
                else:
                    subprocess.check_output(["git", "clone", repository, docs_path])
                os.chdir(docs_path)
            except Exception as error:
                log("Error cloning " + repository + " on " + docs_path)
                abort(error)
        else:
            try:
                os.chdir(docs_path)
                log("Pulling updates from git repository " + repository)
                subprocess.check_output(['git', 'pull'])
            except Exception as error:
                log("Error pulling " + repository + " on " + docs_path)
                abort(error)

        # Identify the latest commit ID (HEAD) of the git repository.
        try:
            head = subprocess.check_output(["git", "rev-parse", "HEAD"])
            head = (head.decode("utf-8")).replace('\n', '')
            log("Last commit ID on the repository is " + head)
        except Exception as error:
            log("Could not fetch HEAD  of " + repository + " on " + docs_path)
            abort(error)

        # Clean up existing virtual environment if the -f (--force) flag has
        # been passed. This could help pip install to resolve dependency
        # issues that are preventing a project from being compiled.
        if args.venv_refresh and os.path.isdir(venv_path):
            log("Forcing clean up of venv " + venv_path)
            subprocess.check_output(["rm", "-rf", venv_path])

        # Compile to documentation in case the latest version (head) has not
        # been compiled yet.
        if not os.path.isdir(html_path + "/" + head):
            # Create a virtual environment for the project, if one does not
            # exist yet.
            if not os.path.isdir(venv_path):
                try:
                    log("Creating a venv ")
                    subprocess.check_output(["virtualenv", "-p", "/usr/bin/python3", venv_path])
                except Exception as error:
                    log("Could not create virtual environment for " + project)
                    abort(error)
            # Activate the virtual environment, install the requirements and
            # compile the documentation. This must be done in one go, because
            # all sub-commands need to run under the same shell and inherit the
            # changes to the environment variables made by virtualenv's activate
            # script.
            #try:
            #    log("Compiling the documentation")
            #    subprocess.check_output(["bash", "-c", "source " + venv_path +
            #                             "/bin/activate && pip install -r "
            #                             + docs_path + "/requirements.txt && make html"])
            try:
                log("Compiling the documentation")
                subprocess.check_output(["bash", "-c", "source " + venv_path +
                                         "/bin/activate && pip install -r "
                                         + docs_path + "/requirements.txt && cd " + docs_path +
                                         " && make html"])
            except Exception as error:
                log("Error compiling documentation for " + project)
                abort(error)
            # Create the project_path/html directory if it doesn't exist.
            if not os.path.isdir(html_path):
                os.mkdir(html_path)
            # Move the latest build to project_path/html/commit_id.
            shutil.move(docs_path + "/build/html", html_path + "/" + head)
        else:
            log("Documentation for " + project + " is already up to date")

        # As a last step, we always clean up old versions of the documentation
        # from all projects, raining only the number defined in the
        # configuration.
        os.chdir(html_path)
        # List all directories under the html_path
        doc_versions = os.listdir(html_path)
        # If the number of version directories identified is higher than the
        # number of versions defined in the configuration, delete versions
        # that should not be retained any longer.
        if len(doc_versions) > docs_config["versions"]:
            versions_to_delete = len(doc_versions) - docs_config["versions"]
            log("Cleaning up " + str(versions_to_delete) +
                " old versions of the documentation from project " + project)
            # Add path to each directory
            doc_versions = [os.path.join(html_path, f) for f in doc_versions]
            # Sort versions by time
            doc_versions.sort(key=lambda x: os.path.getmtime(x))
            # Delete versions older than docs_config["versions"].
            for i in range(versions_to_delete):
                shutil.rmtree(doc_versions[i])
