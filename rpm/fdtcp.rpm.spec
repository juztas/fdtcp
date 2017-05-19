# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fdtcp
Version:        0.25
Release:        1%{?dist}
Summary:        client/server tools for running persistent fdt services

Group:          System Environment/Daemons
License:        ASL 2.0
URL:            https://twiki.cern.ch/twiki/bin/view/Main/PhEDExFDTIntegration
Source0:        https://github.com/cmscaltech/fdtcp/archive/%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# We'll need java and related libraries when we are ready to
# build the authenticators from source.
#BuildRequires:  jdk ant cog-jglobus
Requires:       fdt jdk jpackage-utils cog-jglobus pyro python-apmon psutil
BuildArch:      noarch

%description
%{summary}.

%prep
%setup -q -n fdtcp-%{version}


%build
# Uncomment these when we're ready to build from source
#cd authenticator
#ant jars


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
install -p -m 0644 conf/fdtd-system-conf.sh $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
install -p -m 0644 conf/fdtd.conf $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
install -p -m 0644 conf/fdtcp.conf $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/

# Install the authenticator jars
mkdir -p $RPM_BUILD_ROOT%{_javadir}/%{name}
install -p -m 0644 javalibs/authclient.jar $RPM_BUILD_ROOT%{_javadir}/%{name}/
install -p -m 0644 javalibs/authservice.jar $RPM_BUILD_ROOT%{_javadir}/%{name}/

# Install the python libraries
mkdir -p $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/common/
mkdir -p $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/utils/
install -p -m 0644 src/python/*.py $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/
install -p -m 0644 src/python/common/*.py $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/common/
install -p -m 0644 src/python/utils/*.py $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/utils/
install -p -m 0644 src/python/fdtd $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/
install -p -m 0644 src/python/fdtcp $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/
install -p -m 0644 src/python/fdtd-log-analyzer $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/
chmod 0755 $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/fdtd
chmod 0755 $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/fdtcp
chmod 0755 $RPM_BUILD_ROOT%{python_sitelib}/fdtcp/fdtd-log-analyzer

# Link to the fdt client and server clt
mkdir -p $RPM_BUILD_ROOT%{_bindir}
ln -s %{python_sitelib}/fdtcp/fdtd $RPM_BUILD_ROOT%{_bindir}/fdtd
ln -s %{python_sitelib}/fdtcp/fdtcp $RPM_BUILD_ROOT%{_bindir}/fdtcp
ln -s %{python_sitelib}/fdtcp/fdtd-log-analyzer $RPM_BUILD_ROOT%{_bindir}/fdtd-log-analyzer

# Install the three sudo wrapper scripts
install -p -m 0755 bin/wrapper_fdt.sh $RPM_BUILD_ROOT%{_bindir}/
install -p -m 0755 bin/wrapper_kill.sh $RPM_BUILD_ROOT%{_bindir}/
install -p -m 0755 bin/wrapper_auth.sh $RPM_BUILD_ROOT%{_bindir}/

# Install the fdtd init script
mkdir -p $RPM_BUILD_ROOT%{_initrddir}/
install -p -m 0755 bin/fdtd.sh $RPM_BUILD_ROOT%{_initrddir}/fdtd

# Create the log directories
mkdir -p $RPM_BUILD_ROOT%{_var}/log/fdtd
mkdir -p $RPM_BUILD_ROOT%{_var}/run/fdtd

%check
# Nothing to test!

%clean
rm -rf $RPM_BUILD_ROOT


%pre
getent group fdt >/dev/null || groupadd -r fdt
getent passwd fdt >/dev/null || \
       useradd -r -g fdt -c "FDT service user" \
       -s /sbin/nologin -d /etc/fdtcp fdt
exit 0

%post
/sbin/chkconfig --add fdtd

%preun
if [ "$1" = "0" ]; then
    /sbin/service fdtd stop > /dev/null 2>&1
    /sbin/chkconfig --del fdtd
fi

%postun
if [ "$1" -ge "1" ] ; then
    /sbin/service fdtd condrestart >/dev/null 2>&1 || :
fi

%files
%defattr(-,root,root,-)
%doc README.md
%attr(-,fdt,fdt) %config(noreplace) %{_sysconfdir}/fdtcp
%{_bindir}/wrapper_*.sh
%{_bindir}/fdtd
%{_bindir}/fdtcp
%{_bindir}/fdtd-log-analyzer
%{python_sitelib}/fdtcp
%{_javadir}/%{name}
%{_initrddir}/fdtd
%attr(-,fdt,fdt) %{_var}/log/fdtd
%attr(-,fdt,fdt) %{_var}/run/fdtd

