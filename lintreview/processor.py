import logging
import lintreview.tools as tools

from lintreview.diff import DiffCollection
from lintreview.review import Problems
from lintreview.review import Review

log = logging.getLogger(__name__)


class Processor(object):

    _client = None
    _number = None
    _head = None
    _target_path = None
    _changes = None
    _problems = None
    _review = None
    _config = None

    def __init__(self, client, number, head, target_path, config=None):
        self._client = client
        self._number = number
        self._head = head
        self._target_path = target_path
        self._problems = Problems(target_path)
        self._review = Review(client, number)

        if config is None:
            config = {}
        self._config = config

    def load_changes(self):
        log.info('Loading pull request patches from github.')
        files = self._client.pull_requests.list_files(self._number)
        pull_request_patches = files.all()
        self._changes = DiffCollection(pull_request_patches)
        self._problems.set_changes(self._changes)

    def run_tools(self, review_config):
        if self._changes is None:
            raise RuntimeError('No loaded changes, cannot run tools. '
                               'Try calling load_changes first.')
        files_to_check = self._changes.get_files(
            append_base=self._target_path,
            ignore_patterns=review_config.ignore_patterns())
        tools.run(
            review_config,
            self._problems,
            files_to_check,
            self._target_path)

    def publish(self):
        self._problems.limit_to_changes()
        self._review.publish(
            self._problems,
            self._head,
            self._config.get('SUMMARY_THRESHOLD'))
