from aws_cdk import (
    core
)

from prisma_defender_ssm_association.secret_rotation_stack import SecretRotationStack

import common.functions

class SecretStage(core.Stage):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common.functions.unpack_constants_dict(self, constants)

        secret_rotation_stack = SecretRotationStack(
            self,
            '{0}-{1}-SecretStack'.format(self.BUSINESS_UNIT, self.APP_NAME),
            env=self.ENVIRONMENT,
            constants=constants,
            props=props
        )

        # Pass outputs up to pipeline
        self.token_secret_arn = secret_rotation_stack.token_secret_arn
        self.token_secret_arn_full = secret_rotation_stack.token_secret_arn_full
        self.token_secret_name = secret_rotation_stack.token_secret_name
        self.token_secret_kms_key_arn = secret_rotation_stack.token_secret_kms_key_arn
        self.token_secret_kms_key_id = secret_rotation_stack.token_secret_kms_key_id