# Cloud Resume - Ansible

<img class="rounded mx-auto d-block" src="https://cdn.icon-icons.com/icons2/2699/PNG/512/ansible_logo_icon_169596.png" alt="ansible logo" width="400" />

This directory contains the Ansible code used to configure and operate the cloud-resume webserver. Terraform provisions the infrastructure, while Ansible prepares the host, installs required services, and deploys the application container.

## Playbooks

[`install_updates.yaml`](/ansible/install_updates.yaml) - Updates packages and reboots the server when needed. Runs periodically using GitHub Actions.

[`playbook.yaml`](/ansible/playbook.yaml) - Main playbook for configuring the webserver and deploying the application container. See the sections below for an overview of the playbook's responsibilities.

## Inventory

This project uses the [GCP Compute dynamic inventory plugin](https://docs.ansible.com/ansible/latest/collections/google/cloud/gcp_compute_inventory.html) to discover the GCP instances used by the site.

Dynamic inventory is more than this single-host deployment strictly requires, but it avoids hardcoding connection details and keeps the deployment pattern scalable.

## Webserver Configuration

The Ansible playbook used to set up the webserver configures the following items:

1. [Fail2Ban](#fail2ban)
2. [Docker](#docker)
3. [Caddy](#caddy)
4. [Datadog](#datadog)

### Fail2Ban

Fail2Ban helps protect SSH access on the GCP instance. It monitors authentication attempts and bans IPs with excessive failed logins.

On a small instance, reducing repeated failed login traffic also helps preserve host resources during brute force attempts.

### Docker

Docker runs the application as a container. The container packages the application and its dependencies together, which keeps deployment consistent and limits conflicts with other host software.

The Docker Ansible role [in this repo](/ansible/roles/docker) installs Docker on the host. Once Docker is installed, the main [playbook](/ansible/playbook.yaml#L61) launches the application container:

```yaml
- name: Start container
    community.docker.docker_container:
    name: cloud-resume
    image: "{{ webserver_image }}"
    state: started
    recreate: true
    restart_policy: "always"
    pull: "always"
    published_ports: "8080:{{ webserver_port }}"
    etc_hosts:
        host.docker.internal: host-gateway
    env:
        DD_SERVICE: "resume-website"
        DD_ENV: "cloud-resume-prod"
    labels:
        com.datadoghq.tags.env: cloud-resume-prod
        com.datadoghq.tags.service: resume-website
    tags: deploy
```

### Caddy

[Caddy](https://caddyserver.com/) runs in front of the application as the public reverse proxy.

```txt
:80 {
        reverse_proxy localhost:8080
}
resume.sbrtech.xyz:443 {
        reverse_proxy localhost:8080
}
```

Those lines configure Caddy as a reverse proxy with automatic HTTPS, keeping certificate management and renewals out of the application container.

The [Caddy Ansible role](/ansible/roles/caddy) installs the Caddy binary, creates a systemd service, and generates the Caddyfile used by the site.

### Datadog

The Datadog agent collects host metrics, traces, and logs, then forwards them to Datadog for monitoring and troubleshooting. This project uses Datadog's published [Ansible role](https://github.com/DataDog/ansible-datadog?tab=readme-ov-file) to install and configure the agent.

The agent settings are defined as Ansible group variables in [`group_vars/webserver.yaml`](/ansible/group_vars/webserver.yaml).

## Operational Notes

- The main deployment path is driven by GitHub Actions, which runs Ansible after the container image is available.
- The playbooks assume Terraform has already created the target infrastructure and service account access.
- Secrets and environment-specific values should stay in the configured CI/CD or Ansible variable sources rather than being committed directly to this directory.
