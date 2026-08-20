#!/usr/bin/env python3
"""Tests for check_release. Stdlib only; git and network are exercised through
real temporary repos and mocked fetches respectively."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_release as cr  # noqa: E402


def manifest(version="1.0.0", ref="v1.0.0", name="sdl"):
    return {
        "name": "relay",
        "plugins": [{
            "name": name,
            "version": version,
            "source": {"source": "git-subdir", "url": "https://example/x.git",
                       "path": "plugins/sdl", "ref": ref},
        }],
    }


class Semver(unittest.TestCase):
    def test_parses_three_part(self):
        self.assertEqual(cr.parse_semver("1.2.3"), (1, 2, 3))

    def test_rejects_partial_and_prerelease(self):
        for bad in ("1.2", "v1.2.3", "1.2.3-rc1", "1.2.3+build", "", "x"):
            self.assertIsNone(cr.parse_semver(bad), bad)

    def test_orders_numerically_not_lexically(self):
        self.assertGreater(cr.parse_semver("1.10.0"), cr.parse_semver("1.9.0"))


class PluginJson(unittest.TestCase):
    def test_reads_version(self):
        self.assertEqual(cr.version_from_plugin_json('{"version": "0.7.0"}'), "0.7.0")

    def test_missing_or_malformed_gives_none(self):
        self.assertIsNone(cr.version_from_plugin_json("{}"))
        self.assertIsNone(cr.version_from_plugin_json("not json"))
        self.assertIsNone(cr.version_from_plugin_json('{"version": 1}'))


class Changelog(unittest.TestCase):
    TEXT = "# Changelog\n\n## 1.0.0 — 2026-08-03\n\nthings\n\n## 0.7.0\n\nolder\n"

    def test_finds_entry_with_and_without_suffix(self):
        self.assertTrue(cr.changelog_has_entry(self.TEXT, "1.0.0"))
        self.assertTrue(cr.changelog_has_entry(self.TEXT, "0.7.0"))

    def test_missing_entry(self):
        self.assertFalse(cr.changelog_has_entry(self.TEXT, "1.1.0"))

    def test_does_not_match_a_version_prefix(self):
        # `## 1.0.0` must not satisfy a check for 1.0.0.1 or 1.0.01
        self.assertFalse(cr.changelog_has_entry(self.TEXT, "1.0.01"))

    def test_ignores_non_heading_mentions(self):
        self.assertFalse(cr.changelog_has_entry("released 1.4.0 yesterday", "1.4.0"))


class MajorRefs(unittest.TestCase):
    REUSABLE = ("on:\n"
                "  workflow_call:\n"
                "    inputs:\n"
                "      base:\n"
                "        type: string\n"
                "        default: origin/main\n"
                "      sdl_ref:\n"
                "        type: string\n"
                "        # Must track this workflow's own major.\n"
                "        default: v2\n")

    def test_reads_the_default_of_the_sdl_ref_input(self):
        self.assertEqual(cr.sdl_ref_default(self.REUSABLE), "v2")

    def test_a_sibling_inputs_default_is_not_read_as_sdl_ref(self):
        text = ("    inputs:\n"
                "      sdl_ref:\n"
                "        type: string\n"
                "      base:\n"
                "        default: origin/main\n")
        self.assertIsNone(cr.sdl_ref_default(text))

    def test_sdl_ref_without_a_default(self):
        self.assertIsNone(cr.sdl_ref_default(
            self.REUSABLE.replace("        default: v2\n", "")))

    def test_no_sdl_ref_input_at_all(self):
        self.assertIsNone(cr.sdl_ref_default("name: x\n"))

    def test_reads_the_caller_uses_ref(self):
        self.assertEqual(cr.caller_ref(
            "jobs:\n  validate:\n"
            "    uses: savioke/sdl/.github/workflows/sdl-validate.yml@v2\n"), "v2")

    def test_an_unrelated_uses_line_is_not_the_caller(self):
        self.assertIsNone(cr.caller_ref(
            "      - uses: actions/checkout@v7.0.1 # v7.0.1\n"))


class ManifestCheck(unittest.TestCase):
    def test_agreement(self):
        self.assertEqual(cr.check_manifest(manifest(), "sdl", "1.0.0"), [])

    def test_version_disagreement(self):
        errs = cr.check_manifest(manifest(version="0.7.0"), "sdl", "1.0.0")
        self.assertTrue(any("declares sdl '0.7.0'" in e for e in errs))

    def test_ref_pointing_at_a_branch_is_drift(self):
        errs = cr.check_manifest(manifest(ref="main"), "sdl", "1.0.0")
        self.assertTrue(any("source.ref 'main'" in e for e in errs))

    def test_ref_pointing_at_the_moving_alias_is_drift(self):
        errs = cr.check_manifest(manifest(ref="v1"), "sdl", "1.0.0")
        self.assertTrue(any("expected 'v1.0.0'" in e for e in errs))

    def test_unknown_plugin(self):
        errs = cr.check_manifest(manifest(name="other"), "sdl", "1.0.0")
        self.assertEqual(len(errs), 1)
        self.assertIn("no plugin named", errs[0])


class MalformedManifest(unittest.TestCase):
    """The manifest is fetched from another repo, so its shape is untrusted.
    Every case here must be reported as drift; none may raise."""

    def check(self, doc):
        errs = cr.check_manifest(doc, "sdl", "1.0.0")
        self.assertTrue(errs, f"expected drift for {doc!r}")
        return errs

    def test_source_as_a_bare_url_string(self):
        # The marketplace schema allows a string source. It carries no ref, so
        # it cannot satisfy the immutable-tag rule — but it must not crash.
        doc = manifest()
        doc["plugins"][0]["source"] = "https://github.com/savioke/sdl"
        errs = self.check(doc)
        self.assertTrue(any("non-object `source`" in e and "str" in e for e in errs))

    def test_source_of_other_scalar_types(self):
        for bad in (None, 7, True, ["v1.0.0"], []):
            with self.subTest(source=bad):
                doc = manifest()
                doc["plugins"][0]["source"] = bad
                self.assertTrue(any("non-object `source`" in e for e in self.check(doc)))

    def test_source_missing_entirely(self):
        doc = manifest()
        del doc["plugins"][0]["source"]
        self.assertTrue(any("non-object `source`" in e for e in self.check(doc)))

    def test_top_level_is_not_an_object(self):
        for bad in ([], "sdl", 7, None, True):
            with self.subTest(manifest=bad):
                errs = self.check(bad)
                self.assertIn("not an object with a `plugins` array", errs[0])

    def test_plugins_is_not_a_list(self):
        for bad in ({"sdl": {}}, "sdl", 7, None):
            with self.subTest(plugins=bad):
                errs = self.check({"plugins": bad})
                self.assertIn("not an object with a `plugins` array", errs[0])

    def test_plugins_list_holding_non_objects(self):
        errs = self.check({"plugins": ["sdl", 7, None, ["sdl"]]})
        self.assertIn("no plugin named", errs[0])

    def test_version_of_a_non_string_type(self):
        doc = manifest()
        doc["plugins"][0]["version"] = {"major": 1}
        self.assertTrue(any("repo says '1.0.0'" in e for e in self.check(doc)))


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def read(self, n=None):
        return self.body[:n] if n is not None else self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FetchManifest(unittest.TestCase):
    def test_network_failure_returns_error_not_exception(self):
        with mock.patch.object(cr.urllib.request, "urlopen",
                               side_effect=TimeoutError("slow")):
            data, err = cr.fetch_manifest("owner/repo")
        self.assertIsNone(data)
        self.assertIn("TimeoutError", err)

    def test_malformed_json_returns_error_not_exception(self):
        with mock.patch.object(cr.urllib.request, "urlopen",
                               return_value=FakeResponse(b"<html>404</html>")):
            data, err = cr.fetch_manifest("owner/repo")
        self.assertIsNone(data)
        self.assertIn("JSONDecodeError", err)

    def test_non_utf8_body_returns_error_not_exception(self):
        # The decode happens before the parse and raises UnicodeDecodeError,
        # which reaches the handler only because it subclasses ValueError.
        # Asserted explicitly so a narrowed except tuple fails here.
        for body in (b'{"name": "relay\xff", "plugins": []}',  # bad byte inside JSON
                     b"\xff\xfe\x00{",                          # not text at all
                     b"\xef\xbb\xbf\xc3\x28"):                  # BOM then bad sequence
            with self.subTest(body=body):
                with mock.patch.object(cr.urllib.request, "urlopen",
                                       return_value=FakeResponse(body)):
                    data, err = cr.fetch_manifest("owner/repo")
                self.assertIsNone(data)
                self.assertIn("UnicodeDecodeError", err)

    def test_oversized_body_is_refused_unparsed(self):
        body = b"[" + b" " * (cr.MAX_MANIFEST_BYTES + 10)
        with mock.patch.object(cr.urllib.request, "urlopen",
                               return_value=FakeResponse(body)):
            data, err = cr.fetch_manifest("owner/repo")
        self.assertIsNone(data)
        self.assertIn("exceeds", err)

    def test_well_formed_body_parses(self):
        body = json.dumps(manifest()).encode()
        with mock.patch.object(cr.urllib.request, "urlopen",
                               return_value=FakeResponse(body)):
            data, err = cr.fetch_manifest("owner/repo")
        self.assertIsNone(err)
        self.assertEqual(cr.check_manifest(data, "sdl", "1.0.0"), [])


CALLER_YML = """name: sdl
on:
  pull_request:
jobs:
  validate:
    uses: savioke/sdl/.github/workflows/sdl-validate.yml@{ref}
"""

# `base` deliberately precedes `sdl_ref` and carries a `default:` of its own:
# that is the shape a whole-file search for `default:` reads wrongly.
REUSABLE_YML = """name: sdl-validate
on:
  workflow_call:
    inputs:
      base:
        required: false
        type: string
        default: origin/main
      sdl_ref:
        required: false
        type: string
        default: {ref}
"""


class GitFixture(unittest.TestCase):
    """Builds a throwaway repo so the git-touching paths are covered for real."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")
        (self.repo / "plugins/sdl/.claude-plugin").mkdir(parents=True)
        self.write_version("1.0.0")
        self.write_workflows("v1")
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0.0\n\nfirst\n")
        self.commit("initial")

    def write_workflows(self, ref, caller_ref=None):
        workflows = self.repo / ".github/workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "sdl.yml").write_text(CALLER_YML.format(ref=caller_ref or ref))
        (workflows / "sdl-validate.yml").write_text(REUSABLE_YML.format(ref=ref))

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                       capture_output=True, text=True)

    def write_version(self, version):
        (self.repo / cr.PLUGIN_JSON).write_text(
            json.dumps({"name": "sdl", "version": version}, indent=2) + "\n")

    def add_changelog(self, version):
        p = self.repo / "CHANGELOG.md"
        p.write_text(p.read_text() + f"\n## {version}\n\nnotes\n")

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def released(self, **kw):
        kw.setdefault("plugin", "sdl")
        kw.setdefault("marketplace_repo", "owner/repo")
        kw.setdefault("offline", True)
        return cr.check_released(self.repo, **kw)


class ReleasedMode(GitFixture):
    def tag_release(self, version="1.0.0", major="v1"):
        self.git("tag", "-a", f"v{version}", "-m", f"release {version}")
        self.git("tag", "-f", "-a", major, "-m", f"alias {major}")

    def test_untagged_version_is_drift(self):
        errors, _ = self.released()
        self.assertTrue(any("was never released" in e for e in errors))

    def test_tagged_and_aliased_is_clean(self):
        self.tag_release()
        errors, _ = self.released()
        self.assertEqual(errors, [])

    def test_alias_left_behind_is_drift(self):
        self.git("tag", "-a", "v1.0.0", "-m", "r")
        self.git("tag", "-a", "v1", "-m", "stale")  # same commit here…
        self.write_version("1.1.0")
        self.add_changelog("1.1.0")
        self.commit("ship more")
        self.git("tag", "-a", "v1.1.0", "-m", "r")  # …but not moved with the new tag
        errors, _ = self.released()
        self.assertTrue(any("consumer CI is running a different tree" in e
                            for e in errors))

    def test_unreleased_shipped_change_is_drift(self):
        self.tag_release()
        (self.repo / "plugins/sdl/skills").mkdir(parents=True)
        (self.repo / "plugins/sdl/skills/SKILL.md").write_text("new instructions\n")
        self.commit("change a skill without releasing")
        errors, _ = self.released()
        self.assertTrue(any("not released" in e for e in errors))

    def test_a_manifest_body_of_literal_null_is_drift_not_an_outage(self):
        # json.loads("null") is None. Discriminating on the manifest value
        # rather than the fetch error would file this as "unreachable" and
        # silently skip the comparison it exists to make.
        self.tag_release()
        with mock.patch.object(cr, "fetch_manifest", return_value=(None, None)):
            errors, notes = self.released(offline=False)
        self.assertTrue(any("not an object with a `plugins` array" in e for e in errors))
        self.assertFalse(any("unreachable" in n for n in notes))

    def test_a_genuine_fetch_failure_is_still_only_a_note(self):
        self.tag_release()
        with mock.patch.object(cr, "fetch_manifest", return_value=(None, "HTTP 503")):
            errors, notes = self.released(offline=False)
        self.assertEqual(errors, [])
        self.assertTrue(any("unreachable" in n and "HTTP 503" in n for n in notes))

    def test_docs_only_change_after_a_release_is_fine(self):
        self.tag_release()
        (self.repo / "docs").mkdir()
        (self.repo / "docs/notes.md").write_text("prose\n")
        self.commit("docs only")
        errors, _ = self.released()
        self.assertEqual(errors, [])

    def test_missing_changelog_entry_is_drift(self):
        self.write_version("2.0.0")
        self.commit("bump only")
        self.git("tag", "-a", "v2.0.0", "-m", "r")
        self.git("tag", "-a", "v2", "-m", "r")
        errors, _ = self.released()
        self.assertTrue(any("no `## 2.0.0` entry" in e for e in errors))

    def test_unreachable_marketplace_warns_but_does_not_fail(self):
        self.tag_release()
        with mock.patch.object(cr, "fetch_manifest",
                               return_value=(None, "URLError fetching x")):
            errors, notes = self.released(offline=False)
        self.assertEqual(errors, [])
        self.assertTrue(any("unreachable" in n for n in notes))

    def test_validator_ref_left_on_the_previous_major_is_drift(self):
        self.write_version("2.0.0")
        self.add_changelog("2.0.0")
        self.write_workflows("v1", caller_ref="v2")
        self.commit("release 2.0.0 with sdl_ref still on v1")
        self.tag_release("2.0.0", "v2")
        errors, _ = self.released()
        self.assertTrue(any("sdl_ref defaults to 'v1'" in e for e in errors))

    def test_the_caller_may_still_name_the_old_major_on_the_release_commit(self):
        # release.sh verifies straight after cutting the alias, and the alias
        # the caller must move to did not exist until this very commit.
        self.write_version("2.0.0")
        self.add_changelog("2.0.0")
        self.write_workflows("v2", caller_ref="v1")
        self.commit("release 2.0.0")
        self.tag_release("2.0.0", "v2")
        errors, _ = self.released()
        self.assertEqual(errors, [])

    def test_a_caller_left_on_a_retired_major_is_drift_once_main_moves_on(self):
        self.write_version("2.0.0")
        self.add_changelog("2.0.0")
        self.write_workflows("v2", caller_ref="v1")
        self.commit("release 2.0.0")
        self.tag_release("2.0.0", "v2")
        (self.repo / "docs").mkdir()
        (self.repo / "docs/notes.md").write_text("work continues\n")
        self.commit("main moves on without moving the gate")
        errors, _ = self.released()
        self.assertTrue(any("still calls @v1" in e for e in errors))

    def test_a_missing_reusable_workflow_is_drift(self):
        self.tag_release()
        (self.repo / cr.REUSABLE_WORKFLOW).unlink()
        self.commit("drop the reusable workflow")
        errors, _ = self.released()
        self.assertTrue(any(f"{cr.REUSABLE_WORKFLOW} is missing" in e for e in errors))

    def test_disagreeing_marketplace_fails(self):
        self.tag_release()
        with mock.patch.object(cr, "fetch_manifest",
                               return_value=(manifest(ref="main"), None)):
            errors, _ = self.released(offline=False)
        self.assertTrue(any("source.ref 'main'" in e for e in errors))


class PrMode(GitFixture):
    def setUp(self):
        super().setUp()
        self.git("branch", "base")

    def test_shipped_change_without_bump_fails(self):
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/validate.py").write_text("print(1)\n")
        self.commit("ship a validator change")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("version did not increase" in e for e in errors))

    def test_shipped_change_with_bump_and_changelog_passes(self):
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/validate.py").write_text("print(1)\n")
        self.write_version("1.1.0")
        self.add_changelog("1.1.0")
        self.commit("ship a validator change, released as 1.1.0")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertEqual(errors, [])

    def test_bump_without_changelog_fails(self):
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/validate.py").write_text("print(1)\n")
        self.write_version("1.1.0")
        self.commit("forgot the changelog")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("CHANGELOG.md has no" in e for e in errors))

    def test_version_decrease_fails(self):
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/validate.py").write_text("print(1)\n")
        self.write_version("0.9.0")
        self.add_changelog("0.9.0")
        self.commit("wrong direction")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("version did not increase" in e for e in errors))

    def test_unorderable_base_version_skips_the_check_instead_of_crashing(self):
        # The base is history the PR author did not write. A version that is
        # present but not orderable must be noted and skipped, the same as a
        # base with no plugin.json — not raise out of a required check.
        for bad in ("1.0", "1.0.0-rc1", "v1.0.0", "1.0.0.1", "", "latest"):
            with self.subTest(base_version=bad):
                self.git("checkout", "-q", "base")
                self.write_version(bad)
                self.commit(f"base at {bad!r}")
                self.git("checkout", "-q", "main")
                (self.repo / "plugins/sdl/lib").mkdir(parents=True, exist_ok=True)
                (self.repo / "plugins/sdl/lib/validate.py").write_text(f"print({bad!r})\n")
                self.write_version("1.1.0")
                self.add_changelog("1.1.0")
                self.commit("ship against an unorderable base")
                errors, notes = cr.check_pr(self.repo, "base", "sdl")
                self.assertEqual(errors, [])
                self.assertTrue(any("skipping increase check" in n for n in notes))

    def test_base_without_a_plugin_json_at_all_still_skips(self):
        self.git("checkout", "-q", "base")
        (self.repo / cr.PLUGIN_JSON).unlink()
        self.commit("base predates the plugin")
        self.git("checkout", "-q", "main")
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/validate.py").write_text("print(1)\n")
        self.commit("ship")
        errors, notes = cr.check_pr(self.repo, "base", "sdl")
        self.assertEqual(errors, [])
        self.assertTrue(any("skipping increase check" in n for n in notes))

    def test_unparseable_head_version_is_still_an_error(self):
        # The head side is the PR author's own work — that one must fail.
        for bad in ("1.0", "1.0.0-rc1", "", "latest"):
            with self.subTest(head_version=bad):
                self.write_version(bad)
                self.commit(f"head at {bad!r}")
                errors, _ = cr.check_pr(self.repo, "base", "sdl")
                self.assertTrue(any("not X.Y.Z" in e for e in errors))

    def test_docs_only_pr_needs_no_bump(self):
        (self.repo / "docs").mkdir()
        (self.repo / "docs/x.md").write_text("prose\n")
        self.commit("docs only")
        errors, notes = cr.check_pr(self.repo, "base", "sdl")
        self.assertEqual(errors, [])
        self.assertTrue(any("no version bump required" in n for n in notes))

    def test_reusable_workflow_counts_as_shipped(self):
        (self.repo / ".github/workflows/sdl-validate.yml").write_text(
            REUSABLE_YML.format(ref="v1") + "# a consumer-visible edit\n")
        self.commit("change the consumer-facing workflow")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("version did not increase" in e for e in errors))

    def test_shipped_change_made_on_the_base_after_branching_is_not_ours(self):
        # main ships something after we branched; our PR only touches docs.
        # A two-dot comparison would blame us for it and demand a version bump.
        self.git("checkout", "-q", "base")
        (self.repo / "plugins/sdl/lib").mkdir(parents=True)
        (self.repo / "plugins/sdl/lib/other.py").write_text("someone else\n")
        self.write_version("1.1.0")
        self.add_changelog("1.1.0")
        self.commit("someone else's release")
        self.git("checkout", "-q", "main")
        (self.repo / "docs").mkdir()
        (self.repo / "docs/x.md").write_text("prose\n")
        self.commit("docs only")
        errors, notes = cr.check_pr(self.repo, "base", "sdl")
        self.assertEqual(errors, [])
        self.assertTrue(any("no version bump required" in n for n in notes))

    def test_a_major_bump_that_forgets_sdl_ref_fails(self):
        self.write_version("2.0.0")
        self.add_changelog("2.0.0")
        self.commit("bump the major, leave sdl_ref behind")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("sdl_ref defaults to 'v1'" in e for e in errors))

    def test_a_major_bump_that_moves_sdl_ref_passes(self):
        # The caller stays on v1 on purpose: it may only move once the v2 alias
        # exists, which is after this PR merges and is released.
        self.write_version("2.0.0")
        self.add_changelog("2.0.0")
        self.write_workflows("v2", caller_ref="v1")
        self.commit("bump the major and sdl_ref together")
        errors, _ = cr.check_pr(self.repo, "base", "sdl")
        self.assertEqual(errors, [])

    def test_sdl_ref_is_checked_on_a_docs_only_pr_too(self):
        # The wrong ref is already on the base, so this PR ships nothing and is
        # told about it anyway — otherwise it goes unseen until the next bump.
        self.write_workflows("v9")
        self.commit("a ref nobody is watching")
        self.git("branch", "-f", "base", "HEAD")
        (self.repo / "docs").mkdir()
        (self.repo / "docs/x.md").write_text("prose\n")
        self.commit("docs only")
        errors, notes = cr.check_pr(self.repo, "base", "sdl")
        self.assertTrue(any("sdl_ref defaults to 'v9'" in e for e in errors))
        self.assertTrue(any("no version bump required" in n for n in notes))

    def test_missing_base_ref_is_reported(self):
        errors, _ = cr.check_pr(self.repo, "origin/nope", "sdl")
        self.assertTrue(any("not found" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
