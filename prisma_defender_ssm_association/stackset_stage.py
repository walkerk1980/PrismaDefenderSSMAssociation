from aws_cdk import (
    core
)

from prisma_defender_ssm_association.stackset_stack import StackSetStack

import common.functions

class StackSetStage(core.Stage):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common.functions.unpack_constants_dict(self, constants)

        stackset_stack = StackSetStack(
            self,
            '{0}-{1}-StackSetStack'.format(self.BUSINESS_UNIT, self.APP_NAME),
            # env=self.ENVIRONMENT,
            constants=constants,
            props=props
        )   
