<!--
#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
-->


# Vagrant Usage


## How to use vagrant in a Linux environment

Clone ngEO Browse Server:

```sh
    git clone git@github.com:EOX-A/ngeo-b.git
    cd ngeo-b/
    git submodule init
    git submodule update
```

Prepare local environment:

```sh
    cd vagrant/shares/
    git clone git@github.com:EOxServer/eoxserver.git
    cd eoxserver/
    git checkout 0.3
    cd ../
    git clone git@github.com:EOX-A/mapcache.git
    cd mapcache/
    git checkout auth
    cd ../../
```

Install VirtualBox & Vagrant. The configuration is tested with:
* [Vagrant v1.3.5](http://downloads.vagrantup.com/tags/v1.3.5)
* [VirtualBox 4.3.0](https://www.virtualbox.org/wiki/Downloads)

Install Vagrant add-ons:
* `sahara` for [sandboxing](https://github.com/jedi4ever/sahara)
* `vagrant-vbguest` to [check for Virtualbox Guest Additions](https://github.com/dotless-de/vagrant-vbguest)
* `vagrant-cachier` to [cache yum/apt/etc. packages](https://github.com/fgrehm/vagrant-cachier)

```sh
    vagrant plugin install sahara
    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-cachier
```

Run vagrant:

```sh
    cd vagrant/
    vagrant up
```

The ngEO Browse Server is now accessible at [http://localhost:3080/](http://localhost:3080/).

Run tests:

```sh
    vagrant ssh
    cd /var/ngeob_autotest/
    python manage.py test control -v2
```


## How to use vagrant in a Windows environment

Use the following steps:

1. Install git from http://git-scm.com/download/win
2. Install VirtualBox from
   http://download.virtualbox.org/virtualbox/4.3.2/VirtualBox-4.3.2-90405-Win.exe
3. Install vagrant from http://downloads.vagrantup.com/tags/v1.3.5 (use the .msi file)
4. Start a git bash and execute the following commands:

```sh
    git clone git@github.com:EOX-A/ngeo-b.git
    cd ngeo-b/
    git submodule init
    git submodule update

    cd vagrant/shares/
    git clone git@github.com:EOxServer/eoxserver.git
    cd eoxserver/
    git checkout 0.3
    cd ../
    git clone git@github.com:EOX-A/mapcache.git
    cd mapcache/
    git checkout auth
    cd ../../
```

5. Open the Vagrantfile (located in ngeo-b/vagrant ) with an editor.
6. Add v.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"] before the line # Use GUI for debugging purposes
7. Save and close Vagrantfile
8. Open an Administrator Console (right click on the command prompt icon and select "Run as administrator")
9. Enter secpol.msc (and hit enter). Navigate to Local Policies, User Rights Assignment and check "Create symbolic links". Make sure that the Administrator account is added. Close it.
10. Still in the admin console enter: fsutil behavior set SymlinkEvaluation L2L:1 R2R:1 L2R:1 R2L:1 (and hit enter. This step isn't necessary on all systems. Only if you use net shares. But it does not hurt 
11. Open the Administrative Tools Panel from the Control Panel. Open Component Services.
12. Select Computers, My Computer, Select DCOM Config.
13. Right click on "Virtual Box Application". Select Security. At "Launch and Activation Permissions" select Customize. Hit Edit.
14. Add your user account and Administrator. Select Permissions: Local Launch, Remote Launch, Local Activation and Remote Activation. Hit Ok. And again ok. Close the Component Services.
15. Log off and log on again.
16. Open an Administrator console and enter:

```sh
    vagrant plugin install sahara
    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-cachier
    cd vagrant/
    vagrant up
```

17. The ngEO Browse Server is now accessible at [http://localhost:3080/](http://localhost:3080/).
18. Run tests:

```sh
    vagrant ssh
    cd /var/ngeob_autotest/
    python manage.py test control -v2
```


## Troubleshoot vagrant

* If the provisioning didn't finish during vagrant up or after changes try: `vagrant provision`
* (Re-)Install virtualbox guest additions in case it complains about not matching versions: `vagrant vbguest -f`
* Slow performance: Check "Enable IO APIC", uncheck "Extended Features: Enable PAE/NX", and uncheck "Enable Nested Paging" in VirtualBox Manager.
* Symlinks with VirtualBox 4.1 not working: vi /opt/vagrant/embedded/gems/gems/vagrant-1.3.5/plugins/providers/virtualbox/driver/version_4_1.rb and add those changes: https://github.com/mitchellh/vagrant/commit/387692f9c8fa4031050646e2773b3d2d9b2c994e


# Build preparations

[Prepare a vagrant environment](https://gitlab.eox.at/vagrant/builder_rpm/tree/master).


## How to build ngEO Browse Server

Check Jenkins build is passing.

```sh
    cd git/ngeo-b/
    git pull

    # If starting a new release branch:
    git checkout -b branch-1-1
    vi ngeo_browse_server/__init__.py
    # Adjust version to future one
    git commit ngeo_browse_server/__init__.py -m "Adjusting version."
    git push origin branch-1-1

    vi ngeo_browse_server/__init__.py
    # Adjust version
    vi setup.py
    # Adjust Development Status
    git commit setup.py ngeo_browse_server/__init__.py -m "Adjusting version."
    # Info:
    #Development Status :: 1 - Planning
    #Development Status :: 2 - Pre-Alpha
    #Development Status :: 3 - Alpha
    #Development Status :: 4 - Beta
    #Development Status :: 5 - Production/Stable
    #Development Status :: 6 - Mature
    #Development Status :: 7 - Inactive

    git tag -a release-2.0.8 -m "Tagging release 2.0.8."
    git archive --format=tar --prefix=ngEO_Browse_Server-2.0.8/ release-2.0.8 | gzip > ngEO_Browse_Server-2.0.8.tar.gz
    mv ngEO_Browse_Server-2.0.8.tar.gz <path-to-builder_rpm>
    cd <path-to-builder_rpm>/
    vagrant ssh

    tar xzf ngEO_Browse_Server-2.0.8.tar.gz
    rm ngEO_Browse_Server-2.0.8.tar.gz
    cd ngEO_Browse_Server-2.0.8/
    python setup.py bdist_rpm --release <NO>
    cd dist
    tar czf ../../rpmbuild/RPMS/ngEO_Browse_Server-2.0.8.tar.gz ngEO_Browse_Server-*rpm
    # scp ../../ngEO_Browse_Server-2.0.8.tar.gz -> packages@packages.eox.at:.
    cd ../..
    rm -r ngEO_Browse_Server-2.0.8/
    exit # vagrant

    vi ngeo_browse_server/__init__.py
    # Adjust version to dev
    vi setup.py
    # Adjust Development Status if necessary
    git commit setup.py ngeo_browse_server/__init__.py -m "Adjusting version."

    git push
    git push --tags
```

* Edit release at https://github.com/EOX-A/ngeo-b/releases
* Edit milestones at https://github.com/EOX-A/ngeo-b/issues/milestones
* Mail to dev & users
* Tweet


## How to build EOxServer

See https://github.com/EOxServer/eoxserver/tree/master/vagrant#how-to-build-eoxserver


## How to build MapCache

```sh
    cd mapcache_git
    git pull
    git archive --format=tar --prefix=mapcache-1.2.1/ rel-1-2-1 | gzip > mapcache-1.2.1.tar.gz
    mv mapcache-1.2.1.tar.gz <path-to-builder_rpm>
    cd <path-to-builder_rpm>/
    vagrant ssh

    g diff -p branch-1-2 auth -- > patch_auth

    cd rpmbuild/SPECS/
    rpmdev-bumpspec --comment="<COMMENT>" --userstring="<NAME> <<MAIL>>" mapcache.spec
    vi mapcache.spec
    # Adjust Release
    rpmbuild -ba mapcache.spec
    cd ..
    mv RPMS/x86_64/ .
    tar czf t x86_64/ SRPMS/
    rm -r x86_64/ SRPMS/
    # Install at packages@yum.packages.eox.at
```


## How to build MapServer

```sh
    cd mapserver_git
    git pull
    vi mapserver.h
    # Adjust MS_VERSION: #define MS_VERSION "6.3dev"
    git archive --format=tar --prefix=mapserver-6.3dev/ master | gzip > mapserver-6.3dev.tar.gz
    cd ....
    vagrant ssh
    cd rpmbuild/SPECS/
    vi mapserver.spec
    # Adjust Release
    rpmbuild -ba mapserver.spec
    cd ..
    mv RPMS/x86_64/ .
    tar czf t x86_64/ SRPMS/
    rm -r x86_64/ SRPMS/
    # Install at packages@yum.packages.eox.at
```
