# GCP Related Resources
# This looks up the official Ubuntu 22 LTS GCP image so we can create our instance from it.
data "google_compute_image" "ubuntu-22-lts" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
  most_recent = true
}

resource "google_compute_instance" "web01" {
  machine_type = "e2-micro"
  name         = "web01"
  zone = "us-east1-b" # Could also be "us-west1" or "us-central1" and be eligible for the free tier.
  labels = {
    instance_function = "webserver"
    env = "cloud-resume-prod"
  }
  boot_disk {
    auto_delete = true
    initialize_params {
      image = data.google_compute_image.ubuntu-22-lts.self_link
      size  = 30 # Currently the largest disk we can use and stay within the free tier.
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
  # The metadata parameter is used to supply our user-data config file to Cloud-Init.
  # This allows us to customize our instance with users, ssh keys, and more during it's creation.
  metadata = {
    user-data = templatefile("${path.module}/cloud-init.tftpl", {ssh_pub_keys = var.ssh_pub_keys})
  }
  service_account {
    email = google_service_account.webserver_sa.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    ignore_changes = [ boot_disk[0].initialize_params.image ]
  }
}

# Firestore Related Resources

resource "google_firestore_database" "database" {
  name        = "(default)" # The firestore database must be named this to be counted by the free tier.
  # There does not appear to be a restriction for where we can run the database. https://cloud.google.com/firestore/pricing
  # However, we should keep it in the same region as our gcp instance for best performance.
  location_id = var.google_cloud_region
  type        = "FIRESTORE_NATIVE"
}

# IAM Related Resources
# By using IAM resources, we can allow our Webserver to access the Firestore database without having to manage secrets.
# NOTE: We could restrict our service account so the webserver would only be able to access it's own Firestore database.
#       However, since IAM Service Accounts are scoped by project and we do not have any other databases in this project,
#       the webserver won't be able to access any other database aside from it's own.
resource "google_service_account" "webserver_sa" {
  account_id = "webserver"
  description = "Service account for webservers."
}

resource "google_project_iam_member" "webserver_db_access" {
  project = var.google_cloud_project
  # Default GCP role that provides read/write access to a Datastore database. https://cloud.google.com/iam/docs/understanding-roles#datastore.user
  # Even though it doeds not explicitly mention "Firestore", this is the correct role for our use case. 
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.webserver_sa.email}"
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

# Note: Our ingress rules are overly permissive. This is fine if we aren't going to use Cloudflare and directly serve the site to visitors.
#       But if our website will be behind Cloudflare's proxy, we should restrict access to Cloudflare-owned IPs: https://www.cloudflare.com/ips/       
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
  # If we could use URLs instead of IPs, then we could list all the domains we want to whitelist. However, this isn't supported by GCP at the moment.
  destination_ranges = ["0.0.0.0/0"]
  description        = "Allow webservers to reach anywhere."
}