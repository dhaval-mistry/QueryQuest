"""Prepare, execute and inspect the specific QueryQuest CloudFormation stack.

Run with the AWS project's Python environment. No credentials are persisted here.
"""
import argparse
import json
from pathlib import Path
import secrets
import subprocess

import boto3
from botocore.exceptions import ClientError
from aws_stack import template

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.tmp' / 'queryquest-deployment.json'
STACK = 'queryquest-public'
ACCOUNT = '456823161025'
REGION = 'us-east-2'


def session():
    value = boto3.Session(profile_name='queryquest', region_name=REGION)
    actual = value.client('sts').get_caller_identity()['Account']
    if actual != ACCOUNT:
        raise RuntimeError(f'Expected project account {ACCOUNT}; current account is {actual}')
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['plan', 'create-change-set', 'execute', 'status'])
    args = parser.parse_args()
    aws = session()
    cf = aws.client('cloudformation')
    if args.action in ('plan', 'create-change-set'):
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        ec2 = aws.client('ec2')
        vpc = ec2.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['true']}])['Vpcs'][0]['VpcId']
        subnet = next(item['SubnetId'] for item in ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc]}])['Subnets'] if item['MapPublicIpOnLaunch'])
        image = aws.client('ssm').get_parameter(Name='/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64')['Parameter']['Value']
        prefix = ec2.describe_managed_prefix_lists(Filters=[{'Name': 'prefix-list-name', 'Values': ['com.amazonaws.global.cloudfront.origin-facing']}])['PrefixLists'][0]['PrefixListId']
        body = json.dumps(template())
        cf.validate_template(TemplateBody=body)
        print(json.dumps({'account': ACCOUNT, 'region': REGION, 'revision': revision,
                          'vpc': vpc, 'subnet': subnet, 'image': image,
                          'resources': {key: item['Type'] for key, item in template()['Resources'].items()},
                          'estimated_hosting_usd_per_month': 21}, indent=2))
        if args.action == 'plan':
            return
        try:
            existing = cf.describe_stacks(StackName=STACK)['Stacks'][0]
        except ClientError as error:
            if error.response['Error']['Code'] != 'ValidationError' or 'does not exist' not in error.response['Error']['Message']:
                raise
        else:
            if existing['StackStatus'] != 'REVIEW_IN_PROGRESS':
                raise RuntimeError('A deployment stack already exists. Inspect it before creating or updating resources.')
        parameters = {'VpcId': vpc, 'SubnetId': subnet, 'ImageId': image,
                      'CloudFrontPrefixList': prefix, 'SourceCommit': revision,
                      'OriginSecret': secrets.token_urlsafe(32), 'UsageSecret': secrets.token_urlsafe(32)}
        result = cf.create_change_set(
            StackName=STACK, ChangeSetName='deploy-' + revision[:12], ChangeSetType='CREATE',
            TemplateBody=body, Capabilities=['CAPABILITY_IAM'],
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in parameters.items()],
            Tags=[{'Key': 'Project', 'Value': 'QueryQuest'}],
            Description='One public QueryQuest server with HTTPS and persistent research limits',
        )
        STATE.parent.mkdir(exist_ok=True)
        STATE.write_text(json.dumps({'stack': STACK, 'change_set_id': result['Id'], 'source_commit': revision,
                                     'account': ACCOUNT, 'region': REGION}, indent=2), encoding='utf-8')
        print('Prepared change set:', result['Id'])
        return
    if args.action == 'execute':
        state = json.loads(STATE.read_text(encoding='utf-8'))
        change = cf.describe_change_set(ChangeSetName=state['change_set_id'])
        if change['Status'] != 'CREATE_COMPLETE' or change['ExecutionStatus'] != 'AVAILABLE':
            raise RuntimeError('Change set is not ready: ' + change['Status'] + ' / ' + change['ExecutionStatus'])
        print('Executing additions:', [(item['ResourceChange']['LogicalResourceId'], item['ResourceChange']['ResourceType']) for item in change['Changes']])
        cf.execute_change_set(ChangeSetName=state['change_set_id'])
        print('Deployment started:', STACK)
        return
    stack = cf.describe_stacks(StackName=STACK)['Stacks'][0]
    print('Stack:', stack['StackStatus'])
    for item in stack.get('Outputs', []):
        print(item['OutputKey'] + ':', item['OutputValue'])
    if stack['StackStatus'] == 'REVIEW_IN_PROGRESS' and STATE.exists():
        change = cf.describe_change_set(ChangeSetName=json.loads(STATE.read_text())['change_set_id'])
        print('Change set:', change['Status'], change.get('StatusReason', ''))
        for item in change.get('Changes', []):
            entry = item['ResourceChange']
            print(entry['Action'], entry['LogicalResourceId'], entry['ResourceType'])
    else:
        events = cf.describe_stack_events(StackName=STACK)['StackEvents'][:12]
        for item in reversed(events):
            print(item['LogicalResourceId'], item['ResourceStatus'], item.get('ResourceStatusReason', ''))


if __name__ == '__main__':
    main()
