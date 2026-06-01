"""engine.py — parsing, planning, live execution, and the editor."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import engine  # noqa: E402
import brands  # noqa: E402


# ── fixtures ─────────────────────────────────────────────────────────────────
def _brand(tmp_path):
    b = brands.load_brand("source_vessel")
    b.raw["base_dir"] = str(tmp_path)   # sandbox all output
    return b


def _job(spec, brand):
    p = engine.plan(spec, brand)
    return {
        "id": time.strftime("%H%M%S") + "-test",
        "ts": "2026-06-01T00:00:00",
        "spec": spec.to_dict(), "plan": p, "status": "queued",
        "step_status": {s["name"]: "pending" for s in p["steps"]}, "output": None,
    }


# ── parse ────────────────────────────────────────────────────────────────────
def test_parse_detects_music_video_and_song():
    spec = engine.parse("music video for midnight_bloom.mp3, neon, cut on the beat",
                        use_llm=False)
    assert spec.kind == "music_video"
    assert spec.song == "midnight_bloom.mp3"
    assert "neon" in spec.looks


def test_parse_detects_short_and_looks():
    spec = engine.parse("make a 30s cinematic short about discipline", use_llm=False)
    assert spec.kind == "short"
    assert "cinematic" in spec.looks


def test_parse_filters_unknown_looks():
    spec = engine.parse("short about x, sparkleglow look", use_llm=False)
    assert "sparkleglow" not in spec.looks


# ── plan ─────────────────────────────────────────────────────────────────────
def test_plan_music_video_steps():
    spec = engine.parse("music video for s.mp3", use_llm=False)
    names = [s["name"] for s in engine.plan(spec, None)["steps"]]
    assert names == ["ingest", "clips", "assemble"]


def test_plan_short_has_full_pipeline():
    spec = engine.parse("30s short about focus", use_llm=False)
    names = [s["name"] for s in engine.plan(spec, None)["steps"]]
    assert names == ["script", "voice", "talking_head", "broll", "assemble"]


def test_plan_local_is_free():
    spec = engine.parse("music video for s.mp3", use_llm=False)
    assert engine.plan(spec, None)["est_cost"] == 0.0


# ── execute (orchestration, mocked steps) ────────────────────────────────────
def test_execute_partial_when_only_script_runs(tmp_path):
    b = _brand(tmp_path)
    job = _job(engine.parse("30s short about grit", use_llm=False), b)
    done = engine.execute(job, b)   # real steps, all services offline
    assert done["status"] == "partial"
    assert done["step_status"]["script"] == "done"
    assert (tmp_path / "jobs" / job["id"] / "script.txt").exists()


def test_execute_done_with_output_when_mocked(tmp_path):
    b = _brand(tmp_path)
    job = _job(engine.parse("music video for s.mp3, neon", use_llm=False), b)

    def mk(note):
        def _f(j, s, br, ctx):
            if note == "clips":
                ctx["clips"] = ["/x/a.mp4"]
            if note == "ingest":
                ctx["song"] = {"beats": [0, 1]}; ctx["song_path"] = "/x/s.mp3"
            if note == "assemble":
                out = ctx["dir"] / "final.mp4"; out.write_text("v"); ctx["output"] = str(out)
            return note
        return _f
    hooks = {n: mk(n) for n in ("ingest", "clips", "assemble")}
    done = engine.execute(job, b, hooks=hooks)
    assert done["status"] == "done" and done["output"]
    assert engine.get_job(b, job["id"])["status"] == "done"


def test_execute_records_artifacts(tmp_path):
    b = _brand(tmp_path)
    job = _job(engine.parse("music video for s.mp3", use_llm=False), b)
    engine.execute(job, b)
    assert "artifacts" in engine.get_job(b, job["id"])


# ── rerender (editor) ────────────────────────────────────────────────────────
def test_rerender_reorders_and_reskins(tmp_path, monkeypatch):
    b = _brand(tmp_path)
    job = _job(engine.parse("music video for s.mp3, neon", use_llm=False), b)
    wd = engine._workdir(b, job["id"])
    song_json = wd / "song.json"; song_json.write_text(json.dumps({"beats": [0, 1, 2], "lyrics": []}))
    job["artifacts"] = {"clips": [str(wd / f"c{i}.mp4") for i in range(3)],
                        "song_json": str(song_json), "song_path": "/x/s.mp3",
                        "voice": None, "output": None}
    job["status"] = "done"; engine._save_job(b, job)

    seen = {}
    def fake_render(song, clips, audio, out, **kw):
        seen.update(clips=clips, cut=kw.get("cut"), look=kw.get("look"))
        Path(out).write_text("v"); return {"ok": True}
    monkeypatch.setattr(engine._mv, "render", fake_render)

    res = engine.rerender(b, job["id"], order=[2, 0], look=["cinematic"], cut="bars", every=2)
    assert res["ok"]
    assert seen["clips"][0].endswith("c2.mp4") and seen["clips"][1].endswith("c0.mp4")
    assert seen["cut"] == "bars" and seen["look"] == ["cinematic"]
    saved = engine.get_job(b, job["id"])
    assert saved["spec"]["looks"] == ["cinematic"] and saved["edits"][-1]["clips"] == 2


def test_rerender_rejects_non_music_job(tmp_path):
    b = _brand(tmp_path)
    job = _job(engine.parse("30s short about x", use_llm=False), b)
    engine._save_job(b, job)
    res = engine.rerender(b, job["id"], order=[0])
    assert res["ok"] is False


def test_rerender_missing_job(tmp_path):
    res = engine.rerender(_brand(tmp_path), "does-not-exist")
    assert res["ok"] is False and "not found" in res["error"]


# ── persistence ──────────────────────────────────────────────────────────────
def test_save_job_is_atomic_and_roundtrips(tmp_path):
    b = _brand(tmp_path)
    job = {"id": "abc", "ts": "t", "spec": {"kind": "short", "prompt": "p"},
           "plan": {"steps": []}, "status": "done", "step_status": {}}
    engine._save_job(b, job)
    assert engine.get_job(b, "abc")["status"] == "done"
    # no leftover temp files
    assert not list((tmp_path / "jobs").glob("*.tmp"))


def test_ingest_song_degrades_without_librosa(tmp_path):
    b = _brand(tmp_path)
    mp3 = tmp_path / "t.mp3"; mp3.write_bytes(b"x")
    res = engine.ingest_song(b, str(mp3))
    # librosa absent in CI → graceful failure with a hint, never an exception
    if not res["ok"]:
        assert res.get("hint")
