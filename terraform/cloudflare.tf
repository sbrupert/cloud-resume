data "cloudflare_ip_ranges" "cf_ingress" {
}

resource "cloudflare_record" "cloud_resume" {
  zone_id = var.cloudflare_zone_id
  name    = var.webserver_subdomain
  # This dynamically sets the value of our DNS record to whatever the public IP of our GCP instance is.
  content = resource.google_compute_instance.web01.network_interface.0.access_config.0.nat_ip
  type    = "A"
  proxied = true
  # Prevents the record from being created before our GCP instance. Which would cause the run to fail.
  depends_on = [google_compute_instance.web01]
}