locals {
  env    = "dev"
  region = "mxct"
}

# Get resource group data
data "azurerm_resource_group" "main_rg" {
  name = var.resource_group_name
}
# Create hub vnet
resource "azurerm_virtual_network" "hub_vnet" {
  name                = "vnet-${local.env}-${local.region}-hub-01"
  address_space       = ["10.0.0.0/16"]
  location            = data.azurerm_resource_group.main_rg.location
  resource_group_name = data.azurerm_resource_group.main_rg.name
}

# Create subnet for hub vnet
resource "azurerm_subnet" "hub_snet_01" {
  name                 = "snet-${local.env}-${local.region}-hub-01"
  resource_group_name  = data.azurerm_resource_group.main_rg.name
  virtual_network_name = azurerm_virtual_network.hub_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Create spoke vnet
resource "azurerm_virtual_network" "spoke_vnet" {
  name                = "vnet-${local.env}-${local.region}-spoke-01"
  address_space       = ["10.1.0.0/16"]
  location            = data.azurerm_resource_group.main_rg.location
  resource_group_name = data.azurerm_resource_group.main_rg.name
}

# Create subnet for spoke vnet
resource "azurerm_subnet" "spoke_snet_01" {
  name                 = "snet-${local.env}-${local.region}-spoke-01"
  resource_group_name  = data.azurerm_resource_group.main_rg.name
  virtual_network_name = azurerm_virtual_network.spoke_vnet.name
  address_prefixes     = ["10.1.1.0/24"]
}

# Create vnet peering for hub to spoke
resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  name                      = "peer-${local.env}-${local.region}-hub-to-spoke-01"
  resource_group_name       = data.azurerm_resource_group.main_rg.name
  virtual_network_name      = azurerm_virtual_network.hub_vnet.name
  remote_virtual_network_id = azurerm_virtual_network.spoke_vnet.id

  # Allow hub to access spoke
  allow_virtual_network_access = true
  # Allow traffic forwarding from spoke to hub
  allow_forwarded_traffic = true
}
# Create vnet peering for spoke to hub
resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  name                      = "peer-${local.env}-${local.region}-spoke-to-hub-01"
  resource_group_name       = data.azurerm_resource_group.main_rg.name
  virtual_network_name      = azurerm_virtual_network.spoke_vnet.name
  remote_virtual_network_id = azurerm_virtual_network.hub_vnet.id

  # Allow spoke to access hub
  allow_virtual_network_access = true
  # Allow traffic forwarding from hub to spoke
  allow_forwarded_traffic = true

}


# Create public ip address for hub vm
resource "azurerm_public_ip" "pip_hub" {
  name                = "pip-${local.env}-${local.region}-hub-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location
  allocation_method   = "Static"
}

# Create nic for hub vm
resource "azurerm_network_interface" "hub_vm_nic" {
  name                  = "nic-${local.env}-${local.region}-hub-01"
  location              = data.azurerm_resource_group.main_rg.location
  resource_group_name   = data.azurerm_resource_group.main_rg.name
  ip_forwarding_enabled = true



  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.hub_snet_01.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip_hub.id
  }
}

# Create a virtual machine in the hub vnet
resource "azurerm_linux_virtual_machine" "hub_vm" {
  name                = "vm-${local.env}-${local.region}-hub-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location
  size                = "Standard_B2ts_v2"
  admin_username      = "linuxadmin"
  admin_ssh_key {
    username   = "linuxadmin"
    public_key = var.public_ssh_key
  }


  network_interface_ids = [azurerm_network_interface.hub_vm_nic.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 64

  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }
}

# Create nic for spoke vm
resource "azurerm_network_interface" "spoke_vm_nic" {
  name                  = "nic-${local.env}-${local.region}-spoke-01"
  location              = data.azurerm_resource_group.main_rg.location
  resource_group_name   = data.azurerm_resource_group.main_rg.name
  ip_forwarding_enabled = true



  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.spoke_snet_01.id
    private_ip_address_allocation = "Dynamic"
  }
}

# Create a virtual machine in the spoke vnet
resource "azurerm_linux_virtual_machine" "spoke_vm" {
  name                = "vm-${local.env}-${local.region}-spoke-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location
  size                = "Standard_B2ts_v2"
  admin_username      = "linuxadmin"

  admin_ssh_key {
    username   = "linuxadmin"
    public_key = var.public_ssh_key
  }

  network_interface_ids = [azurerm_network_interface.spoke_vm_nic.id]


  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 64

  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }
}

# Create route table
# destination set to internet route through hub vm
resource "azurerm_route_table" "spoke_route_table" {
  name                = "rt-${local.env}-${local.region}-spoke-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location

}

resource "azurerm_route" "default_to_hub" {
  name                   = "default-to-hub"
  resource_group_name    = data.azurerm_resource_group.main_rg.name
  route_table_name       = azurerm_route_table.spoke_route_table.name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_network_interface.hub_vm_nic.private_ip_address
}

# Set spoke subnet
resource "azurerm_subnet_route_table_association" "spoke_route_table_association" {
  subnet_id      = azurerm_subnet.spoke_snet_01.id
  route_table_id = azurerm_route_table.spoke_route_table.id
}

# Create NSG for hub
resource "azurerm_network_security_group" "nsg_hub" {
  name                = "nsg-${local.env}-${local.region}-hub-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location
}

# Create NSG rule to allow ssh to hub
resource "azurerm_network_security_rule" "hub_allow_ssh" {
  name                        = "AllowSSHFromAdmin"
  priority                    = 300
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  source_address_prefix       = "Internet" # Will change this to use my public ip later on
  destination_port_range      = "22"
  destination_address_prefix  = azurerm_network_interface.hub_vm_nic.private_ip_address
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_hub.name
}

# Create NSG rule to allow traffic from spoke to hub
resource "azurerm_network_security_rule" "hub_allow_traffic_from_spoke" {
  name                        = "AllowInboundFromSpoke"
  priority                    = 310
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "*"
  source_port_range           = "*"
  source_address_prefix       = "10.1.0.0/16"
  destination_port_range      = "*"
  destination_address_prefix  = "Internet"
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_hub.name

}

# Create NSG rule to allow API port to hub
resource "azurerm_network_security_rule" "hub_allow_port_traffic" {
  name                        = "AllowInboundOnAPIPort"
  priority                    = 320
  direction                   = "Inbound"
  protocol                    = "Tcp"
  access                      = "Allow"
  source_port_range           = "*"
  source_address_prefix       = "Internet"
  destination_port_range      = "8080"
  destination_address_prefix  = azurerm_network_interface.hub_vm_nic.private_ip_address
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_hub.name
}

# Associate NSG to hub subnet
resource "azurerm_subnet_network_security_group_association" "hub_subnet_nsg_association" {
  subnet_id                 = azurerm_subnet.hub_snet_01.id
  network_security_group_id = azurerm_network_security_group.nsg_hub.id
}

# Create NSG for spoke
resource "azurerm_network_security_group" "nsg_spoke" {
  name                = "nsg-${local.env}-${local.region}-spoke-01"
  resource_group_name = data.azurerm_resource_group.main_rg.name
  location            = data.azurerm_resource_group.main_rg.location
}

# Create NSG rule to allow ssh from hub
resource "azurerm_network_security_rule" "spoke_allow_ssh_from_hub" {
  name                        = "AllowSSHFromHub"
  priority                    = 300
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  source_address_prefix       = azurerm_network_interface.hub_vm_nic.private_ip_address
  destination_port_range      = "22"
  destination_address_prefix  = "*"
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_spoke.name
}

# Create NSG rule to allow ICMP from hub
resource "azurerm_network_security_rule" "spoke_allow_icmp_from_hub" {
  name                        = "AllowICMPFromHub"
  priority                    = 310
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Icmp"
  source_port_range           = "*"
  source_address_prefix       = azurerm_network_interface.hub_vm_nic.private_ip_address
  destination_port_range      = "*"
  destination_address_prefix  = "*"
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_spoke.name
}

# Create NSG rule to allow API port from hub
resource "azurerm_network_security_rule" "spoke_allow_api_from_hub" {
  name                        = "AllowAPIPortFromHub"
  priority                    = 320
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  source_address_prefix       = azurerm_network_interface.hub_vm_nic.private_ip_address
  destination_port_range      = "8080"
  destination_address_prefix  = "*"
  resource_group_name         = data.azurerm_resource_group.main_rg.name
  network_security_group_name = azurerm_network_security_group.nsg_spoke.name
}

# Associate NSG to spoke subnet
resource "azurerm_subnet_network_security_group_association" "spoke_subnet_nsg_association" {
  subnet_id                 = azurerm_subnet.spoke_snet_01.id
  network_security_group_id = azurerm_network_security_group.nsg_spoke.id
}
