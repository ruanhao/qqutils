from hprint import hprint
from .stringutils import *
from .sqliteutils import *
from .threadutils import *
from .inspectutils import *
from .commutils import *
from .osutils import *
from .logutils import *
from .netutils import *
from .funcutils import *
from .dateutils import *
from .dbgutils import *
from .dsutils import *
from .urlutils import *
from .cryptutils import *

CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

__all__ = [

    'CLICK_CONTEXT_SETTINGS',

    'hprint',

    # threadutils
    'create_thread_pool',
    'submit_daemon_thread',
    'submit_thread',
    'submit_thread_and_wait',
    'submit_thread_and_wait_with_timeout',
    'submit_thread_with_callback',
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
    'download',
    'upload_multipart',
    'check_http_response',
    'http_get',
    'http_post',
    'http_put',
    'http_delete',
    'http_patch',
    'http_session_get',
    'http_session_post',
    'http_session_put',
    'http_session_delete',
    'http_session_patch',
    'encode_session_base64',
    'decode_session_base64',
    'sockinfo',
    'run_proxy',
    'sendall',
    'recvall',
    'acceptall',
    'eventfd',
    'sock_connect',
    'is_readable',
    'is_port_in_use',

    # MAIL
    'send_mail',

    # dateutils
    'YmdHMS',
    'datetimestr',
    'pretty_duration',
    'utc_to_local',
    'timestamp_seconds',
    'timestamp_millis',

    # logutils
    'pfatal',
    'pdebug',
    'pinfo',
    'pwarning',
    'perror',
    'pstderr',
    'configure_logging',
    'install_print_with_flush',
    'LoggerAdapter',

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
    'add_suffix',
    'modify_extension',
    'from_path_str',
    'under_home',
    'backup',                   # backup a file

    # funcutils
    'cached',

    # dbutils
    'setup_icecream',
    'assert_that',
    'simple_timing',
    'debug_timing',

    # urlutils
    'get_param',

    # inspectutils
    'get_source',

    # sqliteutils
    'sqlite3_connect',
    'sqlite3_cursor',
    'sqlite3_execute',
    'sqlite3_query',
    'sqlite3_tables',
    'sqlite3_select_all',
    'sqlite3_dump',
    'sqlite3_get',
    'sqlite3_put',
    'sqlite3_jget',
    'sqlite3_jput',

    # cryptutils
    'aes_encrypt',
    'aes_decrypt',

    # stringutils
    'style',
    'green',
    'red',
    'yellow',
    'blue',
    'cyan',
    'magenta',
    'bold',
    'underline',

]
