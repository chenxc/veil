######## export begin
from .website import start_website
from .website import create_website_http_handler
from .routing import route
from .routing import async_route
from .routing import public_route
from .routing import is_public_route

__all__ = [
    # from website
    start_website.__name__,
    create_website_http_handler.__name__,
    # from routing
    route.__name__,
    async_route.__name__,
    public_route.__name__,
    is_public_route.__name__
]
######## export end

def init():
    from sandal.component import init_component
    from static_file import process_script_tags
    from static_file import process_inline_blocks
    from sandal.template import register_page_post_processor
    from sandal.template import register_template_post_processor

    register_template_post_processor(process_inline_blocks)
    register_page_post_processor(process_script_tags)
    init_component(__name__)

init()