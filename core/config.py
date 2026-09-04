import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")
OTRS_URL_BASE = "https://atendimento.sead.pb.gov.br/otrs/index.pl"
OTRS_USER = os.getenv('OTRS_USER')
OTRS_PASS = os.getenv('OTRS_PASS')

OUTPUT_DIR = "dist"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

TEMPLATE_DIR = "templates"
TEMPLATE_FILE = os.path.join(TEMPLATE_DIR, "template.html")

ASSETS_DIR = os.path.join(TEMPLATE_DIR, "assets")
OUTPUT_ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")
