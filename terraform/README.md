# Cloud Resume - Terraform 
<img class="rounded mx-auto d-block" src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Terraform_Logo.svg/1280px-Terraform_Logo.svg.png" alt="terraform logo" width="500" /> 

Welcome to the Terraform part of the project! This directory contains all the Terraform code needed to create the infrastructure for our cloud-resume app.

## Providers

For this project, we are using a combination of services from [Google Cloud Platform (GCP)](https://registry.terraform.io/providers/hashicorp/google/latest) and [Cloudflare](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs).

## Resources

Our Terraform code will create the following resources:

- 1 Compute Engine instance.
- 1 Firestore Database instance.
- Various firewall and service account resources for managing access between resources.
- 1 Cloudflare DNS record.

For more details, check out the various Terraform files in this directory!

## HCP Terraform

Most engineers typically store their Terraform state file in an storage bucket (S3, Google Cloud Storage Bucket, etc.) or in their CI/CD platform if it's self managed. While Google does include up to 5GB of CLoud Storage, I wanted to give Hashicorp's "HCP Terraform" a shot.

HCP Terraform is a SaaS Terraform option by Hashicorp. They handle managing your state file, Terraform version, execution environment and more. For this project, I'm using them to manage my state file, execute Terraform runs, and storing my secrets.

Terraform runs are integrated with Github Actions and are fully automated. Pull requests trigger a terraform plan and the output summary is even written as a comment for quick reference!

![Terraform PR Comment Example](/.assets/terraform_plan_pr_comment.png)

### Why GCP?

GCP was selected over AWS due to their generous [free tier](https://cloud.google.com/free?hl=en) that does not expire. The two major services we are utilizing from this are:

1. One [e2-micro Compute Engine instance](https://cloud.google.com/free/docs/free-cloud-features#compute)
2. One Firestore database with the following [limitations](https://cloud.google.com/free/docs/free-cloud-features#firestore):
   - 1GB storage per project
   - 50,000 reads, 20,000 writes, and 20,000 deletes per day, per project

### Why Cloudflare?

Cloudflare hosts the domain where our website will be reachable. Cloudflare does not charge "usage" fees for DNS-related items such as record queries, hosted zones, etc.

By using Cloudflare to host our domain, we can utilize their [proxy feature](https://developers.cloudflare.com/dns/manage-dns-records/reference/proxied-dns-records/). This provides us with caching and DDoS protection.

Caching can help us make the most of our e2-micro instance by reducing the load from visitor traffic, outbound data transfer fees, and more.
