from docset.rust.defaults import RUST_STD_RULES, RUST_RULES
from docset.rust.types import to_dash_type
import os

DEBUG = os.getenv("DOCSET_DEBUG")

DOCSET_NAME = "RustNightly"
TEMPLATE_PLIST = "template/Info.plist"
TEMPLATE_ICON = "template/icon.png"

TYPE_MAP_FN = to_dash_type
RULES = RUST_RULES
