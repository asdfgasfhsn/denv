#!/usr/bin/env python

import io
import yaml
import argparse
import sys

# Set global defaults
docker_run_prefix='docker run --rm -u $(id -u):$(id -g) ${DENV_GLOBALS}'

def load_denv_yaml():
  '''
  Load .denv.yml from CWD, return as a dict.
  '''
  try:
    with open(".denv.yml", 'r') as stream:
      denv_data = yaml.load(stream)
    return denv_data
  except IOError:
    print('Unable to find .denv.yml, qutting.')
    sys.exit(1)


def generate_docker_commands(denv_commands):
  '''
  Generates a docker run command for each command described in .denv.yml
  Returns a dict:
    {'denv_command_name': 'docker_command'}

  example dict:
    {'make': 'docker run --rm -u $(id -u):$(id -g) ${DENV_GLOBALS}   make:latest ',
     'make_stuff': 'docker run --rm -u $(id -u):$(id -g) ${DENV_GLOBALS} -it  make:latest make stuff'}
  '''
  ret = {}

  for command in denv_commands:
    denv_command = denv_commands[command]
    denv_name = command

    # Set blank values for items that can be blank
    denv_cmd = ''
    denv_interactive = ''
    denv_mounts = ''

    denv_image = denv_command['image']

    if 'tag' in denv_command:
      denv_tag = denv_command['tag']
    else:
      denv_tag = 'latest'

    if 'cmd' in denv_command:
      denv_cmd = denv_command['cmd']

    if 'interactive' in denv_command:
      denv_interactive = '-it'

    if 'mounts' in denv_command:
      for mount in denv_command['mounts']:
        denv_mounts += '-v {mount_local}:{mount_container} '.format(mount_local=denv_command['mounts'][mount]['local'],
                                                                    mount_container=denv_command['mounts'][mount]['container'])

    denv_docker_args='{denv_interactive} {denv_mounts} {denv_image}:{denv_tag} {denv_cmd}'.format(denv_interactive=denv_interactive,
                                                                                                  denv_image=denv_image,
                                                                                                  denv_tag=denv_tag,
                                                                                                  denv_cmd=denv_cmd,
                                                                                                  denv_name=denv_name,
                                                                                                  denv_mounts=denv_mounts)

    docker_cmd = ('{docker_run_prefix} {denv_docker_args}'.format(docker_run_prefix=docker_run_prefix,
                                                                  denv_docker_args=denv_docker_args))

    ret[denv_name] = docker_cmd

  return ret


def print_docker_shell_vars(docker_commands):
  for denv_command in docker_commands:
      print('denv_{denv_command}="{docker_command}"'.format(denv_command=denv_command,
                                                            docker_command=docker_commands[denv_command]))
  return 0


def print_docker_shell_functions(docker_commands):
  for denv_command in docker_commands:
      print('function denv_{denv_command}() {{\n  {docker_command}\n}}'.format(denv_command=denv_command,
                                                                               docker_command=docker_commands[denv_command]))
  return 0


def print_denv_global_vars(denv_yaml):
  denv_yaml = denv_yaml
  DENV_GLOBALS = ''
  try:
     global_envs = denv_yaml['global']['environment']
     for k in global_envs:
       DENV_GLOBALS += '-e {key}={value} '.format(key=k,value=denv_yaml['global']['environment'][k])
  except KeyError:
    pass

  print('DENV_GLOBALS="{0}"'.format(DENV_GLOBALS))

  return 0

def unset_denv_commands(denv_commands,unset_type):
  '''
  Unsets denv created things.
  '''
  if unset_type == 'func':
    unset_arg = '-f'
  else:
    unset_arg = ''

  print ('unset DENV_GLOBALS')
  for command in denv_commands:
    print('unset {unset_arg} denv_{command}'.format(unset_arg=unset_arg, command=command))
  return 0

def main():
  '''
  Parse args and then call functionality...
  '''
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  outputs = parser.add_mutually_exclusive_group()
  group.add_argument("-b", "--bootstrap", help="denv bootstrap", action="store_true")
  group.add_argument("-u", "--unset", help="unsets denv bootstrap", action="store_true")
  outputs.add_argument("--var", help="bootstrap denv commands as shell variables", action='store_true')
  outputs.add_argument("--func", help="bootstrap denv commands as shell functions", action="store_true")
  args = parser.parse_args()

  denv_yaml = load_denv_yaml()
  denv_commands = denv_yaml['commands']

  if args.bootstrap:
    print('\n### DENV Global Environment Overides')
    print_denv_global_vars(denv_yaml)
    if args.var:
      print('\n### DENV Shell Variables')
      print_docker_shell_vars(generate_docker_commands(denv_commands))
    if args.func:
      print('\n### DENV Shell Functions')
      print_docker_shell_functions(generate_docker_commands(denv_commands))
    print('')

  if args.unset:
    if args.var:
      unset_type='var'
    elif args.func:
      unset_type='func'
    else:
      print('Please define what --var/--func')
      sys.exit(1)

    unset_denv_commands(denv_commands, unset_type)


# Main entry point...

if __name__ == "__main__": main()
