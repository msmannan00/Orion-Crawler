import gc
import warnings
from celery import Celery
import subprocess
import sys
import os
import signal
import socket

from crawler.constants.enums import network_type
from crawler.crawler_instance.proxies.shared_proxy_methods import shared_proxy_methods
from crawler.crawler_services.log_manager.log_controller import log
from crawler.crawler_services.redis_manager.redis_controller import redis_controller
from crawler.crawler_services.celery_manager.celery_enums import CELERY_CONNECTIONS, CELERY_COMMANDS
from crawler.crawler_instance.genbot_service.genbot_controller import genbot_instance
from crawler.crawler_services.shared.helper_method import helper_method

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

celery = Celery('crawler', broker=CELERY_CONNECTIONS.conn, backend=None)

# Configure Celery task routing
celery.conf.task_routes = {
    'celery_controller.start_crawler': {'queue': 'crawler_queue'}
}
socket.setdefaulttimeout(30)
celery.conf.worker_task_log_format = None
celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1
celery.conf.update(
  worker_log_color=True,
  worker_redirect_stdouts=True,
  worker_redirect_stdouts_level='DEBUG',
  worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
)

class celery_controller:
  __instance = None

  @staticmethod
  def get_instance():
    if celery_controller.__instance is None:
      celery_controller()
    return celery_controller.__instance

  def __init__(self):
    if celery_controller.__instance is not None:
      raise Exception("This class is a singleton!")
    else:
      celery_controller.__instance = self
    warnings.filterwarnings("ignore")
    self.__redis_controller = redis_controller()
    self.__clear_redis_database()

  def __clear_redis_database(self):
    try:
      self.__redis_controller.invoke_trigger('S_FLUSH_ALL')
    except Exception:
      pass

  @staticmethod
  def __stop_all_workers():
    try:
      output = subprocess.check_output(['pgrep', '-f', 'celery'])
      pids = output.decode().strip().split("\n")
      for pid in pids:
        os.kill(int(pid), signal.SIGTERM)
    except subprocess.CalledProcessError:
      pass
    except Exception:
      pass

  @staticmethod
  def __run_crawler(url, virtual_id):
    m_proxy, m_tor_id = shared_proxy_methods.get_proxy(url)
    if helper_method.get_network_type(url) == network_type.I2P and shared_proxy_methods.get_i2p_status() or helper_method.get_network_type(url) == network_type.ONION and shared_proxy_methods.get_onion_status() or helper_method.get_network_type(url) == network_type.CLEARNET and shared_proxy_methods.get_onion_status():
      start_crawler.delay(url, virtual_id, m_proxy, m_tor_id)

  def invoke_trigger(self, p_commands, p_data=None):
    if p_commands == CELERY_COMMANDS.S_START_CRAWLER:
      self.__run_crawler(p_data[0], p_data[1])

# Celery tasks
@celery.task(name='celery_controller.start_crawler', time_limit=3600, soft_time_limit=3540)
def start_crawler(url, virtual_id, m_proxy, m_tor_id):
  genbot_instance(url, virtual_id, m_proxy, m_tor_id)
  gc.collect()

if __name__ == "__main__":
  manager = celery_controller.get_instance()