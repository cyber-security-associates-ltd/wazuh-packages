Summary:     Wazuh API is an open source RESTful API to interact with Wazuh from your own application or with a simple web browser or tools like cURL
Name:        wazuh-api
Version:     3.2.1
Release:     %{_release}
License:     GPL
Group:       System Environment/Daemons
Source0:     %{name}-%{version}.tar.gz
URL:         https://www.wazuh.com/
BuildRoot:   %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Vendor:      Wazuh, Inc <support@wazuh.com>
Packager:    Wazuh, Inc <support@wazuh.com>
Requires(pre):    /usr/sbin/groupadd /usr/sbin/useradd
Requires(post):   /sbin/chkconfig
Requires(preun):  /sbin/chkconfig /sbin/service
Requires(postun): /sbin/service

Requires: nodejs >= 4.6
Requires: wazuh-manager >= 3.2.1
BuildRequires: nodejs >= 4.6
ExclusiveOS: linux

%description
Wazuh API is an open source RESTful API to interact with Wazuh
from your own application or with a simple web browser or tools like cURL

%prep
%setup -q

npm install --production

%install
# Clean BUILDROOT
rm -fr %{buildroot}

mkdir -p ${RPM_BUILD_ROOT}%{_initrddir}
#Folders
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/api
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/api/{configuration,controllers,examples,helpers,models,scripts}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/api/configuration/{auth,ssl}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/api/node_modules
#Files
install -m 0400 package.json ${RPM_BUILD_ROOT}%{_localstatedir}/api
install -m 0500 app.js ${RPM_BUILD_ROOT}%{_localstatedir}/api
install -m 0500 configuration/config.js ${RPM_BUILD_ROOT}%{_localstatedir}/api/configuration
install -m 0500 configuration/preloaded_vars.conf ${RPM_BUILD_ROOT}%{_localstatedir}/api/configuration
install -m 0500 configuration/auth/user  ${RPM_BUILD_ROOT}%{_localstatedir}/api/configuration/auth
install -m 0500 controllers/* ${RPM_BUILD_ROOT}%{_localstatedir}/api/controllers
install -m 0500 examples/* ${RPM_BUILD_ROOT}%{_localstatedir}/api/examples
install -m 0500 helpers/* ${RPM_BUILD_ROOT}%{_localstatedir}/api/helpers
install -m 0500 models/*  ${RPM_BUILD_ROOT}%{_localstatedir}/api/models
install -m 0500 scripts/bump_version.sh ${RPM_BUILD_ROOT}%{_localstatedir}/api/scripts
install -m 0500 scripts/configure_api.sh ${RPM_BUILD_ROOT}%{_localstatedir}/api/scripts
install -m 0500 scripts/install_daemon.sh ${RPM_BUILD_ROOT}%{_localstatedir}/api/scripts
install -m 0400 scripts/wazuh-api ${RPM_BUILD_ROOT}%{_localstatedir}/api/scripts
install -m 0400 scripts/wazuh-api.service  ${RPM_BUILD_ROOT}%{_localstatedir}/api/scripts

cp -r node_modules/* ${RPM_BUILD_ROOT}%{_localstatedir}/api/node_modules/

cp CHANGELOG.md CHANGELOG

exit 0
%pre

if [ $1 = 1 ]; then
  API_PATH="${RPM_BUILD_ROOT}%{_localstatedir}/api"
  API_PATH_BACKUP="${RPM_BUILD_ROOT}%{_localstatedir}/~api"

  if [ -e ${API_PATH} ]; then
    if [ -e ${API_PATH_BACKUP} ]; then
        rm -rf ${API_PATH_BACKUP}
    fi

    cp -rLfp ${API_PATH} ${API_PATH_BACKUP}
    chown root:root ${API_PATH_BACKUP}

    ${API_OLD_VERSION}=`cat ${API_PATH_BACKUP}/package.json | grep "version\":" | grep -P "\d+(?:\.\d+){0,2}" -o`
    if [ "X${API_OLD_VERSION}" == "X1.3.0" ]; then
        rm -rf ${API_PATH}/configuration
        cp -rfp ${API_PATH_BACKUP}/configuration ${API_PATH}/configuration
    elif [ "X${API_OLD_VERSION}" == "X1.1" ] || [ "X${API_OLD_VERSION}" == "X1.2.0" ] || [ "X${API_OLD_VERSION}" == "X1.2.1" ]; then
        cp -rfp ${API_PATH_BACKUP}/ssl/htpasswd ${API_PATH}/configuration/auth/user
        cp -p ${API_PATH_BACKUP}/ssl/*.key $API_PATH_BACKUP/ssl/*.crt ${API_PATH}/configuration/ssl/
        chown -R root:root ${API_PATH}/configuration
        chmod -R 500 ${API_PATH}/configuration
        chmod u-x ${API_PATH}/configuration/ssl/*
    fi
  fi
fi

%post

if [ $1 = 1 ]; then
  /var/ossec/api/scripts/install_daemon.sh
  echo "Don’t forget to secure the API configuration by running the script /var/ossec/api/scripts/configure_api.sh"
fi
  touch /var/ossec/logs/api.log
  chmod 660 /var/ossec/logs/api.log
  chown root:ossec /var/ossec/logs/api.log
  chmod 740 /var/ossec/api/configuration/config.js
  chown root:ossec /var/ossec/api/configuration/config.js
ln -sf /var/ossec/api/node_modules/htpasswd/bin/htpasswd /var/ossec/api/configuration/auth/htpasswd

#veriy python version
if python -V >/dev/null 2>&1; then
   python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' | cut -c1-3)
   if [ ! $python_version == '2.7' ]; then
      echo "Warning: Minimal supported version is 2.7"
   fi
else
   echo "Warning: You need python 2.7 or above"
fi

if [ -n "$(ps -e | egrep ^\ *1\ .*systemd$)" ]; then
  systemctl stop wazuh-api.service
  systemctl daemon-reload
  systemctl restart wazuh-api.service

elif [ -n "$(ps -e | egrep ^\ *1\ .*init$)" ]; then
  service wazuh-api restart
fi

%preun

if [ $1 = 0 ]; then
  if [ -n "$(ps -e | egrep ^\ *1\ .*systemd$)" ]; then
    systemctl stop wazuh-api.service
    systemctl disable wazuh-api.service
    rm -f /etc/systemd/system/wazuh-api.service
  fi

  if [ -n "$(ps -e | egrep ^\ *1\ .*init$)" ]; then
    service wazuh-api stop
    chkconfig wazuh-api off
  fi
fi


%clean
rm -fr %{buildroot}

%files
%defattr(-,root,root)
%doc CHANGELOG
%attr(750,root,ossec) %dir %{_localstatedir}/api
%attr(750,root,ossec) %config(noreplace) %dir %{_localstatedir}/api/configuration
%attr(750,root,ossec) %dir %{_localstatedir}/api/controllers
%attr(750,root,ossec) %dir %{_localstatedir}/api/examples
%attr(750,root,ossec) %dir %{_localstatedir}/api/helpers
%attr(750,root,ossec) %dir %{_localstatedir}/api/models
%attr(750,root,root) %dir %{_localstatedir}/api/scripts
%attr(750,root,root) %config(noreplace) %dir %{_localstatedir}/api/configuration/auth
%attr(750,root,root) %config(noreplace) %dir %{_localstatedir}/api/configuration/ssl
%attr(750,root,ossec) %dir %{_localstatedir}/api/node_modules

%attr(640,root,ossec) %{_localstatedir}/api/package.json
%attr(750,root,ossec) %{_localstatedir}/api/app.js
%attr(740,root,ossec) %config(noreplace) %{_localstatedir}/api/configuration/config.js
%attr(750,root,root) %{_localstatedir}/api/configuration/preloaded_vars.conf
%attr(750,root,root) %config(noreplace) %{_localstatedir}/api/configuration/auth/user
%attr(750,root,ossec) %{_localstatedir}/api/controllers/*
%attr(750,root,ossec) %{_localstatedir}/api/examples/*
%attr(750,root,ossec) %{_localstatedir}/api/helpers/*
%attr(750,root,ossec) %{_localstatedir}/api/models/*
%attr(750,root,root) %{_localstatedir}/api/scripts/*.sh
%attr(640,root,root) %{_localstatedir}/api/scripts/wazuh-api
%attr(640,root,root) %{_localstatedir}/api/scripts/wazuh-api.service
%attr(750,ossec,ossec) %{_localstatedir}/api/node_modules/*

%changelog
* Wed Feb 21 2018 support <support@wazuh.com> - 3.2.1
- More info: https://documentation.wazuh.com/current/release-notes/
* Wed Feb 07 2018 support <support@wazuh.com> - 3.2.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Dec 19 2017 support <support@wazuh.com> - 3.1.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Mon Nov 07 2017 support <support@wazuh.com> - 3.0.0
- More info: https://documentation.wazuh.com/current/release-notes/
* Fri May 26 2017 support <support@wazuh.com> - 2.0.1
- Issue when basic-auth is disabled.
- Regex for latest version in install_api.sh
- Wrong scan dates for syscheck and rootcheck.
- IP value always must be lowercase.
* Fri Sep 16 2016 Jose Luis Ruiz <jose@wazuh.com> - 2.0
- First rpm.
