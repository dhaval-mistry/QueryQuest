"""CloudFormation definition for one public QueryQuest AWS deployment."""
import json
from pathlib import Path


def ref(name):
    return {"Ref": name}


def sub(text):
    return {"Fn::Sub": text}


def template():
    resources = {}
    resources["AppRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {"Version": "2012-10-17", "Statement": [{
                "Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole",
            }]},
            "ManagedPolicyArns": [sub("arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore")],
            "Policies": [{"PolicyName": "QueryQuestResearch", "PolicyDocument": {
                "Version": "2012-10-17", "Statement": [
                    {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": [
                        sub("arn:${AWS::Partition}:bedrock:${AWS::Region}:${AWS::AccountId}:inference-profile/us.anthropic.claude-sonnet-4-6"),
                        sub("arn:${AWS::Partition}:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-6"),
                        sub("arn:${AWS::Partition}:bedrock:us-east-2::foundation-model/anthropic.claude-sonnet-4-6"),
                        sub("arn:${AWS::Partition}:bedrock:us-west-2::foundation-model/anthropic.claude-sonnet-4-6"),
                    ]},
                    {"Effect": "Allow", "Action": "bedrock-agentcore:InvokeWebSearch",
                     "Resource": sub("arn:${AWS::Partition}:bedrock-agentcore:${AWS::Region}:aws:tool/web-search.v1")},
                    {"Effect": "Allow", "Action": "cloudformation:SignalResource",
                     "Resource": sub("arn:${AWS::Partition}:cloudformation:${AWS::Region}:${AWS::AccountId}:stack/${AWS::StackName}/*")},
                ],
            }}],
            "Tags": [{"Key": "Project", "Value": "QueryQuest"}],
        },
    }
    resources["AppProfile"] = {"Type": "AWS::IAM::InstanceProfile", "Properties": {"Roles": [ref("AppRole")]}}
    resources["OriginSecurityGroup"] = {"Type": "AWS::EC2::SecurityGroup", "Properties": {
        "GroupDescription": "QueryQuest: CloudFront origin traffic only; administration through SSM",
        "VpcId": ref("VpcId"),
        "SecurityGroupIngress": [{"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                                  "SourcePrefixListId": ref("CloudFrontPrefixList")}],
        "Tags": [{"Key": "Project", "Value": "QueryQuest"}],
    }}
    resources["PublicIp"] = {"Type": "AWS::EC2::EIP", "Properties": {
        "Domain": "vpc", "Tags": [{"Key": "Project", "Value": "QueryQuest"}],
    }}
    userdata = (Path(__file__).parent / "server-bootstrap.sh").read_text(encoding="utf-8")
    resources["Server"] = {"Type": "AWS::EC2::Instance", "CreationPolicy": {"ResourceSignal": {"Timeout": "PT20M"}}, "Properties": {
        "ImageId": ref("ImageId"), "InstanceType": "t3.small",
        "CreditSpecification": {"CPUCredits": "standard"},
        "IamInstanceProfile": ref("AppProfile"), "SubnetId": ref("SubnetId"),
        "SecurityGroupIds": [ref("OriginSecurityGroup")],
        "MetadataOptions": {"HttpTokens": "required", "HttpEndpoint": "enabled", "HttpPutResponseHopLimit": 2},
        "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {
            "VolumeSize": 25, "VolumeType": "gp3", "Encrypted": True, "DeleteOnTermination": True,
        }}],
        "Tags": [{"Key": "Name", "Value": "QueryQuest"}, {"Key": "Project", "Value": "QueryQuest"}],
        "UserData": {"Fn::Base64": sub(userdata)},
    }}
    resources["IpAssociation"] = {"Type": "AWS::EC2::EIPAssociation", "Properties": {
        "AllocationId": {"Fn::GetAtt": ["PublicIp", "AllocationId"]}, "InstanceId": ref("Server"),
    }}
    origin_dns = {"Fn::Join": ["", ["ec2-", {"Fn::Join": ["-", {"Fn::Split": [".", ref("PublicIp")]}]}, ".", ref("AWS::Region"), ".compute.amazonaws.com"]]}
    resources["Website"] = {"Type": "AWS::CloudFront::Distribution", "DependsOn": "IpAssociation", "Properties": {
        "DistributionConfig": {
            "Enabled": True, "Comment": "QueryQuest public research application",
            "PriceClass": "PriceClass_100", "HttpVersion": "http2", "IPV6Enabled": True,
            "Origins": [{"Id": "QueryQuestServer", "DomainName": origin_dns,
                "OriginCustomHeaders": [{"HeaderName": "X-QueryQuest-Origin", "HeaderValue": ref("OriginSecret")}],
                "CustomOriginConfig": {"HTTPPort": 80, "HTTPSPort": 443, "OriginProtocolPolicy": "http-only", "OriginReadTimeout": 60, "OriginKeepaliveTimeout": 5},
            }],
            "DefaultCacheBehavior": {
                "TargetOriginId": "QueryQuestServer", "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"],
                "CachedMethods": ["GET", "HEAD"], "Compress": True,
                "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
                "OriginRequestPolicyId": "216adef6-5c7f-47e4-b989-5492eafa07d3",
            },
            "ViewerCertificate": {"CloudFrontDefaultCertificate": True},
            "CustomErrorResponses": [{"ErrorCode": code, "ErrorCachingMinTTL": 0} for code in (400, 403, 404, 500, 502, 503, 504)],
        }, "Tags": [{"Key": "Project", "Value": "QueryQuest"}],
    }}
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "QueryQuest: one EC2 server, instance role, restricted origin and CloudFront HTTPS",
        "Parameters": {
            "VpcId": {"Type": "AWS::EC2::VPC::Id"}, "SubnetId": {"Type": "AWS::EC2::Subnet::Id"},
            "ImageId": {"Type": "AWS::EC2::Image::Id"}, "CloudFrontPrefixList": {"Type": "String"},
            "SourceCommit": {"Type": "String", "AllowedPattern": "[a-f0-9]{40}"},
            "OriginSecret": {"Type": "String", "NoEcho": True, "AllowedPattern": "[A-Za-z0-9_-]{32,}"},
            "UsageSecret": {"Type": "String", "NoEcho": True, "AllowedPattern": "[A-Za-z0-9_-]{32,}"},
        },
        "Resources": resources,
        "Outputs": {
            "WebsiteUrl": {"Value": {"Fn::Join": ["", ["https://", {"Fn::GetAtt": ["Website", "DomainName"]}]]}},
            "InstanceId": {"Value": ref("Server")},
            "DistributionId": {"Value": ref("Website")},
            "AppRoleArn": {"Value": {"Fn::GetAtt": ["AppRole", "Arn"]}},
        },
    }


if __name__ == "__main__":
    print(json.dumps(template(), indent=2))
