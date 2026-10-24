variable "public_ssh_key" {
  type        = string
  description = "The public SSH key to access the virtual machine."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "repository_name" {
  type        = string
  description = "The name of the GitHub repository."
}

variable "terraform_github_pat" {
  type        = string
  description = "The GitHub token to access the repository."
  sensitive   = true
}


