terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-dev-ctus"
    storage_account_name = "statftstatedevctus"
    container_name       = "tfstate"
    key                  = "hub_spoke_tf/terrafom.tfstate"
  }
}

provider "github" {
  token = var.terraform_github_pat
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

