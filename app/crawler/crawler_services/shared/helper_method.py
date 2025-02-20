# Local Imports
import os
import re
import zipfile
import socket
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import STOPWORDS
from crawler.constants.strings import MANAGE_MESSAGES
from crawler.crawler_services.log_manager.log_controller import log


class helper_method:

  @staticmethod
  def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

  @staticmethod
  def is_stop_word(p_word):
    if p_word in STOPWORDS:
      return True
    else:
      return False

  @staticmethod
  def strip_special_character(p_text):
    m_text = re.sub(r"^\W+", "", p_text)
    return m_text

  @staticmethod
  def on_clean_url(p_url):
    parsed_url = urlparse(p_url)
    netloc = parsed_url.netloc.replace("www.", "", 1)
    cleaned_url = urlunparse((
      parsed_url.scheme,
      netloc.lower(),
      parsed_url.path.rstrip('/ '),
      parsed_url.params,
      parsed_url.query,
      parsed_url.fragment
    ))
    return cleaned_url

  @staticmethod
  def get_network_type(url: str):
    try:
      if not url.startswith("http"):
        url = "http://" + url
      parsed_url = urlparse(url)
      if not parsed_url.scheme or not parsed_url.netloc:
        return "invalid"
      if re.search(r"\.onion$", parsed_url.netloc, re.IGNORECASE):
        return "onion"
      if re.search(r"\.i2p$", parsed_url.netloc, re.IGNORECASE):
        return "i2p"
      return "clearnet"
    except Exception:
      return "invalid"

  @staticmethod
  def extract_emails(text: str) -> list:

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails

  @staticmethod
  def extract_phone_numbers(text: str) -> list:
    phone_pattern = r'\(?\b\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'
    phone_numbers = re.findall(phone_pattern, text)

    filtered_phone_numbers = []
    for number in phone_numbers:
      digits_only = re.sub(r'[^0-9]', '', number)

      if 7 <= len(digits_only) <= 15:
        if '(' in text[text.find(number):text.find(number) + len(number)]:
          filtered_phone_numbers.append(number)
        else:
          filtered_phone_numbers.append(number)

    return filtered_phone_numbers

  @staticmethod
  def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=' ')
    return helper_method.clean_text(text)

  @staticmethod
  def clear_hosts_file(file_path):
    try:
      os.makedirs(os.path.dirname(file_path), exist_ok=True)

      with open(file_path, 'w'):
        pass

    except Exception:
      pass

  @staticmethod
  def get_host_name(p_url):
    m_parsed_uri = urlparse(p_url)
    m_netloc = m_parsed_uri.netloc

    if m_netloc.startswith('www.'):
      m_netloc = m_netloc[4:]

    netloc_parts = m_netloc.split('.')

    if len(netloc_parts) > 2:
      m_host_name = netloc_parts[-2]
    elif len(netloc_parts) == 2:
      m_host_name = netloc_parts[0]
    else:
      m_host_name = m_netloc

    return m_host_name

  @staticmethod
  def get_service_ip():
    try:
      service_name = os.getenv('SEARCH_SERVICE', 'orion-search-web')
      service_ip = socket.gethostbyname(service_name)
      return f"http://{service_ip}:8080"
    except socket.error as e:
      return f"Error resolving service IP: {e}"

  @staticmethod
  def check_service_status(service_name, host, port):
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
          try:
              s.connect((host, port))
              return True
          except socket.error:
              log.g().e(MANAGE_MESSAGES.S_SERVICE_NOT_INITIATED + " : " +  f"{service_name} is not running or not installed.")
              return False

  @staticmethod
  def extract_zip(from_path, to_path):
    os.makedirs(to_path, exist_ok=True)
    try:
      with zipfile.ZipFile(from_path, 'r') as zip_ref:
        zip_ref.extractall(to_path)
    except Exception as e:
      log.g().e(f"Error occurred while extracting {from_path}: {e}")

  @staticmethod
  def split_host_url(p_url):
    m_parsed_uri = urlparse(p_url)
    m_host_url = '{uri.scheme}://{uri.netloc}/'.format(uri=m_parsed_uri)
    if m_host_url.endswith("/"):
      m_host_url = m_host_url[:-1]

    m_subhost = p_url[len(m_host_url):]
    if len(m_subhost) == 1:
      m_subhost = "na"
    return m_host_url, m_subhost


  # Remove Extra Slashes
  @staticmethod
  def normalize_slashes(p_url):
    p_url = str(p_url)
    segments = p_url.split('/')
    correct_segments = []
    for segment in segments:
      if segment != '':
        correct_segments.append(segment)
    normalized_url = '/'.join(correct_segments)
    normalized_url = normalized_url.replace("http:/", "http://")
    normalized_url = normalized_url.replace("https:/", "https://")
    normalized_url = normalized_url.replace("ftp:/", "ftp://")
    return normalized_url

  @staticmethod
  def is_url_base_64(p_url):
    if str(p_url).startswith("duplicationHandlerService:"):
      return True
    else:
      return False

  @staticmethod
  def is_uri_validator(p_url):
    try:
      result = urlparse(p_url)
      return all([result.scheme, result.netloc])
    except:
      return False

  @staticmethod
  def clear_folder(p_path):
    for f in os.listdir(p_path):
      try:
        os.remove(os.path.join(p_path, f))
      except Exception as e:
        log.g().e(f"Error removing file {f}: {e}")

  @staticmethod
  def write_content_to_path(p_path, p_content):
    m_url_path = p_path
    file = open(m_url_path, "wb")
    file.write(p_content)
    file.close()

  # Extract URL Host
  @staticmethod
  def get_host_url(p_url):
    m_parsed_uri = urlparse(p_url)
    m_host_url = '{uri.scheme}://{uri.netloc}/'.format(uri=m_parsed_uri)
    if m_host_url.endswith("/"):
      m_host_url = m_host_url[:-1]
    return m_host_url

  @staticmethod
  def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text
