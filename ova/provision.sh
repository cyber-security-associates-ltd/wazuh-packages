#/bin/bash
set -exf
# Variables
repo_branch=$(echo "$1" | cut -c1-3)
repo_baseurl=$(echo "$1" | cut -c1-2)
WAZUH_VERSION=$1
ELK_VERSION=$2
STATUS_PACKAGES=$3
DIRECTORY=$4
ELK_MAJOR=`echo ${ELK_VERSION}|cut -d"." -f1`
ELK_MINOR=`echo ${ELK_VERSION}|cut -d"." -f2`
config_files="/var/provision/wazuh-packages/Config_files"

. /var/provision/wazuh-packages/Libraries/wazuh_functions.sh
. /var/provision/wazuh-packages/Libraries/elastic_functions.sh

# Setting wazuh default root password
yes wazuh | passwd root
hostname wazuhmanager

# Ssh config
sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/" /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

# Dependences
yum install openssl -y

curl -so config_files/filebeat.yml https://raw.githubusercontent.com/wazuh/wazuh/v${WAZUH_VERSION}/extensions/filebeat/7.x/filebeat.yml

install_wazuh

elastic_stack_${ELK_MAJOR}

systemctl stop kibana
systemctl stop  elasticsearch
systemctl stop wazuh-manager
systemctl stop wazuh-api
