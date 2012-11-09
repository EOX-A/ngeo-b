# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.
  config.package.name = "eox.ngeob"
  
  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "eox-box-ngeob"
  config.vm.box_url = "http://downloads.eox.at/boxes/eox-ngeob.box"
  
  # Enable bridged networking
  #config.vm.network :bridged
  
  # Forward a port from the guest to the host, which allows for outside
  # computers to access the VM, whereas host only networking does not.
  config.vm.forward_port 80, 3080 
  config.vm.forward_port 443, 3443
  config.vm.forward_port 8000, 38000

  # Share an additional folder to the guest VM. The first argument is
  # an identifier, the second is the path on the guest to mount the
  # folder, and the third is the path on the host to the actual folder.
  # config.vm.share_folder "v-data", "/vagrant_data", "../data"
  config.vm.share_folder  "httpd-config", "/etc/httpd", "./shares/httpd/conf"
  config.vm.share_folder  "httpd-root", "/var/www", "./shares/httpd/www_root"
  config.vm.share_folder  "eoxserver", "/var/eoxserver", "./shares/eoxserver"
  config.vm.share_folder  "ngeob", "/var/ngeob", "./ngeo_browse_server"

  # Enable symlinks in shared folders 
  config.vm.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/v-root", "1"]
  config.vm.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/httpd-root", "1"]
  config.vm.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/httpd-config", "1"]
  config.vm.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/eoxserver", "1"]
  config.vm.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/ngeob", "1"]

  # Increase memory
  config.vm.customize ["modifyvm", :id, "--memory", 1024]

  # Enable provisioning with Puppet stand alone.
  #config.vm.provision :puppet do |puppet|
  #  puppet.manifests_path = "puppet/manifests"
  #  puppet.module_path = "puppet/modules"
  #  puppet.manifest_file  = "eoxserver.pp"
  #end

  # Use for debugging purposes.
  #config.vm.boot_mode = :gui
end
