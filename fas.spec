%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas
Version:        0.8.7.5
Release:        1%{?dist}
Summary:        Fedora Account System

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/fas/
Source0:        https://fedorahosted.org/releases/f/a/fas/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
BuildRequires:  TurboGears
BuildRequires:  gettext
Requires: TurboGears >= 1.0.4
Requires: python-sqlalchemy
Requires: python-TurboMail
Requires: python-fedora >= 0.3.9.92
Requires: babel
Requires: pygpgme
Requires: python-babel
Requires: python-genshi
Requires: pytz
Requires: python-openid
Requires: python-GeoIP
Requires: pyOpenSSL
Requires: python-memcached
Requires: python-tgcaptcha

%description
The Fedora Account System is a web application that manages the accounts of
Fedora Project Contributors.  It's built in TurboGears and comes with a json
API for querying against remotely.

The python-fedora-infrastructure package has a TurboGears identity provider
that works with the Account System.

%package clients
Summary: Clients for the Fedora Account System
Group: Applications/System
Requires: python-fedora >= 0.3.12.1
Requires: authconfig
Requires: nss_db

%description clients
Additional scripts that work as clients to the accounts system.

%prep
%setup -q


%build
%{__python} setup.py build --install-data='%{_datadir}'


%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install --skip-build --install-data='%{_datadir}' --root %{buildroot}
%{__mkdir_p} %{buildroot}%{_sbindir}
%{__mkdir_p} %{buildroot}%{_sysconfdir}
%{__mv} %{buildroot}%{_bindir}/start-fas %{buildroot}%{_sbindir}
# Unreadable by others because it's going to contain a database password.
%{__install} -m 640 fas.cfg.sample %{buildroot}%{_sysconfdir}/fas.cfg
%{__install} -m 600 client/fas.conf %{buildroot}%{_sysconfdir}
%{__install} -m 700 -d %{buildroot}%{_localstatedir}/lib/fas
%{__cp} fas.wsgi %{buildroot}%{_datadir}/fas/

%{__install} -m 0755 scripts/export-bugzilla.py %{buildroot}%{_sbindir}/export-bugzilla
%{__install} -m 0600 scripts/export-bugzilla.cfg %{buildroot}%{_sysconfdir}/

%{__install} -m 0755 scripts/account-expiry.py %{buildroot}%{_sbindir}/account-expiry
%{__install} -m 0600 scripts/account-expiry.cfg %{buildroot}%{_sysconfdir}/

%find_lang %{name}

%clean
%{__rm} -rf %{buildroot}


%pre
/usr/sbin/useradd -c 'Fedora Acocunt System user' -s /sbin/nologin \
    -r -M -d %{_datadir}/fas fas &> /dev/null || :


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README TODO COPYING fas2.sql fas.spec
%{python_sitelib}/*
%{_datadir}/fas/
%{_sbindir}/start-fas
%{_sbindir}/export-bugzilla
%{_sbindir}/account-expiry
%attr(-,root,fas) %config(noreplace) %{_sysconfdir}/fas.cfg
%attr(-,root,fas) %config(noreplace) %{_sysconfdir}/export-bugzilla.cfg
%attr(-,root,fas) %config(noreplace) %{_sysconfdir}/account-expiry.cfg

%files clients
%defattr(-,root,root,-)
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/fas.conf
%attr(0700,root,root) %dir %{_localstatedir}/lib/fas

%changelog
* Fri Sep 24 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7.5-1
- Upstream released new version

* Thu Sep 09 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7.4-1
- Upstream released new version

* Fri Aug 27 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7.3-1
- Upstream released new version

* Tue Aug 10 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7.1-1
- New upstream release
- Removed python-webob dep (was a false dep anyway)

* Mon Aug 09 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7-1
- New upstream release

* Fri Jul 30 2010 Jon Stanley <jstanley@fedoraproject.org> - 0.8.6.2.6-1
- New upstream release

* Thu Jul 29 2010 Jon Stanley <jstanley@fedoraproject.org> - 0.8.6.2.5-2
- Fix fas.cfg=>fas.cfg.sample rename upstream

* Thu Jul 29 2010 Jon Stanley - 0.8.6.2.5-1
- New upstream release
- Now conflicts with python-sqlalchemy, and requires python-sqlalchemy0.5

* Wed Sep 16 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.6.2.3-1
- New release that implements a captcha for new accounts and fixes a few
  bugs.

* Tue Jun 11 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.6.2.2-1
- Add Requires on python-memcached.
- Fix /var/lib/fas directory.
- Some export-bugzilla fixes.

* Tue Jun  6 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.6.2.1-1
- Typo fix release.

* Tue Jun  4 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.6.2-1
- Upstream released a new version.

* Tue Jun  3 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.6.1-1
- Upstream released a new version.

* Tue Jun  2 2009 Mike McGrath <mmcgrath@fedoraproject.org> - 0.8.6-1
- Upstream released new version
- Cached group/user data

* Sun Apr 12 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.5.2-3
- Fix fas user's home directory (was missing a slash).

* Thu Mar 13 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.5.2-2
- Add /var/lib/fas directory.

* Thu Mar 12 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.5.2-1
- Bugfix for fasClient alias generation and template fixes for the csrf token.

* Mon Mar 9 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.5.1-1
- Quick little bugfix for using the login method via json.

* Sat Mar 7 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.5-1
- Beta new upstream release with CSRF fixes.

* Thu Feb 12 2009 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4.8-1
- New upstream release that fixes some security issues.

* Thu Nov 6 2008 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.4.7-1
- New upstream release that fixes some fasClient issues.

* Mon Nov 3 2008 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.4.6-1
- New upstream release.

* Thu Sep 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.4.5-1
- Upstream released a new version.

* Thu Aug 14 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4.4-1
- Upstream released a new version.

* Tue Jul 29 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4.3-1
- Upstream released a new version.

* Mon Jun 16 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4.2-1
- Upstream released a new version.

* Tue May 27 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4.1-1
- Upstream released a new version

* Tue May 27 2008 Ricky Zhou <ricky@fedoraproject.org> - 0.8.4-1
- Upstream released a new version
- Added pyOpenSSL

* Fri May 16 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.3.2-2
- Upstream released a new version
- Added python-GeoIP

* Thu May 15 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.3.1-1
- updated to a new version (release didn't get updated)

* Thu May 15 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.3-1
- Upstream released new version

* Tue Mar 26 2008 McGrath <mmcgrath@redhat.com> - 0.8.2-1
- Upstream released a new version

* Tue Mar 14 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.1-1
- Upstream released a new version

* Tue Mar 14 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8-1
- Upstream released a new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.7.1-1
- Upstream released new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.7-1
- Upstream released new version

* Tue Mar 13 2008 Mike McGrath <mmcgrath@redhat.com> - 0.6-1
- Upstream released a new version

* Tue Mar 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.5-1
- Upstream released a new version

* Tue Mar 11 2008 Mike McGrath <mmcgrath@redhat.com> - 0.4-1
- added fas.conf will fix later.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.3-1
- Upstream released a new version.

* Mon Mar 10 2008 Mike McGrath <mmcgrath@redhat.com> - 0.2-1
- Added fas user/group

* Mon Mar 10 2008 Toshio Kuratomi <tkuratom@redhat.com> - 0.1-1
- Initial Build.
