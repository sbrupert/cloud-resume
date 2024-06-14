terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 5.32.0"
    }
    cloudflare = {
      source = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.google_cloud_project
  region = var.google_cloud_region
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}