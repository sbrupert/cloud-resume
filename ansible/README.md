# Cloud Resume - Ansible

<img class="rounded mx-auto d-block" src="https://cdn.icon-icons.com/icons2/2699/PNG/512/ansible_logo_icon_169596.png" alt="terraform logo" width="400" /> 

Welcome to the Ansible part of the project! This directory contains all the Ansible code needed to configure and manage the infrastructure for our cloud-resume app.

## Playbooks

[`install_updates.yaml`](/ansible/install_updates.yaml) - Updates all packages and reboots the server when needed. Runs periodically using Github Actions.

[`playbook.yaml`](/ansible/playbook.yaml) - The main playbook for configuring the webserver. See the next section for an overview of the playbooks contents.

## Inventory

We are using the [GCP Compute dynamic inventory plugin](https://docs.ansible.com/ansible/latest/collections/google/cloud/gcp_compute_inventory.html) to discover the GCP instances used in our project.

While a dynamic inventory may not provide much benefit with a single host, it's scalable for future growth, and allows us to not have to define the connection details statically.

## Webserver Configuration

The ansible playbook used to setup our webserver host configures the following items:

1. [Fail2Ban](#fail2ban)
2. [Docker](#docker)
3. [Caddy](#caddy)
4. [Datadog](#datadog)

### Fail2Ban

To protect against brute force attacks on our GCP instance's SSH access, we use Fail2Ban. It monitors authentication attempts and bans IPs with excessive failed logins.

With the limited resources of our GCP instance, banning attackers could also significantly increase performance during brute force attacks.

### Docker

Docker is used to run our application as a container. Containers allow us to bundle our application and it's dependencies together. This simplifies the deployment of our app since we don't have to worry about potential conflicts with other software running on the server.

The Docker ansible role [in this repo](/ansible/roles/docker) handles installing Docker onto our host. Once installed, our main [playbook](/ansible/playbook.yaml#L61) will launch our application's container:

```yaml
- name: Start container
    community.docker.docker_container:
    name: cloud-resume
    image: "{{ webserver_image }}"
    state: started
    restart_policy: "always"
    pull: "always"
    published_ports: "8080:{{ webserver_port }}"
    labels:
        com.datadoghq.tags.env: cloud-resume-prod
        com.datadoghq.tags.service: resume-website
    tags: deploy
```

### Caddy

Sitting in front of our application is [Caddy](https://caddyserver.com/). Caddy is a powerful, simple, and easy to use webserver.

```txt
:80 {
        reverse_proxy localhost:8080
}
resume.sbrtech.xyz:443 {
        reverse_proxy localhost:8080
}
```

Those 6 lines above are all we need to configure Caddy as a reverse proxy with automatic HTTPS. No need to think about certificate management or renewals.

I've written an [ansible role](/ansible/roles/caddy) that installs the Caddy binary, creates a systemd service, and generates the Caddyfile needed to configure our website.

### Datadog

In order to monitor our application and the server running it, we need to install the Datadog agent. The agent will collect metrics, traces, and logs, then forward them to the Datadog console. To configure the agent, Datadog has created an excellent [ansible role](https://github.com/DataDog/ansible-datadog?tab=readme-ov-file).

To use the role, we need to define the variables that'll configure the agent with the features and settings we want. These variables are defined as ansible group vars and can be seen [here](/ansible/group_vars/webserver.yaml).
