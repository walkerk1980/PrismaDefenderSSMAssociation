import json
import pytest

from aws_cdk import core
from prisma_defender_ssm_association.prisma_defender_ssm_association_stack import PrismaDefenderSsmAssociationStack


def get_template():
    app = core.App()
    PrismaDefenderSsmAssociationStack(app, "prisma-defender-ssm-association")
    return json.dumps(app.synth().get_stack("prisma-defender-ssm-association").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())


def test_sns_topic_created():
    assert("AWS::SNS::Topic" in get_template())
