#!/usr/local/bin/pwsh
# check if there are uncommitted changes
if (git diff-index --quiet HEAD --) {
    Write-Host "There are uncommitted changes. Please commit or stash them before running this script."
    exit 1
}

docker-compose build
docker tag ghcr.io/maxfire2008/flipbook-app:latest ghcr.io/maxfire2008/flipbook-app:$(git describe --tags --always)
docker tag ghcr.io/maxfire2008/flipbook-app:latest ghcr.io/maxfire2008/flipbook-app:stable
docker push ghcr.io/maxfire2008/flipbook-app --all-tags
ssh -t max@192.168.86.25 "cd ~/flipbook-app && ~/flipbook-app/reset.sh"
