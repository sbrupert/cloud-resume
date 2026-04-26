# Cloud Resume - Terraform
<img class="rounded mx-auto d-block" src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Terraform_Logo.svg/1280px-Terraform_Logo.svg.png" alt="terraform logo" width="500" />

This directory contains the Terraform code used to provision the cloud-resume infrastructure. It creates the GCP and Cloudflare resources that support the public resume site.

Terraform handles infrastructure provisioning only. Application deployment and host configuration are handled separately through Ansible and GitHub Actions.

## Providers

This project uses providers for [Google Cloud Platform (GCP)](https://registry.terraform.io/providers/hashicorp/google/latest) and [Cloudflare](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs).

## Resources

The Terraform code creates the following resources:

- 1 Compute Engine instance.
- 1 Firestore Database instance.
- Firewall and service account resources for managing access between resources.
- 1 Cloudflare DNS record.

For implementation details, review the `.tf` files in this directory.

## HCP Terraform

Many Terraform projects store state in an object storage bucket such as S3 or Google Cloud Storage, or in a self-managed CI/CD platform. This project uses HashiCorp's HCP Terraform instead.

HCP Terraform manages the state file, Terraform version, execution environment, and workspace variables. For this project, it is used to manage state, execute Terraform runs, and store required secrets.

Terraform runs are integrated with GitHub Actions. Pull requests trigger a Terraform plan, and the plan summary is written back as a pull request comment for review.

![Terraform PR Comment Example](/.assets/terraform_plan_pr_comment.png)

### Why GCP?

GCP was selected for this project because its [free tier](https://cloud.google.com/free?hl=en) includes several resources that fit a small resume site. The two major services used here are:

1. One [e2-micro Compute Engine instance](https://cloud.google.com/free/docs/free-cloud-features#compute)
2. One Firestore database with the following [limitations](https://cloud.google.com/free/docs/free-cloud-features#firestore):
   - 1GB storage per project
   - 50,000 reads, 20,000 writes, and 20,000 deletes per day, per project

### Why Cloudflare?

Cloudflare hosts the domain where the website is reachable. Cloudflare does not charge usage fees for common DNS-related items such as record queries and hosted zones.

By using Cloudflare DNS, the site can use Cloudflare's [proxy feature](https://developers.cloudflare.com/dns/manage-dns-records/reference/proxied-dns-records/). This provides caching and DDoS protection in front of the origin server.

Caching helps make the most of the small GCP instance by reducing origin load and limiting unnecessary outbound traffic.
