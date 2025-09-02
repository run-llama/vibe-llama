import sys
import xml.etree.ElementTree as ET
from typing import Dict, cast, List

from vibe_llama.starter.utils import Retriever


def print_verbose(content: str, verbose: bool) -> None:
    if verbose:
        print(content, file=sys.stderr)


def parse_xml_string(content: str) -> Dict[str, List[str]]:
    root = ET.fromstring(content)
    if root.tag == "result":
        match_dct = {"result": []}
        for i, match in enumerate(root.findall("match")):
            match_dct["result"].append(
                cast(str, cast(ET.Element, match.find("content")).text)
            )
        return match_dct
    else:
        errstr = ""
        for err in root.findall("message"):
            errstr += cast(str, cast(ET.Element, err.find("content")).text)
        return {"error": [errstr]}


VibeLlamaDocsRetriever = Retriever
