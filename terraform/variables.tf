variable "pm_api_url" {}

variable "pm_api_token_id" {
  description = "Proxmox API token ID in the format user@realm!tokenname"
}

variable "pm_api_token_secret" {
  description = "Proxmox API token secret"
}

variable "template_name" {
  default = "ubuntu-22.04-template"
}

variable "public_key" {
  description = "SSH public key to be injected into the VM"
  type        = string
}
