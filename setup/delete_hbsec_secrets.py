import os
import sys
from github import Github, GithubException

workdir = os.path.dirname(__file__) + "/.."

try:
    gh = Github(os.environ['GITHUB_TOKEN'])
    repo = gh.get_repo(os.environ['GITHUB_REPOSITORY'])
except KeyError as e:
    print(f"Error: Environment variable {e} is not set.", file=sys.stderr)
    sys.exit(1)
except GithubException as e:
    print(f"Error connecting to GitHub: {e}", file=sys.stderr)
    sys.exit(1)

# get and delete secrets
try:
    secrets = repo.get_secrets("codespaces")
    secrets_to_delete = [s for s in secrets if s.name.startswith("HBSEC_")]

    if not secrets_to_delete:
        print("No secrets with prefix 'HBSEC_' found.")
    else:
        for secret in secrets_to_delete:
            try:
                repo.delete_secret(secret.name, "codespaces")
                print(f"{secret.name} deleted")
            except GithubException as e:
                print(f"Failed to delete secret {secret.name}: {e}", file=sys.stderr)
        print("All specified secrets have been processed.")

except GithubException as e:
    print(f"Error getting secrets from repository: {e}", file=sys.stderr)
    sys.exit(1)

