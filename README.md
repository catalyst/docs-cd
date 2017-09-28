Continuous deployment system for Sphinx based documentation.

Docs CD is an extremely simple system to host Sphinx documentation for multiple
projects. It monitors the git repository of your Sphinx projects and
automatically compiles and publishes new versions of the documentation as you
update it.

Docs CD was designed to be deployed on ephemeral cloud instances and easily
load-balanced across multiple compute instances (that can be hosted on different
cloud regions to increase availability).

How does it work?
=================

docs-cd.py
----------

docs-cd.py is a continuous deployment tool that reads the configuration of
documentation projects from an yaml config file and for each project:

  * Clones the documentation sources from a git repository, or pulls updates
    if it is an existing project. The project source code is stored on
    $docs-home/$project/docs.
  * Checks if the documentation changed since the last time it run (based on
    the position of HEAD on the git repository).
  * If the documentation changed, it compiles the documentation again (make
    html). Compiled docs are stored at $docs-home/$project/html/$git-commit.
    The latest successfully compiled version of the documentation is stored at
    $docs-home/$project/docs/build/html.

Directory structure:
  * home: The directory where docs-cd stores all the artifacts it produces.
  * home/project_name: Each project receives its own unique name according to
    its domain name. Docs-cd will store all artifacts for a project under its
    own directory.
  * home/project_name/docs: The documentation git repository is cloned to this
    directory.
  * home/project_name/venv: A python virtual environment is created for each
    project under this directory. This is done so that docs-cd can install the
    specific version of Sphinx, document parsing libraries and theme that the
    documentation requires to be compiled.
  * home/project_name/html: N versions of the compiled documentation are stored
    on this directory. The number of versions preserved is defined by the
    versions parameter. Each version lives under a directory named after the
    commit ID on the git repository.

docs-publish.sh
---------------

docs-publish.sh is a simple script that publishes the latest successful build of
the documentation to its corresponding apache vHost. It does this by creating an
apache vHost config file and updating a symlink that points to the latest
version of the docs.

If a vHost does not exist for a given project, it will be created using
templates/vhost_template.cfg as a template. The "# Require ip" line on the
template is replaced with IP restrictions, if defined on the project
configuration.

Since this script touches /etc/apache2 and reload the apache config, it must be
run as root.

docs-run.sh
-----------

docs-run.sh is just a wrapper that executes docs-cd.py as a regular user and
docs-publish.sh as root (so it can change Apache's vhosts and reload config).

This is the script that you are expected to run as frequently as desirable using
cron or similar. It can also be run manually to update all project docs
immediately.

templates/compile.sh
--------------------

This is a script illustrating how docs-cd compiles your documentation on the
server side.

In order for it to work, you need to make sure that:

* You have a `requirements.txt` file on the root of the documentation project
  with all python packages required to compile your documentation successfully,
  including Sphinx.

* Running `make html` works and outputs the built documentation to "build/".

How to deploy
=============

A sample Ansible playbook to deploy docs-cd on OpenStack is provided under the
`playbook` directory.

Before running the playbook you must adjust the following configuration files:

* playbook/cloud-config.yaml: Defines the variables used by the playbook, such
  as the compute instance name and flavour.

* playbook/cloud-init.yaml: Uses cloud-init to install docs-cd on the target
  compute instance. Please note it assumes Ubuntu 16.04 is the guest operating
  system.

* templates/config.yaml: This file is copied to the target instance and used as
  the configuration file for docs-cd.

To deploy, source your OpenStack variables (`source openrc.sh`) and run the
playbook: `ansible-playbook cloud-config.yaml -i inventory`.

Once docs-cd is deployed, it uses an hourly cronjob to trigger the documentation
builds. If you are in a rush, you can force a build to happen by running
`cd /home/ubuntu/docs-cd && ./docs-run.sh`.
