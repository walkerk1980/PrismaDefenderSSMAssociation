import os
import random

from aws_cdk import (
    aws_lambda as lambda_,
    aws_secretsmanager as secrets,
    aws_ssm as ssm,
    aws_cloudformation as cloudformation,
    core
)
from aws_cdk.aws_ecs import Capability

class StackSetStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id,  **kwargs)

        dirname = os.path.dirname(__file__)

        stackset_template = str(props['stackset_template'])
        # print(stackset_template)

        stackset = cloudformation.CfnStackSet(
            self,
            id='association_stackset',
            permission_model='SERVICE_MANAGED',
            auto_deployment=cloudformation.CfnStackSet.AutoDeploymentProperty(
                enabled=True,
                retain_stacks_on_account_removal=False
            ),
            operation_preferences=cloudformation.CfnStackSet.OperationPreferencesProperty(
                failure_tolerance_percentage=100,
                max_concurrent_percentage=100,
                region_order=constants['STACKSET_REGIONS']
            ),
            stack_set_name='{0}-{1}'.format(constants.get('BUSINESS_UNIT'), constants.get('APP_NAME')),
            template_body=stackset_template,
            capabilities=[
                # cloudformation.CloudFormationCapabilities.NAMED_IAM.value,
                # cloudformation.CloudFormationCapabilities.IAM.value,
                'CAPABILITY_NAMED_IAM',
                'CAPABILITY_IAM'
            ],
            call_as='DELEGATED_ADMIN',
            # parameters=stackset_parameters,
        )
        # Needed for old versions of CDK before call_as param was supported
        # stackset.add_property_override(
        #     property_path='CallAs',
        #     value='DELEGATED_ADMIN'
        # )
        stackset.stack_instances_group = [
            cloudformation.CfnStackSet.StackInstancesProperty(
                deployment_targets=cloudformation.CfnStackSet.DeploymentTargetsProperty(
                    organizational_unit_ids=constants['STACKSET_OUS']
                ),
                regions=constants['STACKSET_REGIONS']
            )
        ]



        