package collector

import (
 "time"

 "webintel-collector/internal/httpclient"
 "webintel-collector/internal/parser"
 "webintel-collector/internal/proxy"
 "webintel-collector/internal/ratelimit"
 "webintel-collector/pkg/protocol"
)

// Collect executes one job: rate-limit, fetch (via proxy provider when the
// strategy calls for it), validate. Proxy hook ready.
func Collect(client *httpclient.Client, lim *ratelimit.Limiter, px proxy.Provider, job protocol.Job) protocol.Result {
 res := protocol.Result{
  SchemaVersion: "1.0",
  JobID:         job.JobID,
  Strategy:      "DIRECT_HTTP",
  RetrievedAt:   time.Now().UTC().Format(time.RFC3339),
  ParseStatus:   "pending",
 }
 proxyURL := ""
 if (job.Strategy == "OWN_PROXY" || job.Strategy == "BRIGHT_DATA") && px != nil {
  proxyURL = px.GetProxy(job.Region)
  res.Strategy = job.Strategy
  defer px.ReleaseProxy(proxyURL, true)
 }
 r, err := client.Get(job.URL, proxyURL)
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
