import pytest
from prosemirror_test_builder import schema, out, builders
from prosemirror_transform import Transform
from prosemirror_model import Schema


doc = out["doc"]
blockquote = out["blockquote"]
pre = out["pre"]
h1 = out["h1"]
h2 = out["h2"]
p = out["p"]
li = out["li"]
ul = out["ul"]
ol = out["ol"]
em = out["em"]
strong = out["strong"]
code = out["code"]
a = out["a"]
img = out["img"]
br = out["br"]
hr = out["hr"]


@pytest.mark.parametrize(
    "doc,mark,expect",
    [
        (
            doc(p("hello <a>there<b>!")),
            schema.mark("strong"),
            doc(p("hello ", strong("there"), "!")),
        ),
        (
            doc(p("hello ", strong("<a>there"), "!<b>")),
            schema.mark("strong"),
            doc(p("hello ", strong("there!"))),
        ),
        (
            doc(p("one <a>two ", em("three<b> four"))),
            schema.mark("strong"),
            doc(p("one ", strong("two ", em("three")), em(" four"))),
        ),
        (
            doc(
                p("before"), blockquote(p("the variable is called <a>i<b>")), p("after")
            ),
            schema.mark("code"),
            doc(
                p("before"),
                blockquote(p("the variable is called ", code("i"))),
                p("after"),
            ),
        ),
        (
            doc(p("hi <a>this"), blockquote(p("is")), p("a docu<b>ment"), p("!")),
            schema.mark("em"),
            doc(
                p("hi ", em("this")),
                blockquote(p(em("is"))),
                p(em("a docu"), "ment"),
                p("!"),
            ),
        ),
    ],
)
def test_add_mark(doc, mark, expect, test_transform):
    test_transform(Transform(doc).add_mark(doc.tag["a"], doc.tag["b"], mark), expect)


def test_does_not_remove_non_excluded_marks_of_the_same_type():
    schema = Schema(
        {
            "nodes": {"doc": {"content": "text*"}, "text": {}},
            "marks": {"comment": {"excludes": "", "attrs": {"id": {}}}},
        }
    )
    tr = Transform(
        schema.node(
            "doc", None, schema.text("hi", [schema.mark("comment", {"id": 10})])
        )
    )
    tr.add_mark(0, 2, schema.mark("comment", {"id": 20}))
    assert len(tr.doc.first_child.marks) == 2


def test_can_remote_multiple_excluded_marks():
    schema = Schema(
        {
            "nodes": {"doc": {"content": "text*"}, "text": {}},
            "marks": {"big": {"excludes": "small1 small2"}, "small1": {}, "small2": {}},
        }
    )
    tr = Transform(
        schema.node(
            "doc",
            None,
            schema.text("hi", [schema.mark("small1"), schema.mark("small2")]),
        )
    )
    assert len(tr.doc.first_child.marks) == 2
    tr.add_mark(0, 2, schema.mark("big"))
    assert len(tr.doc.first_child.marks) == 1


@pytest.mark.parametrize(
    "doc,mark,expect",
    [
        (
            doc(p(em("hello <a>world<b>!"))),
            schema.mark("em"),
            doc(p(em("hello "), "world", em("!"))),
        ),
        (
            doc(p(em("hello"), " <a>world<b>!")),
            schema.mark("em"),
            doc(p(em("hello"), " <a>world<b>!")),
        ),
        (
            doc(p("<a>hello ", a("link<b>"))),
            schema.mark("link", {"href": "foo"}),
            doc(p("hello link")),
        ),
        (
            doc(p("<a>hello ", a("link<b>"))),
            schema.mark("link", {"href": "foo"}),
            doc(p("hello link")),
        ),
        (
            doc(p("hello ", a("link"))),
            schema.mark("link", {"href": "bar"}),
            doc(p("hello ", a("link"))),
        ),
        (
            doc(
                blockquote(p(em("much <a>em")), p(em("here too"))),
                p("between", em("...")),
                p(em("end<b>")),
            ),
            schema.mark("em"),
            doc(
                blockquote(p(em("much "), "em"), p("here too")),
                p("between..."),
                p("end"),
            ),
        ),
        (
            doc(p("<a>hello, ", em("this is ", strong("much"), " ", a("markup<b>")))),
            None,
            doc(p("<a>hello, this is much markup")),
        ),
    ],
)
def test_remove_mark(doc, mark, expect, test_transform):
    test_transform(
        Transform(doc).remove_mark(doc.tag.get("a", 0), doc.tag.get("b", 0), mark),
        expect,
    )


@pytest.mark.parametrize(
    "doc,nodes,expect",
    [
        (
            doc(p("hello<a>there")),
            schema.node("hard_break"),
            doc(p("hello", br, "<a>there")),
        ),
        (
            doc(p("one"), "<a>", p("two<2>")),
            schema.node("paragraph"),
            doc(p("one"), p(), "<a>", p("two<2>")),
        ),
        (
            doc(p("one"), "<a>", p("two<2>")),
            [
                schema.node("paragraph", None, [schema.text("hi")]),
                schema.node("horizontal_rule"),
            ],
            doc(p("one"), p("hi"), hr, "<a>", p("two<2>")),
        ),
        (
            doc(blockquote(p("he<before>y"), "<a>"), p("after<after>")),
            schema.node("paragraph"),
            doc(blockquote(p("he<before>y"), p()), p("after<after>")),
        ),
        (
            doc(blockquote("<a>", p("he<1>y")), p("after<2>")),
            schema.node("paragraph"),
            doc(blockquote(p(), "<a>", p("he<1>y")), p("after<2>")),
        ),
        (
            doc(p("foo<a>bar")),
            schema.nodes["list_item"].create_and_fill(),
            doc(p("foo"), ol(li(p())), p("bar")),
        ),
    ],
)
def test_insert(doc, nodes, expect, test_transform):
    test_transform(Transform(doc).insert(doc.tag.get("a", 0), nodes), expect)


@pytest.mark.parametrize(
    "doc,expect",
    [
        (
            doc(p("<1>one"), "<a>", p("tw<2>o"), "<b>", p("<3>three")),
            doc(p("<1>one"), "<a><2>", p("<3>three")),
        ),
        (doc(blockquote("<a>", p("hi"), "<b>"), p("x")), doc(blockquote(p()), p("x"))),
        (
            doc(blockquote(p("a"), "<a>", p("b"), "<b>"), p("c<1>")),
            doc(blockquote(p("a")), p("c<1>")),
        ),
        (doc(pre("fo<a>o"), p("b<b>ar", img)), doc(pre("fo"), p("ar", img))),
        (doc(pre("fo<a>o"), p(em("b<b>ar"))), doc(pre("fo"), p(em("ar")))),
    ],
)
def test_delete(doc, expect, test_transform):
    tr = Transform(doc).delete(doc.tag.get("a"), doc.tag.get("b"))
    test_transform(tr, expect)