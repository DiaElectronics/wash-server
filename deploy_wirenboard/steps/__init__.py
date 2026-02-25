from steps.common import state
from steps import (
    step1_welcome,
    step2_select_device,
    step3_check_prerequisites,
    step4_format_ssd,
    step5_install_docker,
    step6_deploy_compose,
)

STEPS = [
    (step1_welcome.LABEL, step1_welcome.run),
    (step2_select_device.LABEL, step2_select_device.run),
    (step3_check_prerequisites.LABEL, step3_check_prerequisites.run),
    (step4_format_ssd.LABEL, step4_format_ssd.run),
    (step5_install_docker.LABEL, step5_install_docker.run),
    (step6_deploy_compose.LABEL, step6_deploy_compose.run),
]
