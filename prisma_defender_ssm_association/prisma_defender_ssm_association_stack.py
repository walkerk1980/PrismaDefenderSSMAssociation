import os
import random
import yaml

from aws_cdk import (
    aws_lambda as lambda_,
    aws_secretsmanager as secrets,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_cloudformation as cloudformation,
    core
)

class PrismaDefenderSsmAssociationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id,  **kwargs)

        dirname = os.path.dirname(__file__)

        us_east_1_condition = core.CfnCondition(
            self,
            'USEast1RegionCondition',
            expression=core.Fn.condition_equals(
                core.Stack.of(self).region,
                'us-east-1'
            )
        )

        content_dir = 'content'

        command_doc_content = ''
        command_doc_content_fn = 'command_document.yaml'
        command_doc_content_path = os.path.join(dirname, content_dir, command_doc_content_fn)
        with open(command_doc_content_path, 'r') as file_descriptor:
            command_doc_content = file_descriptor.read()

        deployment_version = random.randint(0,9999)
        ssm_command = ssm.CfnDocument(
            self,
            'install-prisma-ssm-command',
            document_type='Command',
            name='{0}-Prisma-ManageDefender-{1}'.format(constants['BUSINESS_UNIT'], deployment_version),
            content=yaml.safe_load(command_doc_content)
        )

        automation_doc_content = ''
        automation_doc_content_fn = 'automation_document.yaml'
        automation_doc_content_path = os.path.join(dirname, content_dir, automation_doc_content_fn)
        with open(automation_doc_content_path, 'r') as file_descriptor:
            automation_doc_content = file_descriptor.read()
        automation_doc_content = automation_doc_content.replace('prisma_secret_name_placeholder', '{0}_token'.format(constants['PRISMA_SECRET_NAME']))
        automation_doc_content = automation_doc_content.replace('prisma_secret_account_placeholder', constants['DEPLOYMENT_ACCOUNT'])
        automation_doc_content = automation_doc_content.replace('ssm_command_placeholder', ssm_command.name)

        automation_execution_role = iam.Role(
            self,
            'automation-execution-role',
            assumed_by=iam.ServicePrincipal('ssm.amazonaws.com'),
            # Can't provide name unless using region condition
            # role_name='nni-PrismaDefenderSSMExecutionRole',
            description='Role to install Prisma Defender on EC2 Instances',
            inline_policies=[
                iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[
                                # constants['PRISMA_TOKEN_SECRET_ARN'],
                                # constants['PRISMA_TOKEN_SECRET_ARN_FULL'],
                                'arn:aws:secretsmanager:*:{0}:secret:{1}'.format(
                                    constants['DEPLOYMENT_ACCOUNT'],
                                    '{0}'.format(constants['PRISMA_TOKEN_SECRET_NAME'])
                                ),
                                'arn:aws:secretsmanager:*:{0}:secret:{1}'.format(
                                    constants['DEPLOYMENT_ACCOUNT'],
                                    '{0}-??????'.format(constants['PRISMA_TOKEN_SECRET_NAME'])
                                )
                            ],
                            actions=['secretsmanager:GetSecretValue'],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[
                                'arn:aws:ssm:*:*:document/{0}'.format(ssm_command.ref),
                                'arn:aws:ec2:*:*:instance/*'
                            ],
                            actions=['ssm:SendCommand'],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=['arn:aws:ssm:*:*:*'],
                            actions=[
                                'ssm:ListCommands',
                                'ssm:ListCommandInvocations',
                                'ssm:DescribeInstanceInformation'
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[
                                'arn:aws:kms:*:{0}:key/*'.format(
                                    constants['DEPLOYMENT_ACCOUNT']
                                )
                            ],
                            actions=[
                                'kms:Decrypt',
                                'kms:DescribeKey'
                            ]
                        )
                    ]
                )
            ]
        )
        # iam.Role does not have cfn_options, only iam.CfnRole does
        # This means condition can't currently be used with level 2 Role construct
        # automation_execution_role.cfn_options.condition = us_east_1_condition

        ssm_automation = ssm.CfnDocument(
            self,
            'get-token-run-command-automation',
            document_type='Automation',
            name='{0}-Prisma-DefenderAutomation-{1}'.format(constants['BUSINESS_UNIT'], deployment_version),
            content=yaml.safe_load(automation_doc_content)
        )

        ssm_association = ssm.CfnAssociation(
            self,
            'prisma-defender-association',
            max_concurrency='100',
            max_errors='100',
            association_name='{0}-SystemAssociationForPrismaDefender'.format(constants['BUSINESS_UNIT']),
            automation_target_parameter_name='InstanceIds',
            name=ssm_automation.name,
            document_version='$DEFAULT',
            schedule_expression='rate(1 hour)',
            compliance_severity='UNSPECIFIED',
            targets=[
                {
                    'key': 'InstanceIds',
                    'values': ['*']
                }
            ]
        )
        ssm_association.add_property_override(
            'Parameters.AutomationAssumeRole',
            value=[automation_execution_role.role_arn]
        )
        ssm_association.add_property_override(
            'Parameters.Operation',
            value=['Install']
        )
        ssm_association.add_depends_on(ssm_automation)

