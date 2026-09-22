#!/usr/bin/env python3
"""tau_direct.py -- submit the tau dose-response circuits to Quantum Inspire.

Pure REST through the generated compute_api_client. No CLI, no subprocess, no
asyncio.run() inside an event loop. Call sequence mirrors the official client
(qiskit_quantuminspire/qi_jobs.py::QIJob._submit_async):

    LanguagesApi.read_languages            -> cqasm 3.0 language id
    ProjectsApi.create_project             -> project
    BatchJobsApi.create_batch_job          -> batch job (<=5 jobs each)
    per circuit: AlgorithmsApi -> CommitsApi -> FilesApi -> JobsApi
    BatchJobsApi.enqueue_batch_job
    JobsApi.read_job  /  ResultsApi.read_results_by_job_id

Rolling window keeps at most batchjobs_per_queue_limit (5) batch jobs in flight.
"""
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime, timezone

from compute_api_client import (
    AlgorithmIn, AlgorithmsApi, AlgorithmType, ApiClient, BatchJobIn, BatchJobsApi,
    CommitIn, CommitsApi, CompileStage, FileIn, FilesApi, JobIn, JobsApi, JobStatus,
    LanguagesApi, ProjectIn, ProjectsApi, ResultsApi, ShareType,
)
from qi2_shared.client import config
from qi2_shared.settings import ApiSettings

ROOT = os.path.dirname(os.path.abspath(__file__))
TAU_DIR = os.environ.get("TAU_DIR", "cqasm_tau")
MANIFEST = os.path.join(ROOT, TAU_DIR, "manifest.json")
OUTDIR = os.path.join(ROOT, os.environ.get("TAU_OUTDIR", "results/tau"))
QUEUE = os.path.join(OUTDIR, "queue.json")
LOG = os.path.join(ROOT, os.environ.get("TAU_LOG", "tau_direct.log"))
PROJECT_NAME = os.environ.get("TAU_PROJECT", "qbn-tau-dose-response")

SHOTS = int(os.environ.get("TAU_SHOTS", "65536"))
BACKEND_TYPE_ID = 7          # Tuna-17
CHUNK = 5                    # backend_type.max_jobs_per_batch_job
MAX_INFLIGHT = 5             # backend_type.batchjobs_per_queue_limit
POLL_S = 20
MAX_ATTEMPTS = 3
LIMIT = int(os.environ.get("TAU_LIMIT", "0"))   # 0 = all; >0 = smoke test

TERMINAL = (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED)


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = "[%sZ] %s" % (ts, msg)
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def result_path(e):
    return os.path.join(OUTDIR, "%s__k%02d.json" % (e["tag"], e["k"]))


def save_queue(batches):
    snap = []
    for rec in batches:
        snap.append({
            "batch_job_id": rec["bj"],
            "jobs": [{"job_id": j, "tag": e["tag"], "k": e["k"]}
                     for j, e in rec["job_ids"].items()],
        })
    tmp = QUEUE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(snap, fh, indent=1)
    os.replace(tmp, QUEUE)


async def find_language(api_client, name, version):
    api = LanguagesApi(api_client)
    for pageno in range(1, 6):
        page = await api.read_languages_languages_get(page=pageno, size=100)
        items = getattr(page, "items", None) or []
        for lan in items:
            if lan.name.lower() == name.lower() and lan.version == version:
                return lan
        if not items:
            break
    return None


async def collect(api_client, jid, e, st):
    page = await ResultsApi(api_client).read_results_by_job_id_results_job_job_id_get(job_id=jid)
    items = getattr(page, "items", None) or []
    if not items:
        log("job %d %s/k%d COMPLETED but no result row" % (jid, e["tag"], e["k"]))
        return False
    r = items[0]
    counts = r.results or {}
    out = {
        "tag": e["tag"], "k": e["k"], "job_id": jid, "tau": e["tau"],
        "shots": SHOTS, "status": str(st), "exec_s": r.execution_time_in_seconds,
        "shots_done": r.shots_done, "n_keys": len(counts), "counts": counts,
    }
    tmp = result_path(e) + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh, indent=1)
    os.replace(tmp, result_path(e))
    log("SAVED %s/k%d shots_done=%d keys=%d exec=%.1fs"
        % (e["tag"], e["k"], r.shots_done, len(counts), r.execution_time_in_seconds or 0.0))
    return r.shots_done == SHOTS


async def main():
    entries = json.load(open(MANIFEST))
    missing = [e for e in entries if not os.path.exists(result_path(e))]
    todo = missing[:LIMIT] if LIMIT else list(missing)
    log("manifest=%d done=%d todo=%d shots=%d" % (len(entries), len(entries) - len(missing), len(todo), SHOTS))
    if not todo:
        log("nothing to do")
        return 0

    settings = ApiSettings.from_config_file()
    owner_id = settings.auths[settings.default_host].team_member_id

    async with ApiClient(config()) as api_client:
        language = await find_language(api_client, "cqasm", "3.0")
        if language is None:
            log("FATAL: no cqasm 3.0 language on the platform")
            return 1
        log("language cqasm %s id=%s owner=%s" % (language.version, language.id, owner_id))

        project = await ProjectsApi(api_client).create_project_projects_post(
            ProjectIn(owner_id=owner_id, name=PROJECT_NAME,
                      description="QBN tau dose-response, Tuna-17", starred=False))
        log("project id=%s" % project.id)

        batches = []
        pending = list(todo)
        retry = []
        attempt = {}

        async def make_batch(chunk):
            bj = await BatchJobsApi(api_client).create_batch_job_batch_jobs_post(
                BatchJobIn(backend_type_id=BACKEND_TYPE_ID))
            rec = {"bj": bj.id, "job_ids": {}}
            for e in chunk:
                nm = "%s_k%02d" % (e["tag"], e["k"])
                alg = await AlgorithmsApi(api_client).create_algorithm_algorithms_post(
                    AlgorithmIn(project_id=project.id, type=AlgorithmType.QUANTUM,
                                shared=ShareType.PRIVATE, name=nm))
                cm = await CommitsApi(api_client).create_commit_commits_post(
                    CommitIn(description=nm, algorithm_id=alg.id))
                content = open(os.path.join(ROOT, e["path"])).read()
                fl = await FilesApi(api_client).create_file_files_post(
                    FileIn(commit_id=cm.id, content=content, language_id=language.id,
                           compile_stage=CompileStage.NONE, compile_properties={}, name=nm))
                jb = await JobsApi(api_client).create_job_jobs_post(
                    JobIn(file_id=fl.id, batch_job_id=bj.id, number_of_shots=SHOTS,
                          raw_data_enabled=False))
                rec["job_ids"][jb.id] = e
                e["job_id"] = jb.id
                e["done"] = False
                log("  job %d <- %s" % (jb.id, nm))
            await BatchJobsApi(api_client).enqueue_batch_job_batch_jobs_id_enqueue_patch(bj.id)
            log("batch %d enqueued (%d jobs)" % (bj.id, len(chunk)))
            batches.append(rec)
            save_queue(batches)

        while pending or batches or retry:
            if not pending and not batches and retry:
                nxt = [e for e in retry if attempt.get((e["tag"], e["k"]), 0) < MAX_ATTEMPTS]
                if not nxt:
                    break
                log("retrying %d circuit(s)" % len(nxt))
                pending.extend(nxt)
                retry = []

            while len(batches) < MAX_INFLIGHT and pending:
                chunk = [pending.pop(0) for _ in range(min(CHUNK, len(pending)))]
                try:
                    await make_batch(chunk)
                except Exception as exc:
                    log("submit failed (%s); returning %d circuit(s) to pending" % (exc, len(chunk)))
                    for e in chunk:
                        k = (e["tag"], e["k"])
                        attempt[k] = attempt.get(k, 0) + 1
                        e.pop("job_id", None)
                    pending[0:0] = chunk
                    await asyncio.sleep(POLL_S)
                    break

            for rec in list(batches):
                all_done = True
                for jid, e in list(rec["job_ids"].items()):
                    if e.get("done"):
                        continue
                    try:
                        j = await JobsApi(api_client).read_job_jobs_id_get(id=jid)
                    except Exception as exc:
                        log("status read failed for %d: %s" % (jid, exc))
                        all_done = False
                        continue
                    st = j.status
                    if st not in TERMINAL:
                        all_done = False
                        continue
                    e["done"] = True
                    if st == JobStatus.COMPLETED:
                        try:
                            if not await collect(api_client, jid, e, st):
                                retry.append(e)
                        except Exception as exc:
                            log("collect failed for %d: %s" % (jid, exc))
                            retry.append(e)
                    else:
                        log("job %d %s/k%d -> %s msg=%s"
                            % (jid, e["tag"], e["k"], st, getattr(j, "message", None)))
                        k = (e["tag"], e["k"])
                        attempt[k] = attempt.get(k, 0) + 1
                        retry.append(e)
                if all_done:
                    batches.remove(rec)
                    save_queue(batches)

            if pending or batches or retry:
                await asyncio.sleep(POLL_S)

    done = [e for e in entries if os.path.exists(result_path(e))]
    log("FINISHED %d/%d" % (len(done), len(entries)))
    missing = [e for e in entries if not os.path.exists(result_path(e))]
    for e in missing:
        log("MISSING %s/k%d" % (e["tag"], e["k"]))
    return 0 if not missing else 2


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception:
        traceback.print_exc()
        rc = 1
    sys.exit(rc)