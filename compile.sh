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

if [ $# -eq 0 ]; then
  echo "No arguments supplied. Please specify the project path."
  exit 1
fi

PROJECT_PATH="$1"

# Activate the virtual environment
if ! [ -f "${PROJECT_PATH}/venv/bin/activate"]; then
  echo "Could not find the virtual environment."
  exit 2
fi
source ${PROJECT_PATH}/venv/bin/activate

# Install the Python requirements on the virtual environment
pip install -r requirements.txt

# Compile the documentation
make html
