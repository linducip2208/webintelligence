// Package crawler runs the worker pool: queue -> collect -> results.
package crawler

import (
 "context"
 "sync"
 "time"

 "webintel-collector/internal/collector"
 "webintel-collector/internal/config"
 "webintel-collector/internal/httpclient"
 "webintel-collector/internal/metrics"
 "webintel-collector/internal/proxy"
 "webintel-collector/internal/queue"
 "webintel-collector/internal/ratelimit"
 "webintel-collector/internal/reporter"
 "webintel-collector/pkg/protocol"
)

func Run(ctx context.Context, cfg config.Config, q *queue.Queue, out chan protocol.Result) {
 client := httpclient.New(cfg.TimeoutMs, cfg.MaxBody)
 lim := ratelimit.New(20, time.Minute)
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
    r := collector.Collect(client, lim, px, pj)
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
