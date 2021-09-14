#!/usr/bin/env python3

from aws_cdk import core

from prisma_defender_ssm_association.version_control_stack import VersionControlStack
from prisma_defender_ssm_association.deployment_pipeline_stack import DeploymentPipelineStack

# Constants
APP_NAME = 'PrismaDefenderSSMAssociation'
BUSINESS_UNIT = 'SEC'
DEPLOYMENT_ACCOUNT = '123456789012'
DEPLOYMENT_REGION = 'us-west-2'
AWS_ORG_ID = 'o-oyourorgid'
# Sandbox and Deployment Account OUs
SANDBOX_OUS = ['ou-sand-example', 'ou-depl-example']
# Production and Deployment Account OUs
PRODUCTION_OUS = ['ou-prod-example', 'ou-depl-example']
STACKSET_OUS = SANDBOX_OUS
STACKSET_REGIONS = ['us-east-1', 'us-west-2', 'us-west-1', 'us-east-2']
# Secret Name for API Key Secret that was manually created in DEPLOYMENT_REGION
PRISMA_SECRET_NAME = 'prod/service_account/prisma_defender'

constants = {}
constants.update({'APP_NAME': APP_NAME})
constants.update({'BUSINESS_UNIT': BUSINESS_UNIT})
constants.update({'DEPLOYMENT_ACCOUNT': DEPLOYMENT_ACCOUNT})
constants.update({'AWS_ORG_ID': AWS_ORG_ID})
constants.update({'STACKSET_OUS': STACKSET_OUS})
constants.update({'STACKSET_REGIONS': STACKSET_REGIONS})
constants.update({'PRISMA_SECRET_NAME': PRISMA_SECRET_NAME})

ENVIRONMENT = {'account': DEPLOYMENT_ACCOUNT,'region': DEPLOYMENT_REGION}
ENVIRONMENT = {'region': DEPLOYMENT_REGION}

constants.update({'ENVIRONMENT': ENVIRONMENT})

app = core.App()

props = {}

version_control_stack = VersionControlStack(
    app,
    '{0}-{1}-version-control'.format(BUSINESS_UNIT, APP_NAME),
    env=ENVIRONMENT,
    constants=constants,
    props=props
)
props = version_control_stack.output_props

deployment_pipeline_stack = DeploymentPipelineStack(
    app,
    '{0}-{1}-deployment-pipeline'.format(BUSINESS_UNIT, APP_NAME),
    env=ENVIRONMENT,
    constants=constants,
    props=props
)
deployment_pipeline_stack.add_dependency(version_control_stack)

app.synth()
