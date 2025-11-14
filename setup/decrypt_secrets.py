import os
import gnupg
import shutil
import subprocess
import sys

workdir = os.path.dirname(__file__) + "/.."
tmpdir = '/tmp'
secrets_dir = os.path.join(tmpdir, 'secrets')
gnupg_home = os.path.join(tmpdir, '.gnupg')
secrets_zip = os.path.join(tmpdir, 'secrets.zip')

if not os.getenv('HBSEC_PASSPHRASE'):
    print("HBSEC_PASSPHRASE is not set", file=sys.stderr)
    sys.exit(1)

try:
    # Decrypt secrets.gpg
    os.makedirs(secrets_dir, exist_ok=True)
    os.makedirs(gnupg_home, exist_ok=True)
    gpg = gnupg.GPG(gnupghome=gnupg_home)
    gpg.encoding = 'utf-8'
    gpg_file = os.path.join(workdir, 'secrets.gpg')
    passphrase = os.getenv('HBSEC_PASSPHRASE')
    
    with open(gpg_file, 'rb') as f:
        decrypted_result = gpg.decrypt_file(f, passphrase=passphrase, output=secrets_zip)

    if not decrypted_result.ok:
        print(f"Failed to decrypt secrets.gpg: {decrypted_result.status}", file=sys.stderr)
        print(decrypted_result.stderr, file=sys.stderr)
        sys.exit(1)
    print("secrets.gpg decrypted to secrets.zip")

    # Extract secrets.zip
    subprocess.run(['unzip', '-o', 'secrets.zip'], stdout=subprocess.DEVNULL, cwd=tmpdir, check=True)
    print(f"secrets.zip extracted to {secrets_dir}")
    for secret in os.listdir(secrets_dir):
        src_path = os.path.join(secrets_dir, secret)
        dst_path = os.path.join(workdir, secret)
        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                answer = input(f"{secret} already exists. Overwrite? [y/N]: ")
                if answer.lower() != 'y':
                    continue
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            if os.path.exists(dst_path):
                answer = input(f"{secret} already exists. Overwrite? [y/N]: ")
                if answer.lower() != 'y':
                    continue
                os.remove(dst_path)
            shutil.copy2(src_path, dst_path)

finally:
    # Remove temporary files
    if os.path.exists(secrets_dir):
        shutil.rmtree(secrets_dir)
    if os.path.exists(gnupg_home):
        shutil.rmtree(gnupg_home)
    if os.path.exists(secrets_zip):
        os.remove(secrets_zip)
    print("/tmp/secrets and related files removed")
