#!/usr/local/bin/pwsh

$pwd=(Get-Location).Path

docker run -p 5000:3547 -v $pwd/uploads:/uploads -v $pwd/config.yaml:/app/config.yaml -it --rm $(docker build -q .)
