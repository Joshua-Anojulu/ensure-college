import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "app" / "static" / "index.html"
APP_JS = ROOT / "app" / "static" / "js" / "app.js"
STYLE = ROOT / "app" / "static" / "css" / "style.css"
MANIFEST = Path(__file__).with_name("dom_contract.json")
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag.lower()
        self.attrs = {name.lower(): value if value is not None else "" for name, value in attrs}
        self.parent = parent
        self.children = []


class ContractParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if node.tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def parse_index():
    parser = ContractParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    return parser.nodes


def get_by_id(nodes, element_id):
    return next((node for node in nodes if node.attrs.get("id") == element_id), None)


def class_tokens(node):
    return set((node.attrs.get("class") or "").split())


def matches_simple(node, selector):
    selector = selector.strip()
    if selector.endswith(":checked"):
        return matches_simple(node, selector.removesuffix(":checked")) and "checked" in node.attrs
    if selector.startswith("#"):
        return node.attrs.get("id") == selector[1:]
    if selector.startswith("."):
        return selector[1:] in class_tokens(node)

    attr_match = re.fullmatch(
        r"(?P<tag>[a-zA-Z][\w-]*)?(?:\[(?P<attr>[\w-]+)(?:=(?P<quote>[\"']?)(?P<value>.*?)(?P=quote))?\])?",
        selector,
    )
    if attr_match:
        tag = attr_match.group("tag")
        attr = attr_match.group("attr")
        value = attr_match.group("value")
        if tag and node.tag != tag.lower():
            return False
        if attr:
            attr = attr.lower()
            if attr not in node.attrs:
                return False
            if value is not None and node.attrs.get(attr) != value:
                return False
        return True

    return node.tag == selector.lower()


def matches_selector(nodes, selector):
    if "," in selector:
        return any(matches_selector(nodes, part.strip()) for part in selector.split(","))

    parts = selector.split()
    if len(parts) == 1:
        return any(matches_simple(node, parts[0]) for node in nodes)

    for node in nodes:
        if not matches_simple(node, parts[-1]):
            continue
        parent = node.parent
        wanted = list(reversed(parts[:-1]))
        for part in wanted:
            while parent is not None and not matches_simple(parent, part):
                parent = parent.parent
            if parent is None:
                break
            parent = parent.parent
        else:
            return True
    return False


def extract_app_js_queries():
    js = APP_JS.read_text(encoding="utf-8")
    ids = sorted(set(re.findall(r"getElementById\(\s*[\"']([^\"']+)[\"']\s*\)", js)))
    selectors = []
    for quote in ('"', "'"):
        selectors.extend(
            re.findall(
                r"querySelector(?:All)?\(\s*" + re.escape(quote) + r"(.+?)" + re.escape(quote) + r"\s*\)",
                js,
            )
        )
    return ids, sorted(set(selectors))


def extract_inline_consent_boot_ids():
    html = INDEX.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="site-consent-boot">(?P<script>.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return []
    return sorted(
        set(re.findall(r"getElementById\(\s*[\"']([^\"']+)[\"']\s*\)", match.group("script")))
    )


def css_has_class_rule(css, class_name):
    escaped = re.escape(class_name)
    return re.search(rf"\.{escaped}(?![\w-])", css) is not None


def test_manifest_matches_current_app_js_queries():
    manifest = load_manifest()
    ids, selectors = extract_app_js_queries()
    ids = sorted(set(ids).union(extract_inline_consent_boot_ids()))
    assert manifest["ids"] == ids
    assert manifest["selectors"] == selectors


def test_static_queried_selectors_exist_in_index():
    manifest = load_manifest()
    nodes = parse_index()

    missing_ids = [element_id for element_id in manifest["ids"] if get_by_id(nodes, element_id) is None]
    assert missing_ids == []

    dynamic = set(manifest["dynamic_selectors"])
    missing_selectors = [
        selector
        for selector in manifest["selectors"]
        if selector not in dynamic and not matches_selector(nodes, selector)
    ]
    assert missing_selectors == []


def test_required_element_types_and_profile_fields_survive():
    manifest = load_manifest()
    nodes = parse_index()

    for selector, contract in manifest["element_types"].items():
        node = get_by_id(nodes, selector.removeprefix("#"))
        assert node is not None, selector
        assert node.tag == contract["tag"], selector
        if "type" in contract:
            assert node.attrs.get("type") == contract["type"], selector

    for element_id, contract in manifest["profile_fields"].items():
        node = get_by_id(nodes, element_id)
        assert node is not None, element_id
        assert node.tag == contract["tag"], element_id
        assert node.attrs.get("name") == contract["name"], element_id
        if "type" in contract:
            assert node.attrs.get("type") == contract["type"], element_id


def test_required_data_values_survive():
    manifest = load_manifest()
    nodes = parse_index()

    opportunity_views = [
        node.attrs.get("data-view")
        for node in nodes
        if "opportunity-tab" in class_tokens(node)
    ]
    assert opportunity_views == manifest["opportunity_tab_data_view"]

    catalog_kinds = [
        node.attrs.get("data-kind")
        for node in nodes
        if "catalog-kind-tab" in class_tokens(node)
    ]
    assert catalog_kinds == manifest["catalog_kind_data_kind"]


def test_profile_checkbox_group_contract_survives():
    manifest = load_manifest()
    nodes = parse_index()

    for container_id, contract in manifest["profile_checkbox_groups"].items():
        container = get_by_id(nodes, container_id)
        fieldset = get_by_id(nodes, contract["fieldset_id"])
        assert container is not None, container_id
        assert fieldset is not None, contract["fieldset_id"]
        assert fieldset.tag == "fieldset"
        legends = [child for child in fieldset.children if child.tag == "legend"]
        assert legends, contract["fieldset_id"]


def test_emitted_classes_have_stylesheet_rules():
    manifest = load_manifest()
    css = STYLE.read_text(encoding="utf-8")
    missing = [
        class_name
        for class_name in manifest["emitted_classes"]
        if not css_has_class_rule(css, class_name)
    ]
    assert missing == []


def test_page_motion_does_not_use_window_scroll_listener():
    js = APP_JS.read_text(encoding="utf-8")
    assert "window.addEventListener(\"scroll\"" not in js
    assert "window.addEventListener('scroll'" not in js
