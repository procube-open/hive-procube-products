FROM mcr.microsoft.com/vscode/devcontainers/python:3

RUN apt-get update
RUN apt-get install -y vim tcpdump network-manager ca-certificates curl

RUN apt-get install -y systemd
RUN ln -sf /lib/systemd/systemd /sbin/init

# Install Docker
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
RUN usermod -aG docker vscode

# Make virtual environment
RUN python3 -m venv /opt/hive
RUN chown -hR vscode:vscode /opt/hive

# Install Python packages
RUN /opt/hive/bin/pip install --upgrade pip
# ansible-core>=2.19.0 でyamlのパースに失敗するため、バージョンを下げる
RUN /opt/hive/bin/pip install 'ansible-core<2.19.0' ansible-dev-tools setuptools hive-builder inquirer google-cloud-compute 'PyGithub==2.5.0'

# Patch PyGithub
COPY PyGithub.patch /tmp/PyGithub.patch
RUN patch $(/opt/hive/bin/pip show PyGithub | grep Location: | awk '{print $2}')/github/Repository.py < /tmp/PyGithub.patch
RUN rm /tmp/PyGithub.patch

# Setup hive-builder
RUN echo "source \$(/opt/hive/bin/hive get-install-dir)/hive-completion.sh" >> /home/vscode/.bashrc

ENTRYPOINT ["/sbin/init"]