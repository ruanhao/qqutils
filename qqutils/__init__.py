from hprint import hprint
from .threadutils import *
from .commutils import *
from .osutils import *
from .logutils import *
from .netutils import *
from .funcutils import *
from .dateutils import *
from .dbgutils import *
from .dsutils import *
from .dsutils import *

CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

__all__ = [

    'CLICK_CONTEXT_SETTINGS',

    'hprint',

    # threadutils
    'submit_thread'
    'submit_thread_and_wait'
    'submit_thread_and_wait_with_timeout',
    'submit_thread_with_callback'
    'wait_forever',

    # dsutils
    'pget',
    'flatten',
    'kvdict',
    'kdict',
    'set_with_key',

    # EXCEPTION UTILS
    'sneaky',

    # netutils
    'check_http_response',
    'http_get',
    'http_post',
    'http_put',
    'http_delete',
    'socket_description',
    'run_proxy',

    # MAIL
    'send_mail',

    # dateutils
    'YmdHMS',
    'datetimestr',
    'pretty_duration',
    'utc_to_local',

    # LOGGING
    'pfatal',
    'pdebug',
    'pinfo',
    'pwarning',
    'perror',
    'configure_logging',
    'install_print_with_flush',

    # osutils
    'bye',
    'goodbye',
    'run_script',
    'as_root',
    'is_root',
    'switch_dir',
    'tmpdir',
    'from_cwd',
    'from_module',
    'write_to_clipboard',
    'prompt',
    'confirm',
    'pause',

    # funcutils
    'cached',

    # dbutils
    'setup_icecream',
    'assert_that',
    'simple_timing',
    'debug_timing',
]
