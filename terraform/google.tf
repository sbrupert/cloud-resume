# GCP Related Resources
data "google_compute_image" "ubuntu-22-lts" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
  most_recent = true
}

resource "google_compute_instance" "web01" {
  machine_type = "e2-micro"
  name         = "web01"
  zone = "us-east1-b"
  labels = {
    instance_function = "webserver"
  }
  boot_disk {
    auto_delete = true
    initialize_params {
      image = data.google_compute_image.ubuntu-22-lts.self_link
      size  = 30
      type  = "pd-standard"
    }

    mode = "READ_WRITE"
  }
  network_interface {
    network = resource.google_compute_network.webserver_vpc.self_link
    access_config {}
  }
  scheduling {
    on_host_maintenance = "MIGRATE"
  }
  metadata = {
    user-data = templatefile("${path.module}/cloud-init.tftpl", {ssh_pub_keys = var.ssh_pub_keys})
  }
}

# Firestore Related Resources

resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.google_cloud_region
  type        = "FIRESTORE_NATIVE"
}

# VPC Related Resources
resource "google_compute_network" "webserver_vpc" {
  name                    = "webserver-vpc"
  auto_create_subnetworks = true
}

resource "google_compute_firewall" "webserver_ssh_ingress" {
  name    = "webserver-ssh-ingress"
  network = resource.google_compute_network.webserver_vpc.self_link
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  # Not a great security practice. But my ISP issues dynamic public IPs so I can't hardcode my own IP.
  # Instead we will mitigate this risk by installing fail2ban on the webserver.
  source_ranges = ["0.0.0.0/0"]
  description   = "Allow SSH traffic from anywhere to webservers."
}

resource "google_compute_firewall" "webserver_http_ingress" {
  name    = "webserver-http-ingress"
  network = resource.google_compute_network.webserver_vpc.self_link
  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  source_ranges = ["0.0.0.0/0"]
  description   = "Allow all HTTP traffic to webservers."
}

resource "google_compute_firewall" "webserver_https_ingress" {
  name    = "webserver-https-ingress"
  network = resource.google_compute_network.webserver_vpc.self_link
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  source_ranges = ["0.0.0.0/0"]
  description   = "Allow all HTTPS traffic to webservers."
}

resource "google_compute_firewall" "webserver_egress" {
  name    = "webserver-egress"
  network = resource.google_compute_network.webserver_vpc.self_link
  direction = "EGRESS"
  allow {
    protocol = "all"
  }
  # This way our webserver can access the package repositories and other resources it needs.
  # If we could use URLs instead of IPs, then we could list all the domains we want to whitelist.
  destination_ranges = ["0.0.0.0/0"]
  description        = "Allow webservers to reach anywhere."
}