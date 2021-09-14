import os.path
import json

from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_secretsmanager as secrets,
    pipelines,
    core
)

import boto3

from aws_cdk.aws_s3_assets import Asset

from prisma_defender_ssm_association.template_stage import TemplateStage
from prisma_defender_ssm_association.secret_stage import SecretStage
from prisma_defender_ssm_association.stackset_stage import StackSetStage

import common.functions
import common.list_accounts_in_ou

class DeploymentPipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common.functions.unpack_constants_dict(self, constants)

        dirname = os.path.dirname(__file__)
        
        cloud_assembly_artifact = codepipeline.Artifact('cloud_assembly_artifact')
        source_artifact = codepipeline.Artifact('source')

        codecommit_repo = codecommit.Repository.from_repository_arn(
            self,
            'source_repo',
            repository_arn=props['repository_arn']
        )

        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name='Source',
            branch='main',
            repository=codecommit_repo,
            output=source_artifact
        )

        synth_action = pipelines.SimpleSynthAction(
            install_commands=[
                'npm install -g aws-cdk',
                'pip install --upgrade -r requirements.txt'
            ],
            synth_command='cdk synth',
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_artifact=source_artifact,
            # role_policy_statements=[get_accounts_in_ous_statement]
        )

        deployment_pipeline = pipelines.CdkPipeline(
            self,
            'deployment_pipeline',
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_action=source_action,
            synth_action=synth_action
        )

        secret_stage = SecretStage(
            self,
            'secret-stage',
            constants,
            props,
        )
        secret_pipeline_stage = deployment_pipeline.add_application_stage(secret_stage)

        PRISMA_TOKEN_SECRET_ARN = secret_stage.token_secret_arn.value
        PRISMA_TOKEN_SECRET_ARN_FULL = secret_stage.token_secret_arn_full.value
        PRISMA_TOKEN_SECRET_NAME = secret_stage.token_secret_name.value
        PRISMA_TOKEN_KMS_KEY_ARN = secret_stage.token_secret_kms_key_arn.value
        PRISMA_TOKEN_KMS_KEY_ID = secret_stage.token_secret_kms_key_id.value
        constants.update({'PRISMA_TOKEN_SECRET_ARN': PRISMA_TOKEN_SECRET_ARN})
        constants.update({'PRISMA_TOKEN_SECRET_ARN_FULL': PRISMA_TOKEN_SECRET_ARN_FULL})
        constants.update({'PRISMA_TOKEN_SECRET_NAME': PRISMA_TOKEN_SECRET_NAME})
        constants.update({'PRISMA_TOKEN_KMS_KEY_ARN': PRISMA_TOKEN_KMS_KEY_ARN})
        constants.update({'PRISMA_TOKEN_KMS_KEY_ID': PRISMA_TOKEN_KMS_KEY_ID})

        template_stage = TemplateStage(
            self,
            'template-stage',
            constants,
            props,
            env={}
        )
        stackset_template = template_stage.synth(skip_validation=True).stacks[0].template
        try:
            del(stackset_template['Conditions']['CDKMetadataAvailable'])
        except Exception as e:
            print(e)
        try:
            del(stackset_template['Resources']['CDKMetadata'])
        except Exception as e:
            print(e)

        props.update({'stackset_template': json.dumps(stackset_template)})

        stackset_stage = StackSetStage(
            self,
            'stackset-stage',
            constants=constants,
            props=props
        )
        stackset_pipeline_stage = deployment_pipeline.add_application_stage(stackset_stage)
