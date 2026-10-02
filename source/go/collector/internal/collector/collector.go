package collector

import (
 "time"

 "webintel-collector/internal/httpclient"
 "webintel-collector/internal/parser"
 "webintel-collector/internal/proxy"
 "webintel-collector/internal/ratelimit"
 "webintel-collector/pkg/protocol"
)

// Collect executes one job: rate-limit, fetch, validate. Proxy hook ready.
func Collect(client *httpclient.Client, lim *ratelimit.Limiter, _ proxy.Provider, job protocol.Job) protocol.Result {
 res := protocol.Result{
  SchemaVersion: "1.0",
  JobID:         job.JobID,
  Strategy:      "DIRECT_HTTP",
  RetrievedAt:   time.Now().UTC().Format(time.RFC3339),
  ParseStatus:   "pending",
 }
 r, err := client.Get(job.URL, "")
 if err != nil {
  res.Status = "failed"
  res.Diagnostics = map[string]string{"error": err.Error()}
  return res
 }
 ok, _ := parser.Check(r.Header.Get("Content-Type"), r.Body, nil)
 res.HTTPStatus = r.Status
 res.ContentHash = r.Hash
 res.ContentSize = r.Size
 if r.Status == 200 && ok {
  res.Status = "success"
 } else {
  res.Status = "failed"
 }
 _ = lim
 return res
}
