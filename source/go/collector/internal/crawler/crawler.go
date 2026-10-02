// Package crawler runs the worker pool: queue -> collect -> results.
package crawler

import (
 "context"
 "sync"
 "time"

 "webintel-collector/internal/collector"
 "webintel-collector/internal/circuit"
 "webintel-collector/internal/config"
 "webintel-collector/internal/httpclient"
 "webintel-collector/internal/jlog"
 "webintel-collector/internal/metrics"
 "webintel-collector/internal/proxy"
 "webintel-collector/internal/queue"
 "webintel-collector/internal/ratelimit"
 "webintel-collector/internal/reporter"
 "webintel-collector/pkg/protocol"
)

func Run(ctx context.Context, cfg config.Config, q *queue.Queue, out chan protocol.Result) {
 client := httpclient.New(cfg.TimeoutMs, cfg.MaxBody)
 if cfg.UserAgent != "" {
  client.UA = cfg.UserAgent
 }
 lim := ratelimit.New(20, time.Minute)
 cb := circuit.New(5, time.Minute)
 var etags sync.Map // url -> map[string]string{etag,lastmod}
 var px proxy.Provider = proxy.NewOwn(cfg.OwnProxies)
 rep := reporter.New(cfg.APIBase, cfg.APIToken)
 var wg sync.WaitGroup
 for i := 0; i < cfg.Workers; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for {
    select {
    case <-ctx.Done():
     return
    default:
    }
    job, ok := q.Pop(2)
    if !ok {
     time.Sleep(200 * time.Millisecond)
     continue
    }
    pj := protocol.Job{
     SchemaVersion: "1.0",
     JobID:         str(job, "job_id"),
     TargetID:      str(job, "target_id"),
     URL:           str(job, "url"),
     Strategy:      str(job, "strategy"),
     Region:        str(job, "region"),
    }
    cond := map[string]string{}
    if v, ok := etags.Load(pj.URL); ok {
     if m, ok := v.(map[string]string); ok {
      cond["If-None-Match"] = m["etag"]
      cond["If-Modified-Since"] = m["lastmod"]
     }
    }
    host := pj.URL
    if !cb.Allow(host) {
     metrics.Inc("circuit_skipped", 1)
     time.Sleep(200 * time.Millisecond)
     continue
    }
    r := collector.CollectWith(client, lim, px, pj, cond)
    if r.ETag != "" || r.LastModified != "" {
     etags.Store(pj.URL, map[string]string{"etag": r.ETag, "lastmod": r.LastModified})
    }
    cb.Record(host, r.Status == "success")
    jlog.Log("job_finished", map[string]any{"job_id": pj.JobID, "status": r.Status,
     "strategy": r.Strategy, "http": r.HTTPStatus})
    metrics.Inc("jobs_total", 1)
    if r.Status == "success" {
     metrics.Inc("jobs_success", 1)
    } else {
     metrics.Inc("jobs_failed", 1)
    }
    if err := rep.Send(r); err != nil {
     metrics.Inc("reporter_failed", 1)
    } else {
     metrics.Inc("reporter_sent", 1)
    }
    select {
    case out <- r:
    case <-ctx.Done():
     return
    }
   }
  }()
 }
 wg.Wait()
}

func str(m map[string]any, k string) string {
 v, _ := m[k].(string)
 return v
}
