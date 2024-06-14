variable "cloudflare_api_token" {
  type = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
  sensitive = true
}

variable "webserver_subdomain" {
  type = string
  sensitive = false
}

variable "webserver_domain" {
  type = string
  sensitive = false
}

variable "google_cloud_project" {
  type = string
  sensitive = false
}

variable "google_cloud_region" {
  type = string
  sensitive = false
}

variable "ssh_pub_keys" {
  type = list(string)
  sensitive = true
}