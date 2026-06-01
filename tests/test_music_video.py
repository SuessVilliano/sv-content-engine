"""music_video.py — the pure beat-edit logic (no audio/ffmpeg needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import music_video as mv  # noqa: E402

SONG = {
    "tempo": 120,
    "duration": 4.0,
    "beats": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
    "downbeats": [0.0, 2.0, 4.0],
    "sections": [{"start": 0.0, "label": "intro"}],
    "lyrics": [{"text": "first line", "start": 0.0, "end": 1.0},
               {"text": "second line", "start": 2.0, "end": 3.0}],
}


def test_cut_points_downbeat():
    pts = mv._cut_points(SONG, "downbeat", 1)
    assert pts == [0.0, 2.0, 4.0]


def test_cut_points_every_beat():
    pts = mv._cut_points(SONG, "beat", 1)
    assert pts == SONG["beats"]


def test_cut_points_seconds():
    pts = mv._cut_points(SONG, "seconds", 1)
    assert pts == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_cut_points_always_bounded_and_sorted():
    pts = mv._cut_points(SONG, "beat", 1)
    assert pts[0] == 0.0 and pts[-1] == SONG["duration"]
    assert pts == sorted(pts)


def test_build_edit_map_cycles_clips():
    cuts = mv.build_edit_map(SONG, ["a.mp4", "b.mp4"], cut="downbeat")
    assert [c.clip for c in cuts] == ["a.mp4", "b.mp4"]  # 2 windows, 2 clips
    assert cuts[0].start == 0.0 and cuts[0].end == 2.0


def test_build_edit_map_requires_clips():
    import pytest
    with pytest.raises(ValueError):
        mv.build_edit_map(SONG, [])


def test_lyric_at_overlap():
    assert mv._lyric_at(SONG, 0.0, 1.0) == "first line"
    assert mv._lyric_at(SONG, 2.5, 2.8) == "second line"
    assert mv._lyric_at(SONG, 1.2, 1.4) == ""


def test_generate_srt_format():
    srt = mv.generate_srt(SONG)
    assert "first line" in srt and "-->" in srt
    assert srt.startswith("1\n")
