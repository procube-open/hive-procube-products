import os
import shutil
import subprocess
import gnupg
import string
import random
import sys
from github import Github, GithubException

workdir = os.path.dirname(__file__) + "/.."
tmpdir = '/tmp'
secrets_dir = os.path.join(tmpdir, 'secrets')
secrets_zip = os.path.join(tmpdir, 'secrets.zip')
gnupg_home = os.path.join(tmpdir, '.gnupg')

try:
    gh = Github(os.environ['GITHUB_TOKEN'])
    repo = gh.get_repo(os.environ['GITHUB_REPOSITORY'])
except KeyError as e:
    print(f"Environment variable {e} is not set.", file=sys.stderr)
    sys.exit(1)

workdir_secrets = ['secrets.yml', 'gcp_credential.json', '.env']
stages = ["private", "staging", "production"]
skip_files = ["Vagrantfile", "vagrant.log", "vagrant_vars.yml", "growfs.sh", ".vagrant"]

try:
    # Create secrets.zip
    if os.path.exists(secrets_dir):
        shutil.rmtree(secrets_dir)
    if os.path.exists(secrets_zip):
        os.remove(secrets_zip)
    os.makedirs(secrets_dir, exist_ok=True)
    for secret in workdir_secrets:
        src_path = os.path.join(workdir, secret)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(secrets_dir, secret))

    hive_secrets_dir = os.path.join(secrets_dir, '.hive')
    os.makedirs(hive_secrets_dir, exist_ok=True)
    
    persistents_src = os.path.join(workdir, '.hive', 'persistents.yml')
    if os.path.exists(persistents_src):
        shutil.copy2(persistents_src, os.path.join(hive_secrets_dir, 'persistents.yml'))

    for stage in stages:
        stage_src_dir = os.path.join(workdir, '.hive', stage)
        if os.path.exists(stage_src_dir):
            stage_dest_dir = os.path.join(hive_secrets_dir, stage)
            os.makedirs(stage_dest_dir, exist_ok=True)
            for file in os.listdir(stage_src_dir):
                if file in skip_files:
                    continue
                src_file_path = os.path.join(stage_src_dir, file)
                dest_file_path = os.path.join(stage_dest_dir, file)
                if os.path.isdir(src_file_path):
                    shutil.copytree(src_file_path, dest_file_path)
                else:
                    shutil.copy2(src_file_path, dest_file_path)

    subprocess.run(['zip', '-r', 'secrets.zip', 'secrets'], stdout=subprocess.DEVNULL, cwd=tmpdir, check=True)
    print("secrets.zip created")

    # Generate passphrase
    length = 32
    characters = string.ascii_letters + string.digits + string.punctuation
    passphrase = ''.join(random.choice(characters) for i in range(length))
    print("passphrase generated")

    # Encrypt secrets.zip
    os.makedirs(gnupg_home, exist_ok=True)
    gpg = gnupg.GPG(gnupghome=gnupg_home)
    gpg.encoding = 'utf-8'
    gpg_file = os.path.join(workdir, 'secrets.gpg')
    with open(secrets_zip, 'rb') as f:
        encrypted_secrets = gpg.encrypt_file(f, recipients=None, symmetric=True, output=gpg_file, passphrase=passphrase)
    
    if not encrypted_secrets.ok:
        print(f"Failed to encrypt secrets.zip: {encrypted_secrets.status}", file=sys.stderr)
        print(encrypted_secrets.stderr, file=sys.stderr)
        sys.exit(1)
    print("secrets.zip encrypted to secrets.gpg with passphrase")

    # Export HBSEC_PASSPHRASE
    try:
        repo.create_secret("HBSEC_PASSPHRASE", passphrase, "codespaces")
        print("passphrase exported to GitHub repository secret HBSEC_PASSPHRASE")
    except GithubException as e:
        print(f"Failed to create GitHub secret: {e}", file=sys.stderr)
        print("Please set the passphrase manually as a repository secret 'HBSEC_PASSPHRASE'.", file=sys.stderr)
        print(f"PASSPHRASE: {passphrase}")
        sys.exit(1)

finally:
    # Remove temporary files
    if os.path.exists(secrets_dir):
        shutil.rmtree(secrets_dir)
    if os.path.exists(gnupg_home):
        shutil.rmtree(gnupg_home)
    if os.path.exists(secrets_zip):
        os.remove(secrets_zip)
    print("/tmp/secrets and related files removed")
