#!/bin/ksh
# postinst script for wazuh-agent
# Wazuh, Inc 2015-2020

OSSEC_HIDS_TMP_DIR="/tmp/wazuh-agent"
DIR="/var/ossec"

# Restore the ossec.confs, client.keys and local_internal_options
if [ -f ${OSSEC_HIDS_TMP_DIR}/client.keys ]; then
    cp ${OSSEC_HIDS_TMP_DIR}/client.keys ${DIR}/etc/client.keys
fi
# Restore ossec.conf configuration
if [ -f ${OSSEC_HIDS_TMP_DIR}/ossec.conf ]; then
    mv ${OSSEC_HIDS_TMP_DIR}/ossec.conf ${DIR}/etc/ossec.conf
    chmod 640 ${DIR}/etc/ossec.conf
fi
# Restore client.keys configuration
if [ -f ${OSSEC_HIDS_TMP_DIR}/local_internal_options.conf ]; then
    mv ${OSSEC_HIDS_TMP_DIR}/local_internal_options.conf ${DIR}/etc/local_internal_options.conf
fi

# logrotate configuration file
if [ -d /etc/logrotate.d/ ]; then
    if [ -e /etc/logrotate.d/wazuh-hids ]; then
        rm -f /etc/logrotate.d/wazuh-hids
    fi
    cp -p ${DIR}/etc/logrotate.d/wazuh-hids /etc/logrotate.d/wazuh-hids
    chmod 644 /etc/logrotate.d/wazuh-hids
    chown root:root /etc/logrotate.d/wazuh-hids
    rm -rf ${DIR}/etc/logrotate.d
fi

# Service
if [ -f /etc/init.d/wazuh-agent ]; then
        /etc/init.d/wazuh-agent stop > /dev/null 2>&1
fi

# Generate ossec-init.conf
${DIR}/installation_scripts/gen_ossec.sh init agent ${DIR} > ${DIR}/etc/ossec-init.conf

# Delete installation_scripts directory
rm -rf ${DIR}/installation_scripts

# Delete tmp directory
if [ -d ${OSSEC_HIDS_TMP_DIR} ]; then
    rm -r ${OSSEC_HIDS_TMP_DIR}
fi
#
#exit 0
