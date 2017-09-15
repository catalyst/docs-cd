#!/bin/bash
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


# Runs a complete deployment now, so you do not have to wait for the cron
# jobs.

# Compile all projects
/home/ubuntu/docs-cd/docs-cd.py -c /home/ubuntu/docs-cd/config.yaml

# Publish all projects
sudo /home/ubuntu/docs-cd/docs-publish.py  -c /home/ubuntu/docs-cd/config.yaml -t /home/ubuntu/docs-cd/vhost_template.cfg -c /home/ubuntu/docs-cd/vhost_template.cfg
