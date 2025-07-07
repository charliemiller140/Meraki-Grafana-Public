terraform {
  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "= 3.0.2-rc01"
    }
  }
}
#
provider "proxmox" {
  pm_api_url          = var.pm_api_url
  pm_api_token_id     = var.pm_api_token_id
  pm_api_token_secret = var.pm_api_token_secret
  pm_tls_insecure     = true
}
resource "proxmox_vm_qemu" "ubuntu_vm" {
  name        = "lab-vm-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  target_node = "pve"
  clone       = "ubuntu-24.04-cloud-init-template"

  cores   = 2
  sockets = 2
  memory  = 4096

  scsihw   = "virtio-scsi-pci"
  # DO NOT define `boot = "order=scsi0"` here 


  ipconfig0 = "ip=x.x.x.x/24,gw=x.x.x.x" #static IP
  sshkeys   = file("/home/user/.ssh/id_rsa.pub")

  network {
    id     = 0
    model  = "virtio"
    bridge = "vmbr0"
    tag = 10
    firewall = true
  }

  disk {
    slot    = "scsi0"
    size    = 15
    type    = "disk"
    storage = "local-lvm"
  }

  disk {
    slot    = "ide2"
    type    = "cloudinit"
    storage = "local-lvm"
  }

  os_type = "cloud-init"
}
