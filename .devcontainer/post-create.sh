#!/bin/bash
set -e

echo "Installing system packages..."
sudo apt-get update
sudo apt-get install -y vim tcpdump network-manager build-essential cmake libssl-dev

echo "Creating Python virtual environment at /opt/hive..."
sudo mkdir -p /opt/hive
sudo chown -R $(whoami):$(whoami) /opt/hive
python3 -m venv /opt/hive

echo "Upgrading pip..."
/opt/hive/bin/pip install --upgrade pip

echo "Installing Python packages..."
/opt/hive/bin/pip install \
    "ansible-core<2.19.0" \
    ansible-dev-tools \
    setuptools \
    hive-builder \
    inquirer \
    google-cloud-compute \
    "PyGithub==2.5.0"

echo "Applying PyGithub patch..."
PYGITHUB_LOCATION=$(/opt/hive/bin/pip show PyGithub | grep Location: | awk '{print $2}')
SCRIPT_DIR=$(dirname "$0")
sudo patch ${PYGITHUB_LOCATION}/github/Repository.py < "${SCRIPT_DIR}/PyGithub.patch"

echo "Setting up bash completion and virtual environment..."
cat >> /home/vscode/.bashrc << 'EOF'

# Activate hive virtual environment
if [ -f /opt/hive/bin/activate ]; then
    source /opt/hive/bin/activate > /dev/null 2>&1
fi

# Setup hive completion
if command -v /opt/hive/bin/hive &> /dev/null; then
    source $(/opt/hive/bin/hive get-install-dir)/hive-completion.sh 2>/dev/null
fi
EOF

echo "Installing Ansible collections..."
WORKSPACE_DIR=$(dirname "${SCRIPT_DIR}")
"${WORKSPACE_DIR}/setup/scripts/install-collection.sh" "${WORKSPACE_DIR}"

echo "Post-create setup completed successfully!"