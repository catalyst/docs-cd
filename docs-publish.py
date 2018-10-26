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

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------


def get_args():
    parser = argparse.ArgumentParser(
        description='Continuous deployment documentation system based on Sphinx')
    parser.add_argument('-c', '--config', type=str, help='Configuration file', required=True)
    parser.add_argument('-l', '--log', type=str, help='Write output to a log file',
                        action='store', dest='log_file')
    parser.add_argument('-t', '--vhost-default-template', type=str,
                        help='Apache vHost default template file', required=True)
    parser.add_argument('-s', '--vhost-ssl-template', type=str,
                        help='Apache vHost SSL template file', required=True)
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

    changes = False
    for project in projects:
        # Load project config.
        domain = projects[project]["domain"]
        repository = projects[project]["git"]
        https_required = projects[project]["https"]
        project_path = docs_config["home"] + "/" + domain
        docs_path = project_path + "/docs"
        venv_path = project_path + "/venv"
        html_path = project_path + "/html"
        www_path = docs_config["www-home"] + "/" + domain
        vhost_base_path = "/etc/apache2/sites-available/"
        vhost_base_symlink = "/etc/apache2/sites-enabled/"
        log("Working on project ", project, ".")

        # Create an apache vhost config for this project, if one does not exist yet.
        ssltag = ''
        vhost__templates = [args.vhost_default_template, args.vhost_ssl_template]

        for template in vhost__templates:
            if 'ssl' in template and https_required == 'enabled':
                ssltag = '-ssl'
                # Write new vhost to file.
                vhost_path = vhost_base_path + domain + ssltag + ".conf"
                vhost_symlink = vhost_base_symlink + domain + ssltag + ".conf"
            else:
                vhost_path = vhost_base_path + domain + ssltag + ".conf"
                vhost_symlink = vhost_base_symlink + domain + ssltag + ".conf"

            if not os.path.isfile(vhost_path):
                log("Creating a vhost config for the project")
                # Read vhost template from file.
                with open(template, 'r') as f:
                    vhost_template = f.read()
                    vhost = vhost_template.replace('${SERVER_NAME}', domain)
                    # If IP access restriction has been defined on the config file,
                    # add the "Require ip" rule to the vhost.
                    try:
                        projects[project]["restrict-ip"]
                    except KeyError:
                        pass
                    else:
                        vhost = vhost.replace('# Require ip', "Require ip " +
                                              projects[project]["restrict-ip"])
                    if 'default' in template and https_required == 'enabled':
                        vhost = vhost.replace('# Rewrite', "Rewrite")

                with open(vhost_path, 'w') as f:
                    f.write(vhost)
                changes = True

            # Enable the apache vhost, if not enabled yet.
            if not os.path.islink(vhost_symlink):
                log("Enabling the vhost for the project")
                try:
                    os.symlink(vhost_path, vhost_symlink)
                    changes = True
                except Exception as error:
                    log("Error creating symlink from " + vhost_path + " to " + vhost_symlink)
                    abort(error)

        # Find out the latest successful build of the docs for this project.
        # TODO: make this a function that is re-used on docs-cd.py.
        doc_versions = os.listdir(html_path)
        doc_versions = [os.path.join(html_path, f) for f in doc_versions]
        doc_versions.sort(key=lambda x: os.path.getmtime(x))
        latest_path = doc_versions[-1]
        latest_version = os.path.basename(latest_path)
        log("The latest version of the documentation is " + latest_version)

        # Apache's default config prevents sites being hosted outside /var/www
        # or /user/share. To work around this, a symlink is created pointing to
        # the latest version of the docs stored in the ubuntu user home folder.
        if not os.path.islink(www_path):
            log("Creating symlink to www-home for project " + project)
            try:
                os.symlink(latest_path, www_path)
                changes = True
            except Exception as error:
                log("Error creating symlink from " + latest_path + " to " + www_path)
                abort(error)
        # If the symlink already exists, ensure it is pointing to the lastest
        # successful build of the docs.
        else:
            linked_version = os.path.basename(os.readlink(www_path))
            if linked_version != latest_version:
                log("Updating symlink the latest version of the docs")
                try:
                    os.remove(www_path)
                    os.symlink(latest_path, www_path)
                    changes = True
                except Exception as error:
                    log("Error updating symlink from " + linked_version + " to " + latest_version)
                    abort(error)
            else:
                log("Symlink is up to date (points to the latest build)")

    # Reload apache config if changes were made.
    if changes is True:
        log("Reloading apache config to make the changes effective")
        subprocess.check_output(["service", "apache2", "reload"])
