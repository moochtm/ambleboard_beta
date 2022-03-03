import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget

import logging

logger = logging.getLogger(__name__)


class Widget(BaseWidget):
    widget_name = "COUNTER"
    worker_is_needed = False
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}
