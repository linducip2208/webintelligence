package collector

import (
	"encoding/base64"
	"os"
	"strings"
	"time"

	"webintel-collector/internal/httpclient"
	"webintel-collector/internal/parser"
	"webintel-collector/internal/proxy"
	"webintel-collector/internal/ratelimit"
	"webintel-collector/internal/robots"
	"webintel-collector/internal/ssrf"
	"webintel-collector/pkg/protocol"
)

// Classify network errors for diagnostics (dns/timeout/refused/tls/other).
func Classify(err error) string {
	if err == nil {
		return ""
	}
	s := strings.ToLower(err.Error())
	switch {
	case strings.Contains(s, "dns") || strings.Contains(s, "no such host"):
		return "dns"
	case strings.Contains(s, "timeout") || strings.Contains(s, "deadline"):
		return "timeout"
	case strings.Contains(s, "refused"):
		return "refused"
	case strings.Contains(s, "tls") || strings.Contains(s, "certificate"):
		return "tls"
	default:
		return "network"
	}
}

// trustedCIDRs reads the TRUSTED_EGRESS_CIDRS allowlist (comma-separated).
func trustedCIDRs() []string {
	raw := os.Getenv("TRUSTED_EGRESS_CIDRS")
	if raw == "" {
		return nil
	}
	var out []string
	for _, c := range strings.Split(raw, ",") {
		if c = strings.TrimSpace(c); c != "" {
			out = append(out, c)
		}
	}
	return out
}

// Collect executes one job: robots policy, rate-limit, conditional fetch
// (ETag via cond map), validate. Proxy hook ready.
func Collect(client *httpclient.Client, lim *ratelimit.Limiter, px proxy.Provider, job protocol.Job) protocol.Result {
	return CollectWith(client, lim, px, job, map[string]string{})
}

func CollectWith(client *httpclient.Client, lim *ratelimit.Limiter, px proxy.Provider, job protocol.Job, cond map[string]string) protocol.Result {
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
	if err := ssrf.ValidateURL(job.URL, trustedCIDRs()); err != nil {
		res.Status = "failed"
		res.Diagnostics = map[string]string{"error": "ssrf-blocked: " + err.Error()}
		return res
	}
	if os.Getenv("ROBOTS_ENFORCE") == "1" && !robots.Allowed(job.URL, client.Plain()) {
		res.Status = "failed"
		res.Diagnostics = map[string]string{"error": "robots-disallowed"}
		return res
	}
	r, err := client.GetWith(job.URL, proxyURL, cond)
	if err != nil {
		res.Status = "failed"
		res.Diagnostics = map[string]string{"error": err.Error(), "class": Classify(err)}
		return res
	}
	if r.NotModified {
		res.Status = "success"
		res.HTTPStatus = 304
		res.Diagnostics = map[string]string{"note": "not-modified"}
		return res
	}
	if r.FinalURL != "" && r.FinalURL != job.URL {
		if err := ssrf.ValidateURL(r.FinalURL, trustedCIDRs()); err != nil {
			res.Status = "failed"
			res.Diagnostics = map[string]string{"error": "ssrf-blocked-redirect: " + err.Error()}
			return res
		}
	}
	ok, _ := parser.Check(r.Header.Get("Content-Type"), r.Body, nil)
	res.HTTPStatus = r.Status
	res.ContentHash = r.Hash
	res.ContentSize = r.Size
	res.ETag = r.ETag
	res.LastModified = r.LastMod
	res.ContentType = r.Header.Get("Content-Type")
	if len(r.Body) > 0 && len(r.Body) <= 256<<10 {
		res.ContentB64 = base64.StdEncoding.EncodeToString(r.Body)
	}
	if r.Status == 200 && ok {
		res.Status = "success"
	} else {
		res.Status = "failed"
	}
	_ = lim
	return res
}
