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

# Publishes the documentation deployed by docs-cd.sh by creating and
# configuring apache vhosts for each project.

. /home/ubuntu/docs-cd/docs-common.sh

DOC_PROJECTS=$(curl -s ${CONTAINER})
DOC_HOME="/home/ubuntu"

# Read all objects (documentation projects) from the container and create an
# apache vhost config for each one.
CHANGES=false
for PROJECT in ${DOC_PROJECTS}; do
  # Extract the server name and git repo variables.
  SERVER_NAME="${PROJECT}"
  log "${INFO}" "Checking apache vhost config for $SERVER_NAME"
  # Create a new apache vhost config file, if one does not exist yet.
  if ! [ -f "/etc/apache2/sites-available/${SERVER_NAME}" ]; then
    (cat << EOF
<VirtualHost *:80>
	ServerName ${SERVER_NAME}
	ServerAdmin webmaster@localhost
	DocumentRoot /var/www/${SERVER_NAME}
	ErrorLog \${APACHE_LOG_DIR}/error.log
	CustomLog \${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF
    ) > "/etc/apache2/sites-available/${SERVER_NAME}"
    log "${INFO}" "Create new vhost config /etc/apache2/sites-available/${SERVER_NAME}"
    CHANGES=true
  fi
  # Enable the vhost, if not enabled yet.
  if ! [ -f "/etc/apache2/sites-enabled/${SERVER_NAME}" ]; then
    ln -s "/etc/apache2/sites-available/${SERVER_NAME}" "/etc/apache2/sites-enabled/${SERVER_NAME}"
    log "${INFO}" "Enabled apache site /etc/apache2/sites-enabled/${SERVER_NAME}"
    CHANGES=true
  fi
  # Find out the latest version of the docs for $SERVER_NAME.
  LATEST_BUILD=$(ls -lt "${DOC_HOME}/${SERVER_NAME}/html" | grep "^d" | awk '{print $9}' | head -1)
  # Apache's default config prevents sites being hosted outside /var/www or
  # /user/share. To work around this, a symlink is created pointing to the
  # latest version of the docs stored in the ubuntu user home folder.
  if ! [ -L "/var/www/${SERVER_NAME}" ]; then
    ln -s "${DOC_HOME}/${SERVER_NAME}/html/${LATEST_BUILD}" "/var/www/${SERVER_NAME}"
    log "${INFO}" "Created symlink /var/www/${SERVER_NAME} pointing to build ${LATEST_BUILD}"
    CHANGES=true
  else
    CURRENT_BUILD=$(readlink -f "/var/www/${SERVER_NAME}" | xargs basename)
    if [[ "${CURRENT_BUILD}" != "${LATEST_BUILD}" ]]; then
      rm -rf "/var/www/${SERVER_NAME}"
      ln -s "${DOC_HOME}/${SERVER_NAME}/html/${LATEST_BUILD}" "/var/www/${SERVER_NAME}"
      log "${INFO}" "Updated build for ${SERVER_NAME} from ${CURRENT_BUILD} to ${LATEST_BUILD}"
    else
      log "${INFO}" "${SERVER_NAME} is already on latest build (${LATEST_BUILD})"
    fi
  fi
done

# Reload the apache configuration, so it reflects the updates done.
if [[ "${CHANGES}" == "true" ]]; then
  log "${INFO}" "Reloading apache config to make changes effective"
  service apache2 reload
fi

exit 0
