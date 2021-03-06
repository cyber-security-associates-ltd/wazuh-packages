# Spec file for AIX systems
Name:        wazuh-agent
Version:     3.7.1
Release:     1
License:     GPL
URL:         https://www.wazuh.com/
Vendor:      Wazuh, Inc <info@wazuh.com>
Packager:    Wazuh, Inc <info@wazuh.com>
Summary:     The Wazuh agent, used for threat detection, incident response and integrity monitoring.

Group: System Environment/Daemons
AutoReqProv: no
Source0: %{name}-%{version}.tar.gz
Conflicts: ossec-hids ossec-hids-agent wazuh-manager wazuh-local
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: coreutils automake autoconf libtool

%description
Wazuh is an open source security monitoring solution for threat detection, integrity monitoring, incident response and compliance.

%prep
%setup -q
./gen_ossec.sh init agent %{_localstatedir} > ossec-init.conf
cd src && gmake clean && gmake deps RESOURCES_URL=http://packages.wazuh.com/deps/3.7
gmake TARGET=agent USE_SELINUX=no PREFIX=%{_localstatedir} DISABLE_SHARED=yes DISABLE_SYSC=yes
cd ..

%install
# Clean BUILDROOT
rm -fr %{buildroot}

echo 'USER_LANGUAGE="en"' > ./etc/preloaded-vars.conf
echo 'USER_NO_STOP="y"' >> ./etc/preloaded-vars.conf
echo 'USER_INSTALL_TYPE="agent"' >> ./etc/preloaded-vars.conf
echo 'USER_DIR="%{_localstatedir}"' >> ./etc/preloaded-vars.conf
echo 'USER_DELETE_DIR="y"' >> ./etc/preloaded-vars.conf
echo 'USER_ENABLE_ACTIVE_RESPONSE="y"' >> ./etc/preloaded-vars.conf
echo 'USER_ENABLE_SYSCHECK="y"' >> ./etc/preloaded-vars.conf
echo 'USER_ENABLE_ROOTCHECK="y"' >> ./etc/preloaded-vars.conf
echo 'USER_ENABLE_OPENSCAP="n"' >> ./etc/preloaded-vars.conf
echo 'USER_ENABLE_CISCAT="n"' >> ./etc/preloaded-vars.conf
echo 'USER_UPDATE="n"' >> ./etc/preloaded-vars.conf
echo 'USER_AGENT_SERVER_IP="MANAGER_IP"' >> ./etc/preloaded-vars.conf
echo 'USER_CA_STORE="/path/to/my_cert.pem"' >> ./etc/preloaded-vars.conf
echo 'USER_AUTO_START="n"' >> ./etc/preloaded-vars.conf
DISABLE_SHARED="yes" DISABLE_SYSC="yes" ./install.sh

# Remove unnecessary files or directories
rm -rf %{_localstatedir}/selinux

# Create directories
mkdir -p ${RPM_BUILD_ROOT}%{_init_scripts}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/.ssh

# Copy the files into RPM_BUILD_ROOT directory
install -m 0640 ossec-init.conf ${RPM_BUILD_ROOT}%{_sysconfdir}
install -m 0750 src/init/ossec-hids-aix.init ${RPM_BUILD_ROOT}%{_init_scripts}/wazuh-agent
cp -pr %{_localstatedir}/* ${RPM_BUILD_ROOT}%{_localstatedir}/

# Add configuration scripts
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/
cp gen_ossec.sh ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/
cp add_localfiles.sh ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/

# Support files for dynamic creation of configuraiton file
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/etc/templates/config/generic
cp -pr etc/templates/config/generic/* ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/etc/templates/config/generic
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/etc/templates/config/generic/localfile-logs
cp -pr etc/templates/config/generic/localfile-logs/* ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/etc/templates/config/generic/localfile-logs

# Support scripts for post installation
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/src/init
cp src/init/*.sh ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/src/init

# Add installation scripts
cp src/VERSION ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/src/
cp src/REVISION ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/src/
cp src/LOCATION ${RPM_BUILD_ROOT}%{_localstatedir}/tmp/src/

exit 0

%pre

# Create ossec user and group
if ! grep "^ossec:" /etc/group > /dev/null 2>&1; then
  /usr/bin/mkgroup ossec
fi
if ! grep "^ossec" /etc/passwd > /dev/null 2>&1; then
  /usr/sbin/useradd ossec
  /usr/sbin/usermod -G ossec ossec
fi

# Delete old service
if [ -f /etc/rc.d/init.d/wazuh-agent ]; then
  rm /etc/rc.d/init.d/wazuh-agent
fi

# Remove existent config file and notify user for new installations
if [ $1 = 1 ]; then
  if [ -f %{_localstatedir}/etc/ossec.conf ]; then
    echo "A backup from your ossec.conf has been created at %{_localstatedir}/etc/ossec.conf.rpmorig"
    echo "Please verify your ossec.conf configuration at %{_localstatedir}/etc/ossec.conf"
    mv %{_localstatedir}/etc/ossec.conf %{_localstatedir}/etc/ossec.conf.rpmorig
  fi
fi

# Make a backup copy of the config file for package upgrades
if [ $1 = 2 ]; then
  cp -rp %{_localstatedir}/etc/ossec.conf %{_localstatedir}/etc/ossec.bck
fi

%post
# New installations
if [ $1 = 1 ]; then

  # Generating ossec.conf file
  . %{_localstatedir}/tmp/src/init/dist-detect.sh
  %{_localstatedir}/tmp/gen_ossec.sh conf agent ${DIST_NAME} ${DIST_VER}.${DIST_SUBVER} %{_localstatedir} > %{_localstatedir}/etc/ossec.conf
  chown root:ossec %{_localstatedir}/etc/ossec.conf
  chmod 0640 %{_localstatedir}/etc/ossec.conf

  # Add default local_files to ossec.conf
  %{_localstatedir}/tmp/add_localfiles.sh %{_localstatedir} >> %{_localstatedir}/etc/ossec.conf

  # Restore Wazuh manager configuration
  if [ -f %{_localstatedir}/etc/ossec.conf.rpmorig ]; then
    %{_localstatedir}/tmp/src/init/replace_manager_ip.sh %{_localstatedir}/etc/ossec.conf.rpmorig %{_localstatedir}/etc/ossec.conf
  fi

  # Fix for AIX: remove syscollector
  sed '/System inventory/,/^$/{/^$/!d;}' %{_localstatedir}/etc/ossec.conf > %{_localstatedir}/etc/ossec.conf.tmp
  mv %{_localstatedir}/etc/ossec.conf.tmp %{_localstatedir}/etc/ossec.conf

  # Fix for AIX: netstat command
  sed 's/netstat -tulpn/nestat -tu/' %{_localstatedir}/etc/ossec.conf > %{_localstatedir}/etc/ossec.conf.tmp
  mv %{_localstatedir}/etc/ossec.conf.tmp %{_localstatedir}/etc/ossec.conf
  sed 's/sort -k 4 -g/sort -n -k 4/' %{_localstatedir}/etc/ossec.conf > %{_localstatedir}/etc/ossec.conf.tmp
  mv %{_localstatedir}/etc/ossec.conf.tmp %{_localstatedir}/etc/ossec.conf

  # Generate the active-responses.log file
  touch %{_localstatedir}/logs/active-responses.log
  chown ossec:ossec %{_localstatedir}/logs/active-responses.log
  chmod 0660 %{_localstatedir}/logs/active-responses.log
fi

rm -rf %{_localstatedir}/tmp/etc
rm -rf %{_localstatedir}/tmp/src
rm -f %{_localstatedir}/tmp/add_localfiles.sh


# Restart wazuh-agent when manager settings are in place
if grep '<server-ip>.*</server-ip>' %{_localstatedir}/etc/ossec.conf | grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$' > /dev/null 2>&1; then
  /etc/rc.d/init.d/wazuh-agent restart > /dev/null 2>&1 || :
fi
if grep '<server-hostname>.*</server-hostname>' %{_localstatedir}/etc/ossec.conf > /dev/null 2>&1; then
  /etc/rc.d/init.d/wazuh-agent restart > /dev/null 2>&1 || :
fi
if grep '<address>.*</address>' %{_localstatedir}/etc/ossec.conf | grep -v 'MANAGER_IP' > /dev/null 2>&1; then
  /etc/rc.d/init.d/wazuh-agent restart > /dev/null 2>&1 || :
fi


%preun

if [ $1 = 0 ]; then
  /etc/rc.d/init.d/wazuh-agent stop > /dev/null 2>&1 || :
fi


%postun

# Remove ossec user and group
if [ $1 == 0 ];then
  if grep "^ossec" /etc/passwd > /dev/null 2>&1; then
    userdel ossec
  fi
  if grep "^ossec:" /etc/group > /dev/null 2>&1; then
    rmgroup ossec
  fi
fi


%clean
rm -fr %{buildroot}

%files
%{_init_scripts}/*
%attr(640,root,ossec) %verify(not md5 size mtime) %{_sysconfdir}/ossec-init.conf

%dir %attr(750,root,ossec) %{_localstatedir}
%attr(750,root,ossec) %{_localstatedir}/agentless
%dir %attr(700,root,ossec) %{_localstatedir}/.ssh
%dir %attr(750,root,ossec) %{_localstatedir}/active-response
%dir %attr(750,root,ossec) %{_localstatedir}/active-response/bin
%attr(750,root,ossec) %{_localstatedir}/active-response/bin/*
%dir %attr(750,root,system) %{_localstatedir}/bin
%attr(750,root,system) %{_localstatedir}/bin/*
%dir %attr(750,root,ossec) %{_localstatedir}/backup
%dir %attr(770,ossec,ossec) %{_localstatedir}/etc
%attr(640,root,ossec) %config(noreplace) %{_localstatedir}/etc/client.keys
%attr(640,root,ossec) %{_localstatedir}/etc/internal_options*
%attr(640,root,ossec) %config(noreplace) %{_localstatedir}/etc/local_internal_options.conf
%attr(640,root,ossec) %config(noreplace) %{_localstatedir}/etc/ossec.conf
%{_localstatedir}/etc/ossec-init.conf
%attr(640,root,ossec) %{_localstatedir}/etc/wpk_root.pem
%dir %attr(770,root,ossec) %{_localstatedir}/etc/shared
%attr(660,root,ossec) %config(missingok,noreplace) %{_localstatedir}/etc/shared/*
%dir %attr(750,root,system) %{_localstatedir}/lib
%dir %attr(770,ossec,ossec) %{_localstatedir}/logs
%attr(660,ossec,ossec) %ghost %{_localstatedir}/logs/active-responses.log
%attr(660,root,ossec) %ghost %{_localstatedir}/logs/ossec.log
%attr(660,root,ossec) %ghost %{_localstatedir}/logs/ossec.json
%dir %attr(750,ossec,ossec) %{_localstatedir}/logs/ossec
%dir %attr(750,root,ossec) %{_localstatedir}/queue
%dir %attr(750,ossec,ossec) %{_localstatedir}/queue/agents
%dir %attr(770,ossec,ossec) %{_localstatedir}/queue/ossec
%dir %attr(750,ossec,ossec) %{_localstatedir}/queue/diff
%dir %attr(770,ossec,ossec) %{_localstatedir}/queue/alerts
%dir %attr(750,ossec,ossec) %{_localstatedir}/queue/rids
%dir %attr(1750,root,ossec) %{_localstatedir}/tmp
%attr(750,root,system) %config(missingok) %{_localstatedir}/tmp/add_localfiles.sh
%attr(750,root,system) %config(missingok) %{_localstatedir}/tmp/gen_ossec.sh
%dir %attr(1750,root,ossec) %config(missingok) %{_localstatedir}/tmp/etc/templates
%dir %attr(1750,root,ossec) %config(missingok) %{_localstatedir}/tmp/etc/templates/config
%dir %attr(1750,root,ossec) %config(missingok) %{_localstatedir}/tmp/etc/templates/config/generic
%attr(750,root,system) %config(missingok) %{_localstatedir}/tmp/etc/templates/config/generic/*.template
%dir %attr(1750,root,ossec) %config(missingok) /var/ossec/tmp/etc/templates/config/generic/localfile-logs
%attr(750,root,system) %config(missingok) /var/ossec/tmp/etc/templates/config/generic/localfile-logs/*.template
%attr(750,root,system) %config(missingok) %{_localstatedir}/tmp/src/*
%dir %attr(750,root,ossec) %{_localstatedir}/var
%dir %attr(770,root,ossec) %{_localstatedir}/var/incoming
%dir %attr(770,root,ossec) %{_localstatedir}/var/run
%dir %attr(770,root,ossec) %{_localstatedir}/var/upgrade
%dir %attr(770,root,ossec) %{_localstatedir}/var/wodles
%dir %attr(750,root,ossec) %{_localstatedir}/wodles
%dir %attr(750,root,ossec) %{_localstatedir}/wodles/aws
%attr(750,root,ossec) %{_localstatedir}/wodles/aws/*


%changelog
* Wed Nov 7 2018 support <support@wazuh.com> - 3.7.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Sep 7 2018 support <support@wazuh.com> - 3.6.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Jul 25 2018 support <support@wazuh.com> - 3.5.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Jul 11 2018 support <support@wazuh.com> - 3.4.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Jun 18 2018 support <support@wazuh.com> - 3.3.1
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Jun 11 2018 support <support@wazuh.com> - 3.3.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed May 30 2018 support <support@wazuh.com> - 3.2.4
- More info: https://documentation.wazuh.com/current/release-notes/
* Thu May 10 2018 support <support@wazuh.com> - 3.2.3
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Apr 09 2018 support <support@wazuh.com> - 3.2.2
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Feb 21 2018 support <support@wazuh.com> - 3.2.1
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Feb 07 2018 support <support@wazuh.com> - 3.2.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Thu Dec 21 2017 support <support@wazuh.com> - 3.1.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Nov 06 2017 support <support@wazuh.com> - 3.0.0
- More info: https://documentation.wazuh.com/current/release-notes/
