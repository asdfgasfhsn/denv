# denv (docker environment)

## Requirements
  - Docker installed and running with your intended user in the docker group (ie you can run docker commands as your intended user)
## Requirements (optional)
  - yq (python yq, basically jq for yaml) If this is not installed in the current path, it will process .denv.yml config using yq within the denv container

## How it works?
These images give you a nice wrapper to run arbitrary commands as well as all of the nodeintegration/denv-\* image commands inside a container as if it was a local binary
```
$ source /dev/stdin <<< "$(docker run nodeintegration/denv:latest boot)"
Binding to tag: latest
```
What this command does is give a denv function in bash:
```
$ type denv| grep function
denv is a function
```
If you are curious what this is exactly doing before you load it into your shell:
```
$ docker run nodeintegration/denv:latest cat /usr/local/bin/boot
$ docker run nodeintegration/denv:latest cat /workspace/bootstrap
```
What this `denv` function does is create a wrapper to run the first argument to denv as a container.
By default the command will run inside the denv container with your current working directory mounted to /workspace. It is also run as your current uid/gid
```
$ cat /etc/issue
Ubuntu 18.04.2 LTS \n \l

$ denv cat /etc/issue
Welcome to Alpine Linux 3.9
Kernel \r on an \m (\l)
```

## .denv.yml
This configuration file for denv allows you to commit specific versions of commands you use within a repository perhaps or on your CI/CD system at the commit level
It is evaulated per command

### Commands run as different docker images/tags
This is where it gets fun.
The function `denv` looks for a file .denv.yml in your current working directory
It then looks for a key: `commands:`
and then if there is a sub key called the first argument you supply to denv ie:
```
cat .denv.yml
commands:
  bash:
```
denv will then change the docker run image to be `bash` for the command `bash`
with the tag of `latest`

Then lets say i want to run an image that doesnt match the command:
```
commands:
  terraform:
    image: hashicorp/terraform
```

denv will then for the command terraform use the `hashicorp/terraform` image with the default tag of `latest`

...ok...ok but i want a specific tag not latest:
```
commands:
  terraform:
    image: hashicorp/terraform
    tag: 0.11.11
```

### I want environment variables passed to the commands run time
Easy peasy:
```
global:
  environment:
    FOO:
    BAR: baz
```
This will give you FOO and BAR as docker run environment variables
It WILL use your current shells environment variables over the .denv.yml value e.g. with the above .denv.yml:
```
$ denv env | grep -E '^(FOO|BAR)'
BAR="baz"
FOO=""

$ FOO="bar" denv env | grep -E '^(FOO|BAR)'
BAR="baz"
FOO=bar
```
## NOTES

denv does not *currently* enforce freshness of docker images
e.g if you have in your .denv.yml to run a command say `bash` as tag `latest` it will use the image that is cached on your docker host, it does not always do a pull on the intended image/tag

