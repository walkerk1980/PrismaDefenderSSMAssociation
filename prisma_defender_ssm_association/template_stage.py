from aws_cdk import (
    core
)

from prisma_defender_ssm_association.prisma_defender_ssm_association_stack import PrismaDefenderSsmAssociationStack

import common.functions

class TemplateStage(core.Stage):

    def __init__(self, scope: core.Construct, construct_id: str, constants: dict, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common.functions.unpack_constants_dict(self, constants)

        template_stack = PrismaDefenderSsmAssociationStack(
            self,
            '{0}-{1}-TemplateStack'.format(self.BUSINESS_UNIT, self.APP_NAME),
            # env=self.ENVIRONMENT,
            synthesizer=core.BootstraplessSynthesizer(),
            env={},
            constants=constants,
            props=props
        )   

        # self.recipe_url = prereqs_stack.recipe_url