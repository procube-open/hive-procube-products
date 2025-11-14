import subprocess
import getpass
import os
import yaml
import inquirer
import time
import json
from google.cloud import compute_v1
import boto3

user = getpass.getuser()
dir = os.path.dirname(__file__)

# Ask questions
print('--- Ask questions ---')
try:
    def require_validation(base_answers, current):
        if len(current) == 0:
            return False
        return True

    base_questions = [
        inquirer.Text('name',
                      message="What's hive name?",
                      validate=require_validation,
                      ),
        inquirer.List('stage',
                      message="What stage do you want to use?",
                      choices=['private', 'staging', 'production'],
                      )
    ]
    base_answers = inquirer.prompt(base_questions, raise_keyboard_interrupt=True) or {}

    provider_questions = [
        inquirer.List('provider',
                      message="What provider do you want to use?",
                      choices=['vagrant', 'gcp', 'aws', 'azure', 'kickstart', 'prepared'],
                      )
    ]
    provider_answers = inquirer.prompt(provider_questions, raise_keyboard_interrupt=True) or {}

    stage_base_questions = [
        inquirer.Text('cidr',
                      message="What's the CIDR?",
                      default='192.168.0.0/16'
                      ),
        inquirer.Text('internal_cidr',
                      message="What's the internal CIDR?",
                      default='172.31.252.0/22'
                      ),
        inquirer.Confirm('separate_repository',
                         message="Do you want to use a separate repository?",
                         default=False,
                         )
    ]
    stage_base_answers = inquirer.prompt(stage_base_questions, raise_keyboard_interrupt=True) or {}
    default_number = '1'
    if provider_answers['provider'] != 'vagrant':
        if stage_base_answers['separate_repository']:
            default_number = '4'
        else:
            default_number = '3'
    number_of_hosts_questions = [
        inquirer.Text('number_of_hosts',
                      message="How many hosts do you want to create?",
                      validate=lambda _, x: x.isdigit(),
                      default=default_number
                      )
    ]
    number_of_hosts_answers = inquirer.prompt(number_of_hosts_questions, raise_keyboard_interrupt=True) or {}
    number_of_hosts_answers['number_of_hosts'] = int(number_of_hosts_answers['number_of_hosts'])

    vagrant_answers = {}
    if provider_answers['provider'] == 'vagrant':
        vagrant_questions = [
            inquirer.Text('cpus',
                          message="How many cpus do you want to use?",
                          default='2'
                          ),
            inquirer.Text('memory_size',
                          message="How much memory do you want to use?(MB)",
                          default='4096'
                          ),
        ]
        vagrant_answers = inquirer.prompt(vagrant_questions, raise_keyboard_interrupt=True) or {}
        vagrant_answers['cpus'] = int(vagrant_answers['cpus'])
        vagrant_answers['memory_size'] = int(vagrant_answers['memory_size'])
        vagrant_answers['repository_memory_size'] = int(vagrant_answers['memory_size'])

    gcp_region_answers = {}
    gcp_machine_type_answers = {}
    if provider_answers['provider'] == 'gcp':
        gcp_credential_path = dir + '/../gcp_credential.json'
        if not os.path.exists(gcp_credential_path):
            gcp_credential_questions = [
                inquirer.Editor('gcp_credential',
                                message="Please paste GCP credential json",
                                )
            ]
            gcp_credential_answers = inquirer.prompt(gcp_credential_questions, raise_keyboard_interrupt=True) or {}
            with open(gcp_credential_path, 'w') as file:
                file.write(gcp_credential_answers['gcp_credential'])

        def get_available_regions(projectid: str, credential: str):
            client = compute_v1.RegionsClient.from_service_account_json(credential)
            request = compute_v1.ListRegionsRequest(project=projectid)
            result = client.list(request=request)
            return result
        with open(gcp_credential_path) as file:
            credential = json.load(file)
            project_id = credential['project_id']
            available_regions = get_available_regions(project_id, gcp_credential_path)
        regions = []
        for region in available_regions:
            regions.append(region.name)
        gcp_region_questions = [
            inquirer.List('region',
                          message="What region do you want to use?",
                          choices=regions,
                          default='asia-northeast1' if 'asia-northeast1' in regions else regions[0]
                          )
        ]
        gcp_region_answers = inquirer.prompt(gcp_region_questions, raise_keyboard_interrupt=True) or {}

        def get_machine_types(credentials: str, region: str):
            client = compute_v1.MachineTypesClient.from_service_account_json(credentials)
            request = compute_v1.ListMachineTypesRequest(project=project_id, zone=region + '-a')
            result = client.list(request=request)
            return result
        machine_types = get_machine_types(gcp_credential_path, gcp_region_answers['region'])
        machine_types_list = []
        for machine_type in machine_types:
            machine_types_list.append(machine_type.name)
        gcp_machine_type_questions = [
            inquirer.List('instance_type',
                          message="What machine type do you want to use?",
                          choices=machine_types_list,
                          default='n1-standard-2' if 'n1-standard-2' in machine_types_list else machine_types_list[0]
                          )
        ]
        gcp_machine_type_answers = inquirer.prompt(gcp_machine_type_questions, raise_keyboard_interrupt=True) or {}
        gcp_machine_type_answers['repository_instance_type'] = gcp_machine_type_answers['instance_type']

    aws_region_answers = {}
    aws_machine_type_answers = {}
    subnet_answers = {}
    if provider_answers['provider'] == 'aws':
        aws_credential_answers = {}
        if not os.path.exists(dir + '/../.hive/persistents.yml'):
            persistents = {}
        else:
            with open(dir + '/../.hive/persistents.yml') as file:
                persistents = yaml.load(file, Loader=yaml.FullLoader)
        if (
            not 'aws_access_key_id' in persistents or
            not 'aws_secret_access_key' in persistents or
            not base_answers['stage'] in persistents['aws_access_key_id'] or
            not base_answers['stage'] in persistents['aws_secret_access_key']
        ):
            aws_credential_questions = [
                inquirer.Text('aws_access_key_id',
                              message="What's your AWS access key id?",
                              validate=require_validation,
                              ),
                inquirer.Text('aws_secret_access_key',
                              message="What's your AWS secret access key?",
                              validate=require_validation,
                              ),
            ]
            aws_credential_answers = inquirer.prompt(aws_credential_questions, raise_keyboard_interrupt=True) or {}
            if not 'aws_access_key_id' in persistents:
                persistents['aws_access_key_id'] = {}
            if not 'aws_secret_access_key' in persistents:
                persistents['aws_secret_access_key'] = {}
            persistents['aws_access_key_id'][base_answers['stage']] = aws_credential_answers['aws_access_key_id']
            persistents['aws_secret_access_key'][base_answers['stage']] = aws_credential_answers['aws_secret_access_key']
            with open(dir + '/../.hive/persistents.yml', 'w') as file:
                yaml.dump(persistents, file, sort_keys=False)
        else:
            aws_credential_answers['aws_access_key_id'] = persistents['aws_access_key_id'][base_answers['stage']]
            aws_credential_answers['aws_secret_access_key'] = persistents['aws_secret_access_key'][base_answers['stage']]
        ec2_client = boto3.client(
            'ec2',
            region_name='ap-northeast-1',
            aws_access_key_id=aws_credential_answers['aws_access_key_id'],
            aws_secret_access_key=aws_credential_answers['aws_secret_access_key']
        )
        regions = ec2_client.describe_regions()
        regions = [region['RegionName'] for region in regions['Regions']]
        regions.sort()
        aws_region_questions = [
            inquirer.List('region',
                          message="What region do you want to use?",
                          choices=regions,
                          default='ap-northeast-1' if 'ap-northeast-1' in regions else regions[0]
                          )
        ]
        aws_region_answers = inquirer.prompt(aws_region_questions, raise_keyboard_interrupt=True) or {}
        ec2_client = boto3.client(
            'ec2',
            region_name=aws_region_answers['region'],
            aws_access_key_id=aws_credential_answers['aws_access_key_id'],
            aws_secret_access_key=aws_credential_answers['aws_secret_access_key']
        )
        print('Getting instance types...')

        def ec2_instance_types(client):
            describe_args = {}
            while True:
                describe_result = client.describe_instance_types(**describe_args)
                yield from [i['InstanceType'] for i in describe_result['InstanceTypes']]
                if 'NextToken' not in describe_result:
                    break
                describe_args['NextToken'] = describe_result['NextToken']
        machine_types = ec2_instance_types(ec2_client)
        machine_types_list = [machine_type for machine_type in machine_types]
        machine_types_list.sort()
        aws_machine_type_questions = [
            inquirer.List('instance_type',
                          message="What machine type do you want to use?",
                          choices=machine_types_list,
                          default='t2.medium' if 't2.medium' in machine_types_list else machine_types_list[0]
                          )
        ]
        aws_machine_type_answers = inquirer.prompt(aws_machine_type_questions, raise_keyboard_interrupt=True) or {}
        aws_machine_type_answers['repository_instance_type'] = aws_machine_type_answers['instance_type']
        subnet_answers["subnets"] = []
        for i in range(1, number_of_hosts_answers['number_of_hosts'] + 1):
            subnet_questions = [
                inquirer.Text('name',
                              message="What's the name for subnet" + str(i) + '?',
                              default='subnet-' + chr(96 + i)
                              ),
                inquirer.Text('cidr',
                              message="What's the CIDR for subnet" + str(i) + '?',
                              default='192.168.0.' + str((i-1) * 64) + '/26'
                              ),
                inquirer.Text('available_zone',
                              message="What's the available zone for subnet" + str(i) + '?',
                              default=aws_region_answers['region'] + chr(97 + i)
                              )
            ]
            subnet_answers_item = inquirer.prompt(subnet_questions, raise_keyboard_interrupt=True) or {}
            subnet_answers["subnets"].append(subnet_answers_item)

    disk_size_answers = {}
    if provider_answers['provider'] != 'prepared':
        disk_size_questions = [
            inquirer.Text('disk_size',
                          message="How much disk size do you want to use for hives?(GB)",
                          default='20'
                          ),
            inquirer.Text('repository_disk_size',
                          message="How much disk size do you want to use for repository?(GB)",
                          default='40'
                          ),
        ]
        disk_size_answers = inquirer.prompt(disk_size_questions, raise_keyboard_interrupt=True) or {}
        disk_size_answers['disk_size'] = int(disk_size_answers['disk_size'])
        disk_size_answers['repository_disk_size'] = int(disk_size_answers['repository_disk_size'])
    mirrored_disk_size_questions = [
        inquirer.Text('mirrored_disk_size',
                      message="How much disk size do you want to use for drbd disk?(GB)",
                      default='20'
                      ),
    ]
    mirrored_disk_size_answers = inquirer.prompt(mirrored_disk_size_questions, raise_keyboard_interrupt=True, ) or {}
    mirrored_disk_size_answers['mirrored_disk_size'] = int(mirrored_disk_size_answers['mirrored_disk_size'])

    stage_answers = {
        **provider_answers,
        **stage_base_answers,
        **number_of_hosts_answers,
        **vagrant_answers,
        **gcp_region_answers,
        **gcp_machine_type_answers,
        **aws_region_answers,
        **aws_machine_type_answers,
        **subnet_answers,
        **disk_size_answers,
        **mirrored_disk_size_answers
    }
except KeyboardInterrupt:
    print('Setup is canceled')
    exit()
print('--- Ask questions is done ---')

subprocess.run(['hive', 'set', 'stage', base_answers['stage']])

# install dependencies
print('--- Install dependencies ---')
if stage_answers['provider'] == 'vagrant':
    try:
        subprocess.run(['vagrant', '--version'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print('Vagrant is not installed')
        print('Automatically start installation after 3 seconds.')
        time.sleep(3)
        subprocess.run([dir + '/scripts/install-vagrant.sh'], user=user)
        print('Vagrant is successfully installed')
    try:
        subprocess.run(['squid', '--version'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print('squid is not installed')
        print('Automatically start installation after 3 seconds.')
        time.sleep(3)
        subprocess.run([dir + '/scripts/install-squid.sh'])
        print('squid is successfully installed')
    subprocess.run(['hive', 'set', 'vagrant_proxy', 'http://192.168.121.1:3128'])
print('--- Install dependencies is done ---')

# Update hive.yml
hive_yml = None
print('--- Update hive.yml ---')
with open(dir + '/../inventory/hive.yml') as file:
    hive_yml = yaml.load(file, Loader=yaml.FullLoader)

if hive_yml['name'] != base_answers['name']:
    print('hive name is changed:' + hive_yml['name'] + ' -> ' + base_answers['name'])
    hive_yml['name'] = base_answers['name']
if not hive_yml['stages']:
    print('stages is added')
    hive_yml['stages'] = {}
if not hive_yml['stages'][base_answers['stage']]:
    print('stage is added:' + base_answers['stage'])
    hive_yml['stages'][base_answers['stage']] = {}

for key in stage_answers:
    if key not in hive_yml['stages'][base_answers['stage']]:
        print(key + ' is added:' + str(stage_answers[key]))
        hive_yml['stages'][base_answers['stage']][key] = stage_answers[key]
    elif hive_yml['stages'][base_answers['stage']][key] != stage_answers[key]:
        print(key + ' is changed:' + str(hive_yml['stages'][base_answers['stage']][key]) + ' -> ' + str(stage_answers[key]))
        hive_yml['stages'][base_answers['stage']][key] = stage_answers[key]

with open('inventory/hive.yml', 'w') as file:
    yaml.dump(hive_yml, file, sort_keys=False)
print('--- Update hive.yml is done ---')
