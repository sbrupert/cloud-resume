resource "cloudflare_record" "cloud_resume" {
  zone_id = var.cloudflare_zone_id
  name = var.webserver_subdomain
  value = resource.google_compute_instance.web01.network_interface.0.access_config.0.nat_ip
  type = "A"
  proxied = false
  depends_on = [ google_compute_instance.web01 ]
}