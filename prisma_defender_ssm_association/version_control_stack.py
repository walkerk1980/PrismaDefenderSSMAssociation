import os.path
import json
from sys import platform

from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    aws_codecommit as codecommit,
    core
)

from aws_cdk.aws_s3_assets import Asset

import common.functions

class VersionControlStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common.functions.unpack_constants_dict(self, constants)

        dirname = os.path.dirname(__file__)

        codecommit_repo = codecommit.Repository.from_repository_name(
            self,
            'codecommit_repo',
            repository_name='{0}-{1}'.format(self.BUSINESS_UNIT, self.APP_NAME)
        )

        # Prepares output attributes to be passed into other stacks
        self.output_props = props.copy()
        self.output_props['repository_clone_url_http'] = codecommit_repo.repository_clone_url_http
        self.output_props['repository_arn'] = codecommit_repo.repository_arn

        @property
        def outputs(self):
            return self.output_props