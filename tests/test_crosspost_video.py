"""General crosspost-video discovery — no hard-coded incident IDs required."""
from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import aiohttp  # noqa: F401
    import feedparser  # noqa: F401
    import dotenv  # noqa: F401
except ImportError:
    for name in ("aiohttp", "feedparser", "dotenv"):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)
    sys.modules["aiohttp"].ClientSession = object
    sys.modules["aiohttp"].ClientTimeout = lambda total=None: None
    sys.modules["feedparser"].parse = lambda *a, **k: None
    sys.modules["dotenv"].load_dotenv = lambda *a, **k: None

import importlib.util


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v3 = load("crosspost_v3", "testing area/reddit_main_v3.py")
proxy = load("crosspost_proxy", "testing area/reddit_proxy.py")


class OriginalDiscoveryTests(unittest.TestCase):
    def test_labeled_original_without_keyword(self):
        path = v3.find_crosspost_original_path(
            "See the [Original Post](/r/Alpha/comments/parent01/title/)",
            "/r/Beta/comments/child001/",
        )
        self.assertEqual(path, "/r/Alpha/comments/parent01/")

    def test_html_anchor_original_post(self):
        path = v3.find_crosspost_original_path(
            '<a href="https://www.reddit.com/r/Alpha/comments/parent02/x/">Original Post</a>',
            "/r/Beta/comments/child002/",
        )
        self.assertEqual(path, "/r/Alpha/comments/parent02/")

    def test_profile_original_still_resolves(self):
        path = v3.find_crosspost_original_path(
            'crossposted this from <a href="/user/someuser/comments/parent03/clip/">u/someuser</a>',
            "/r/Beta/comments/child003/",
        )
        self.assertEqual(path, "/user/someuser/comments/parent03/")

    def test_own_slugged_link_is_skipped(self):
        html = (
            'crossposted this from <a href="/r/Beta/comments/child004/child_slug/">self</a> '
            '<a href="/r/Alpha/comments/parent04/orig_slug/">orig</a>'
        )
        path = v3.find_crosspost_original_path(html, "/r/Beta/comments/child004/child_slug/")
        self.assertEqual(path, "/r/Alpha/comments/parent04/")

    def test_body_link_without_crosspost_context_is_not_a_parent(self):
        self.assertIsNone(v3.find_crosspost_original_path(
            "related reading /r/Alpha/comments/parent05/title/",
            "/r/Beta/comments/child005/",
        ))

    def test_distant_crosspost_keyword_is_not_a_parent(self):
        text = (
            "I like to crosspost sometimes.\n"
            + ("word " * 80)
            + "\nRelated reading /r/Alpha/comments/parent99/title/"
        )
        self.assertIsNone(v3.find_crosspost_original_path(
            text, "/r/Beta/comments/child099/",
        ))

    def test_foreign_host_rejected(self):
        self.assertIsNone(v3.find_crosspost_original_path(
            "crosspost https://not-reddit.example/r/Alpha/comments/parent06/",
            "/r/Beta/comments/child006/",
        ))

    def test_self_parent_id_is_dropped(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child007/",
            base={},
            post_json={"crosspost_parent": "t3_child007"},
        )
        self.assertEqual(source, {})

    def test_id_only_structured_parent(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child011/",
            base={},
            post_json={"crosspost_parent": "t3_parent11"},
        )
        self.assertEqual(source.get("id"), "parent11")
        self.assertNotEqual(source.get("id"), "child011")

    def test_mismatched_parent_id_and_permalink_rejected(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child012/",
            base={},
            post_json={
                "crosspost_parent_list": [{
                    "id": "child012",
                    "permalink": "/r/Alpha/comments/parent12/orig/",
                }],
            },
        )
        self.assertEqual(source, {})

    def test_scheme_relative_foreign_host_rejected(self):
        self.assertIsNone(v3.find_crosspost_original_path(
            "crosspost from //evil.example/r/Alpha/comments/parent13/",
            "/r/Beta/comments/child013/",
        ))

    def test_structured_parent_one_hop(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child008/",
            base={},
            post_json={
                "crosspost_parent_list": [{
                    "id": "parent08",
                    "permalink": "/r/Alpha/comments/parent08/orig/",
                    "media": {"reddit_video": {
                        "fallback_url": "https://v.redd.it/videoid08/DASH_720.mp4",
                    }},
                }],
            },
        )
        self.assertEqual(source.get("id"), "parent08")
        self.assertEqual(source.get("vred_id"), "videoid08")
        self.assertFalse(v3.is_same_reddit_post(source.get("path"), "/r/Beta/comments/child008/"))


class VideoEligibilityTests(unittest.TestCase):
    def test_audio_cover_filtered(self):
        cover = "https://proxy.embedez.com/render/audio?cover=https://i.redd.it/x.jpg"
        self.assertTrue(proxy.is_audio_cover_url(cover))
        self.assertFalse(proxy.is_motion_video_item({"kind": "video", "url": cover}))
        media = proxy.filter_proxy_media([
            {"kind": "video", "url": cover},
            {"kind": "image", "url": "https://i.redd.it/x.jpg"},
        ])
        self.assertEqual(len(media), 1)
        self.assertEqual(media[0]["kind"], "image")

    def test_proxy_og_skips_audio_cover(self):
        media = proxy._media_from_og({
            "og:video": "https://proxy.embedez.com/render/audio?cover=x",
            "og:image": ["https://i.redd.it/still.jpg"],
        })
        self.assertTrue(all(item["kind"] != "video" for item in media))

    def test_proxy_og_keeps_first_motion_and_skips_later_cover(self):
        page = (
            '<meta property="og:video" content="https://v.redd.it/motion456/DASH_720.mp4"/>'
            '<meta property="og:video" content="https://proxy.embedez.com/render/audio?cover=x"/>'
        )
        meta = proxy._og_meta(page)
        media = proxy._media_from_og(meta)
        videos = [item for item in media if item.get("kind") == "video"]
        self.assertEqual(len(videos), 1)
        self.assertIn("motion456", videos[0]["url"])
        self.assertFalse(any(proxy.is_audio_cover_url(item.get("url")) for item in media))

    def test_proxy_og_prefers_later_motion_video(self):
        page = (
            '<meta property="og:video" content="https://proxy.embedez.com/render/audio?cover=x"/>'
            '<meta property="og:video" content="https://v.redd.it/motion123/DASH_1080.mp4"/>'
            '<meta property="og:image" content="https://i.redd.it/still.jpg"/>'
        )
        meta = proxy._og_meta(page)
        media = proxy._media_from_og(meta)
        videos = [item for item in media if item.get("kind") == "video"]
        self.assertEqual(len(videos), 1)
        self.assertIn("motion123", videos[0]["url"])
        self.assertFalse(any(proxy.is_audio_cover_url(item.get("url")) for item in media))

    def test_encoded_video_id_and_preview_negative(self):
        encoded = "https://x.test/?videoUrl=https%3A%2F%2Fv.redd.it%2Fvideoid09%2FDASH_1080.mp4"
        self.assertEqual(v3.extract_vreddit_id_from_media_url(encoded), "videoid09")
        self.assertIsNone(v3.extract_vreddit_id_from_media_url(
            "https://external-preview.redd.it/videoid09.jpg"))

    def test_images_are_not_usable_when_video_was_requested(self):
        result = {"media": [{"kind": "image", "url": "https://i.redd.it/x.jpg"}]}
        self.assertFalse(v3._proxy_result_usable(result, True))
        self.assertTrue(v3._proxy_result_usable(result, False))

    def test_path_aliases_only_for_profile_posts(self):
        aliases = v3._path_aliases("/user/sampleuser/comments/parent10/")
        self.assertEqual(aliases[0], "/user/sampleuser/comments/parent10/")
        self.assertIn("/r/u_sampleuser/comments/parent10/", aliases)
        self.assertEqual(v3._path_aliases("/r/Beta/comments/child010/"),
                         ["/r/Beta/comments/child010/"])


class UnrelatedBodyLinkTests(unittest.TestCase):
    def test_crosspost_keyword_plus_unrelated_link_is_not_a_parent(self):
        text = (
            "This is a crosspost. Unrelated discussion: "
            "https://www.reddit.com/r/example/comments/abc123/topic/"
        )
        self.assertIsNone(v3.find_crosspost_original_path(
            text, "/r/example/comments/child99/",
        ))


class NewsIncidentMediaFixtures(unittest.TestCase):
    """Both Ananta incidents are parser/resolver fixtures only — not routing."""

    CASES = (
        ("1x6h1mf", "1x6h1a5", "1y2gic17nlvh1"),
        ("1x6lgak", "1x6lbhb", "22e7ve17smvh1"),
    )

    def test_structured_parent_recovers_motion_for_both_incidents(self):
        for child, parent, video in self.CASES:
            with self.subTest(child=child):
                source = v3.resolve_crosspost_source(
                    own_path=f"/r/NewsSub/comments/{child}/",
                    base={},
                    post_json={
                        "crosspost_parent_list": [{
                            "id": parent,
                            "permalink": f"/r/SourceSub/comments/{parent}/orig/",
                            "media": {"reddit_video": {
                                "fallback_url": f"https://v.redd.it/{video}/DASH_1080.mp4",
                            }},
                        }],
                    },
                )
                self.assertEqual(source.get("id"), parent)
                self.assertEqual(source.get("vred_id"), video)
                self.assertFalse(v3.is_same_reddit_post(
                    source.get("path"), f"/r/NewsSub/comments/{child}/"))

    def test_incident_dedup_keys_are_child_not_parent(self):
        for child, parent, _video in self.CASES:
            with self.subTest(child=child):
                path = f"/r/NewsSub/comments/{child}/slug/"
                key = f"NewsSub_{v3.extract_post_id(path)}"
                self.assertEqual(key, f"NewsSub_{child}")
                self.assertNotIn(parent, key)

    def test_html_labeled_original_and_og_motion_for_both_incidents(self):
        for child, parent, video in self.CASES:
            with self.subTest(child=child):
                html = (
                    f'<a href="/r/SourceSub/comments/{parent}/orig/">Original Post</a>'
                    f'<meta property="og:video" content="https://proxy.embedez.com/render/audio?cover=x"/>'
                    f'<meta property="og:video" content="https://v.redd.it/{video}/DASH_1080.mp4"/>'
                )
                path = v3.find_crosspost_original_path(
                    html, f"/r/NewsSub/comments/{child}/")
                self.assertEqual(path, f"/r/SourceSub/comments/{parent}/")
                meta = proxy._og_meta(html)
                media = proxy._media_from_og(meta)
                videos = [item for item in media if item.get("kind") == "video"]
                self.assertEqual(len(videos), 1)
                self.assertEqual(
                    v3.extract_vreddit_id_from_media_url(videos[0]["url"]), video)
                encoded = (
                    "https://proxy.embedez.com/render/video.mp4?"
                    f"videoUrl=https%3A%2F%2Fv.redd.it%2F{video}%2FCMAF_1080.mp4"
                    f"&audioUrl=https%3A%2F%2Fv.redd.it%2F{video}%2FCMAF_AUDIO_128.mp4"
                )
                self.assertEqual(v3.extract_vreddit_id_from_media_url(encoded), video)


class ChildIdentityTests(unittest.TestCase):
    def test_card_path_helpers_keep_child_id(self):
        child = "/r/Beta/comments/child011/slug/"
        parent = "/r/Alpha/comments/parent11/"
        self.assertEqual(v3.extract_post_id(child), "child011")
        self.assertNotEqual(v3.extract_post_id(child), v3.extract_post_id(parent))
        self.assertTrue(v3.is_same_reddit_post(child, "/r/Beta/comments/child011/"))


class NativeAndQualityTests(unittest.TestCase):
    def test_arctic_native_path_resolves_structured_parent(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child014/",
            base={},
            arctic={
                "crosspost_parent_list": [{
                    "id": "parent14",
                    "permalink": "/r/Alpha/comments/parent14/orig/",
                    "media": {"reddit_video": {
                        "fallback_url": "https://v.redd.it/origvid14/DASH_1080.mp4",
                    }},
                }],
            },
        )
        self.assertEqual(source.get("id"), "parent14")
        self.assertEqual(source.get("vred_id"), "origvid14")
        self.assertNotEqual(source.get("id"), "child014")
        self.assertEqual(source.get("provenance"), "structured-archive")

    def test_poster_only_proxy_does_not_replace_parent_video_id(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child015/",
            base={},
            post_json={
                "crosspost_parent_list": [{
                    "id": "parent15",
                    "permalink": "/r/Alpha/comments/parent15/orig/",
                    "media": {"reddit_video": {
                        "fallback_url": "https://v.redd.it/origvid15/DASH_1080.mp4",
                    }},
                }],
            },
        )
        poster = {"media": [{"kind": "image", "url": "https://i.redd.it/poster.jpg"}]}
        self.assertFalse(v3._proxy_result_usable(poster, True))
        self.assertEqual(source.get("vred_id"), "origvid15")
        self.assertNotEqual(source.get("vred_id"), "child015")

    def test_validated_1080_beats_720_base(self):
        quality = {"url": "ez1080", "width": 1920, "height": 1080, "has_audio": True}
        base = {"url": "vx720", "width": 1280, "height": 720, "has_audio": True}
        self.assertIs(v3.prefer_quality_candidate(quality, base), quality)

    def test_default_720_cannot_displace_healthy_higher_vx(self):
        quality = {"url": "ez720", "width": 1280, "height": 720, "has_audio": True}
        base = {"url": "vx1080", "width": 1920, "height": 1080, "has_audio": True}
        self.assertIs(v3.prefer_quality_candidate(quality, base), base)

    def test_failed_quality_keeps_base(self):
        base = {"url": "vx720", "width": 1280, "height": 720, "has_audio": True}
        self.assertIs(v3.prefer_quality_candidate(None, base), base)

    def test_audio_loss_keeps_vxreddit_base(self):
        quality = {"url": "ez1080", "width": 1920, "height": 1080, "has_audio": False}
        base = {"url": "vx720", "width": 1280, "height": 720, "has_audio": True}
        self.assertIs(v3.prefer_quality_candidate(quality, base), base)

    def test_encoded_1080_pairing_keeps_original_id_not_child(self):
        video = "22e7ve17smvh1"
        child = "1x6lgak"
        encoded = (
            "https://proxy.embedez.com/render/video.mp4?"
            f"videoUrl=https%3A%2F%2Fv.redd.it%2F{video}%2FCMAF_1080.mp4"
            f"&audioUrl=https%3A%2F%2Fv.redd.it%2F{video}%2FCMAF_AUDIO_128.mp4"
        )
        self.assertEqual(v3.extract_vreddit_id_from_media_url(encoded), video)
        self.assertNotEqual(v3.extract_vreddit_id_from_media_url(encoded), child)
        self.assertIsNone(v3.extract_vreddit_id_from_media_url(
            "https://proxy.embedez.com/render/audio?cover=https://i.redd.it/x.jpg"))

    def test_gallery_order_preserved_through_filter(self):
        media = [
            {"kind": "image", "url": "https://i.redd.it/a.jpg"},
            {"kind": "gif", "url": "https://i.redd.it/b.gif"},
            {"kind": "image", "url": "https://i.redd.it/c.jpg"},
        ]
        filtered = proxy.filter_proxy_media(media)
        self.assertEqual([item["url"] for item in filtered], [item["url"] for item in media])

    def test_audio_cover_failure_keeps_proxy_images(self):
        mixed = [
            {"kind": "image", "url": "https://i.redd.it/keep-a.jpg"},
            {"kind": "video", "url": "https://proxy.embedez.com/render/audio?cover=https://i.redd.it/x.jpg"},
            {"kind": "image", "url": "https://i.redd.it/keep-b.jpg"},
        ]
        filtered = proxy.filter_proxy_media(mixed)
        self.assertEqual([item["kind"] for item in filtered], ["image", "image"])
        self.assertTrue(v3._proxy_result_usable({"media": filtered}, False))
        self.assertFalse(any(proxy.is_audio_cover_url(item.get("url")) for item in filtered))

    def test_malformed_parent_id_is_not_a_source(self):
        source = v3.resolve_crosspost_source(
            own_path="/r/Beta/comments/child016/",
            base={},
            post_json={"crosspost_parent": "not a t3 id"},
        )
        self.assertEqual(source, {})

    def test_child_card_keeps_identity_with_five_image_gallery(self):
        child_url = "https://www.reddit.com/r/NewsSub/comments/1x6lgak/yacht/"
        data = {
            "title": "Child title stays",
            "author": "child_author",
            "body": "child body text",
            "media": [{"kind": "image", "url": f"https://i.redd.it/g{i}.jpg"} for i in range(5)],
            "stats": {"comments": 4, "ups": 8},
            "crosspost": {
                "path": "/user/orig/comments/1x6lbhb/",
                "url": "https://www.reddit.com/user/orig/comments/1x6lbhb/",
            },
            "op_comment": None,
            "youtube_url": None,
        }
        payload = v3.build_v3_payload("NewsSub", data, child_url, 1700000000)
        blob = json.dumps(payload)
        self.assertIn("Child title stays", blob)
        self.assertIn("child_author", blob)
        self.assertIn("r/NewsSub", blob)
        self.assertIn("child body text", blob)
        self.assertIn("Crosspost of", blob)
        self.assertIn("u/orig", blob)
        row = [c for c in payload["components"][0]["components"] if c.get("type") == 1][0]
        read_post = row["components"][0]
        self.assertEqual(read_post["label"], "Read Post")
        self.assertEqual(read_post["url"], child_url)
        self.assertNotIn("1x6lbhb", read_post["url"])
        galleries = [c for c in payload["components"][0]["components"] if c.get("type") == 12]
        urls = [item["media"]["url"] for g in galleries for item in g["items"]]
        self.assertEqual(urls, [f"https://i.redd.it/g{i}.jpg" for i in range(5)])


if __name__ == "__main__":
    unittest.main()
