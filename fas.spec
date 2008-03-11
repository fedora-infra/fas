%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas
Version:        0.2
Release:        1%{?dist}
Summary:        Fedora Account System

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/fas2/
Source0:        https://fedorahosted.org/releases/f/e/fedora-infrastructure/
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  setuptools-devel
Requires: TurboGears >= 1.0.4
Requires: python-sqlalchemy >= 0.4
Requires: python-turbomail
Requires: python-fedora-infrastructure >= 0.2.99.2

%description
The Fedora Account System is a web application that manages the accounts of
Fedora Project Contributors.  It's built in TurboGears and comes with a json
API for querying against remotely.

The python-fedora-infrastructure package has a TurboGears identity provider
that works with the Account System.

%package clients
Summary: Clients for the Fedora Account System
Group: Applications/System
Requires: python-fedora
Requires: rhpl

%description -n clients
Additional scripts that work as clients to the accounts system.

%prep
%setup -q


%build
%{__python} setup.py build --install-data='%{_datadir}/fas'

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --install-data='%{_datadir}/fas' --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
mv $RPM_BUILD_ROOT%{_bindir}/start-fas $RPM_BUILD_ROOT%{_sbindir}
# Unreadable by others because it's going to contain a database password.
install -m 0600 fas.cfg $RPM_BUILD_ROOT%{_sysconfdir}
 
%clean
rm -rf $RPM_BUILD_ROOT

%pre
/usr/sbin/groupadd -r fas &>/dev/null || :
/usr/sbin/useradd  -r -s /sbin/nologin -d /usr/share/fas -M \
                               -c 'Fedora Account System User' -g fas fas &>/dev/null || :

%files
%defattr(-,root,root,-)
%doc README TODO COPYING fas2.sql
%{python_sitelib}/*
%{_sbindir}/start-fas
%config(noreplace) %{_sysconfdir}/*

%files -n clients
%{_bindir}/*

%changelog
* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.2-1
- Added create user to pre

* Mon Mar 10 2008 Toshio Kuratomi <tkuratom@redhat.com> - 0.1-1
- Initial Build.
