import json, pathlib
from qi2_shared.client import config
from qi2_shared.utils import run_async
from compute_api_client import ApiClient
from compute_api_client.api.batch_jobs_api import BatchJobsApi
from compute_api_client.api.jobs_api import JobsApi
from compute_api_client.api.results_api import ResultsApi

OUT = pathlib.Path("/home/b02/qi/results")
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    async with ApiClient(config()) as client:
        bj = BatchJobsApi(client); ja = JobsApi(client); ra = ResultsApi(client)
        page = await bj.read_batch_jobs_batch_jobs_get()
        items = getattr(page, "items", page)
        print("batch jobs:", len(items))
        rows = []
        for b in items:
            bd = b.to_dict() if hasattr(b, "to_dict") else vars(b)
            for jid in (bd.get("job_ids") or []):
                row = dict(batch=bd.get("id"), backend_type=bd.get("backend_type_id"), job=jid)
                try:
                    j = await ja.read_job_jobs_id_get(id=jid)
                    jd = j.to_dict() if hasattr(j, "to_dict") else vars(j)
                    row.update(status=str(jd.get("status")), shots=jd.get("number_of_shots"),
                               created=str(jd.get("created_on")), finished=str(jd.get("finished_at")),
                               msg=str(jd.get("message")), file_id=jd.get("file_id"))
                    rp = await ra.read_results_by_job_id_results_job_job_id_get(job_id=jid)
                    ri = getattr(rp, "items", rp)
                    if ri:
                        rd = ri[0].to_dict() if hasattr(ri[0], "to_dict") else vars(ri[0])
                        row["counts"] = rd.get("results")
                        row["exec_time"] = rd.get("execution_time_in_seconds")
                        row["shots_done"] = rd.get("shots_done")
                    else:
                        row["counts"] = None
                except Exception as e:
                    row["error"] = "%s: %s" % (type(e).__name__, str(e)[:80])
                rows.append(row)
        (OUT / "recovered.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        ok = [r for r in rows if r.get("counts")]
        print("有結果的 job:", len(ok), "/", len(rows))
        for r in rows[:50]:
            print("  batch=%-7s bt=%s job=%-8s %-10s shots=%-6s keys=%-4s exec=%s" % (
                r.get("batch"), r.get("backend_type"), r.get("job"), str(r.get("status")),
                r.get("shots"), (len(r["counts"]) if r.get("counts") else 0), r.get("exec_time")))

run_async(main())
