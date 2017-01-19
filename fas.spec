%global commit0 780fc52615b497155b411ce16351f3786e4a75b3
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           fas
Version:        3.0
Release:        6%{?dist}
Summary:        Fedora Account System

License:        GPLv2
URL:            https://github.com/fedora-infra/fas
Source0:        https://github.com/fedora-infra/%{name}/archive/%{commit0}.tar.gz#/%{name}-%{shortcommit0}.tar.gz
Patch0:         fas-wsgi.patch

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-pyramid
Requires: python-sqlalchemy
Requires: python-pyramid-mako
Requires: python-transaction
Requires: python-pyramid-tm
Requires: python-zope-sqlalchemy
Requires: python-waitress
Requires: python-mako
Requires: python-wtforms
Requires: python-mistune
Requires: python-GeoIP
Requires: python-pygeoip
Requires: python-ua-parser
Requires: PyYAML
Requires: python-PyGithub
Requires: python-pillow
Requires: python-cryptography
Requires: fedmsg
#Requires: python-fake-factory
Requires: python-alembic
#Requires: GeoIP-GeoLite-data-extra
Requires: GeoIP

# TODO: Conditionalize this for RHEL
Requires: python-webob1.4

%description
The Fedora Account System is a web application that manages the accounts of
Fedora Project Contributors.  It's built in Pyramid and comes with a json
API for querying against remotely.

%package        theme-fedoraproject
Summary:        Fedora Project's theme for fas

Requires:       %{name} = %{version}-%{release}
#TODO: Add node's deps below

%description    theme-fedoraproject
This package contains theme related assets for the Fedora Project.


%prep
%autosetup -n %{name}-%{commit0}
#%patch0 -p0

%build
# A few hacks to nuke unnecessary deps for now:
sed -i '/lingua/d' setup.py
sed -i '/fake-factory/d' setup.py
%{__python} setup.py build #--install-data='%{_datadir}'


%install
%{__mkdir_p} %{buildroot}%{_sbindir}
%{__mkdir_p} %{buildroot}%{_datadir}/%{name}
%{__mkdir_p} %{buildroot}%{_sysconfdir}/%{name}
%{__mkdir_p} %{buildroot}%{python_sitelib}/%{name}/
%{__mkdir_p} %{buildroot}%{_datadir}/%{name}/theme/default/
%{__mkdir_p} %{buildroot}%{_datadir}/%{name}/theme/fedoraproject/

%{__python} setup.py install --skip-build --install-data='%{_datadir}' --root %{buildroot}

%{__install} fas.wsgi %{buildroot}%{_sbindir}
%{__install} -m 700 -d %{buildroot}%{_localstatedir}/lib/%{name}
%{__install} development.ini %{buildroot}%{_sysconfdir}/%{name}/production.ini

%{__cp} -r %{name}/theme/default/static %{buildroot}%{_datadir}/%{name}/theme/default/static
%{__cp} -r %{name}/theme/default/templates %{buildroot}%{python_sitelib}/%{name}/theme/default/templates

%{__cp} -r %{name}/theme/fedoraproject/static %{buildroot}%{_datadir}/%{name}/theme/fedoraproject/static
%{__cp} -r %{name}/theme/fedoraproject/templates %{buildroot}%{python_sitelib}/%{name}/theme/fedoraproject/templates

chmod 755 %{buildroot}%{python_sitelib}/%{name}/

#%find_lang %{name}

%pre
/usr/sbin/useradd -c 'Fedora Account System user' -s /sbin/nologin \
    -r -M -d %{_datadir}/%{name} fas &> /dev/null || :


#%check
#fas-admin --initdb --default-value
#fas-admin --generate-fake-data -n 666

#%files -f %{name}.lang
%files
%doc README.rst COPYING fas.spec fas.wsgi
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/theme/default/*
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/fas/production.ini
%{_sbindir}/fas.wsgi
%{_bindir}/fas-admin
%exclude /%{python_sitelib}/%{name}/theme/default/static
%exclude /%{python_sitelib}/%{name}/theme/fedoraproject/
%exclude /%{datadir}/%{name}/theme/fedoraproject/


%files theme-fedoraproject
%doc COPYING
%{_datadir}/%{name}/theme/fedoraproject


%changelog
* Wed Jan 18 2017 Ryan Lerch <rlerch@redhat.com> - 3.0.0-6
- Bump package's release.
- using commit 780fc52615b497155b411ce16351f3786e4a75b3
- updated spec to match new locations of themes (PR#227)

* Thu Jan 05 2017 Xavier Lamien <laxathon@fedoraproject.org> - 3.0.0-5
- Bump package's release.

* Sun Dec 18 2016 Xavier Lamien <laxathom@fedoraproject.org> - 3.0.0-4
- Move theme to a dedicated subpackage.

* Tue Aug 2 2016 Ricky Elrod <relrod@redhat.com> - 3.0-3
- Include templates.

* Thu Jul 28 2016 Ricky Elrod <relrod@redhat.com> - 3.0-2
- Latest commit
- Install production.ini

* Tue Jun 21 2016 Ricky Elrod <relrod@redhat.com> - 3.0-1
- Inital build of FAS3.

* Thu Oct 18 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.15-1
- Update translations.  Final release

* Mon Sep 24 2012 Ricky Elrod <codeblock@fedoraproject.org> - 0.8.14.92-2
- Update translations

* Fri Sep 14 2012 Ricky Elrod <codeblock@fedoraproject.org> - 0.8.14.92-1
- Remove blog feed commit, because it was dependant on fancyflash.

* Thu Aug 30 2012 Ricky Elrod <codeblock@fedoraproject.org> - 0.8.14.91-1
- Add a patch from ctria (see infra #3027) for checking passwords against
  libpwquality. (Ricky Elrod)

* Sat Aug 10 2012 Ricky Elrod <codeblock@fedoraproject.org> - 0.8.14.90-1
- Differing colors of headers for differing types of deployment.
- Add a place where users are able to add their blog to the planet
- Show the content of the group if there are less than 10 people in it
- Pull in latest translations to prepare for 0.8.15.

* Sat Jul 28 2012 Patrick Uiterwijk <puiterwijk@gmail.com> - 0.8.14-1
- Added security question system, with encrypted security answer

* Fri Jul 06 2012 Ralph Bean <rbean@redhat.com> - 0.8.13-2
- Typo fix.  python-fedmsg should just be 'fedmsg'.

* Fri Jul 06 2012 Ralph Bean <rbean@redhat.com> - 0.8.13-1
- Version bump for fedmsg in stg.

* Sat Mar 31 2012 Ralph Bean <rbean@redhat.com> - 0.8.12-2
- Added dependency on fedmsg.

* Tue Feb 21 2012 Xavier Laminen <laxathom@lxtnow.net> - 0.8.12-1
- Upstream release.
- Add heuristics human's name check.

* Tue Jan 24 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.11-1
- New upstream release -- allows email to be used to login, implements an audio
  captcha, and normalizes some error codes.

* Fri Nov 18 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.9.1-1
- Important fix: the new strength checking validator introduced in 0.8.8.90 (or
  hotfixes before that) was allowing users to set empty passwords.

* Thu Nov 17 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.9-1
- FAS final release.
- Mark the cert files as config

* Thu Oct 27 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.8.92-1
- Going to to daily new rpms until release so translators can see their work.

* Thu Oct 27 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.8.91-1
- Second beta

* Thu Oct 27 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.8.90-1
- Beta of the 0.8.9 release.

* Mon May 2 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.8-1
- Final release

* Tue Apr 5 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8.8-0.1.a1
- Update for FPCA
- Move fas.wsgi into /usr/sbin
- Include the updates directory in the package
- Make the apache configfile %%doc instead of installing it

* Mon Feb 07 2011 Jim Lieb <lieb@sea-troll.net> - 0.8.7.5-1.1
- Localize UI to Yahoo.
- Make wsgi instantiation work

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
- New upstream release that fixes some security issues
