import os
import random

from aws_cdk import (
    aws_lambda as lambda_,
    aws_kms as kms,
    aws_secretsmanager as secrets,
    aws_events_targets as event_targets,
    aws_events as events,
    aws_iam as iam,
    core
)

class SecretRotationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id,  **kwargs)

        dirname = os.path.dirname(__file__)

        lambda_code_folder = 'prisma_defender_ssm_association/lambda/get_prisma_token'
        lambda_code_file = 'index.py'
        with open(os.path.join(lambda_code_folder, lambda_code_file), 'r') as file_descriptor:
            get_prisma_token_code_text = file_descriptor.read()

        get_prisma_token_code_asset = lambda_.Code.from_inline(get_prisma_token_code_text)

        prisma_access_key_secret = secrets.Secret.from_secret_name_v2(
            self,
            'prisma_access_key_secret',
            constants['PRISMA_SECRET_NAME']
        )

        prisma_token_secret_kms_key = kms.Key(
            self,
            'prisma-token-secret-kms-key',
            alias='prisma_secret_token_key',
            enable_key_rotation=True
        )
        prisma_token_secret = secrets.Secret(
            self,
            'prisma-token-secret',
            description='secret that holds prisma tokens to be shared with org',
            # replica_regions=constants['STACKSET_REGIONS'],
            secret_name='{0}_token'.format(constants['PRISMA_SECRET_NAME']),
            encryption_key=prisma_token_secret_kms_key
        )

        zip_relative_path = 'lambda/dependency_layer.zip'
        dependency_layer_zip_path = os.path.join(dirname, zip_relative_path)
        dependency_lambda_layer = lambda_.LayerVersion(
            self,
            'dependency-lambda-layer',
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_8],
            code=lambda_.Code.from_asset(dependency_layer_zip_path)
        )

        get_prisma_token_lambda = lambda_.Function(
            self,
            'get-prisma-token-lambda',
            handler='index.handler',
            code=get_prisma_token_code_asset,
            runtime=lambda_.Runtime.PYTHON_3_8,
            layers=[dependency_lambda_layer]
        )
        prisma_access_key_secret.grant_read(get_prisma_token_lambda)
        # prisma_access_key_secret.encryption_key.grant_decrypt(get_prisma_token_lambda)
        prisma_token_secret.grant_write(get_prisma_token_lambda)
        prisma_token_secret.encryption_key.grant_encrypt(get_prisma_token_lambda)
        get_prisma_token_lambda.add_environment(key='credential_secret', value=prisma_access_key_secret.secret_arn)

        lambda_event_target = event_targets.LambdaFunction(get_prisma_token_lambda)

        lambda_periodic_event_rule = events.Rule(
            self,
            'lambda-periodic-event-rule',
            description='keep an unexpired Prisma Token available',
            enabled=True,
            schedule=events.Schedule.rate(core.Duration.minutes(30)),
            targets=[lambda_event_target]
        )
        prisma_token_secret.grant_read(
            # version_stages=[
            #     'AWSCURRENT',
            #     'TOKEN'
            # ],
            grantee=iam.OrganizationPrincipal(constants['AWS_ORG_ID'])
        )
        prisma_token_secret.encryption_key.grant_decrypt(
            iam.OrganizationPrincipal(constants['AWS_ORG_ID']),
        )

        self.token_secret_arn = core.CfnOutput(
            self,
            'prisma-token-secret-arn',
            value=prisma_token_secret.secret_arn
        )
        self.token_secret_name = core.CfnOutput(
            self,
            'prisma-token-secret-name',
            value=prisma_token_secret.secret_name
        )
        self.token_secret_arn_full = core.CfnOutput(
            self,
            'prisma-token-secret-arn-full',
            value=prisma_token_secret.secret_full_arn
        )
        self.token_secret_kms_key_arn = core.CfnOutput(
            self,
            'prisma-token-secret-kms-key-arn',
            value=prisma_token_secret_kms_key.key_arn
        )
        self.token_secret_kms_key_id = core.CfnOutput(
            self,
            'prisma-token-secret-kms-key-id',
            value=prisma_token_secret_kms_key.key_id
        )