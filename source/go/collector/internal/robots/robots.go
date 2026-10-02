// Package robots enforces robots.txt Disallow rules when enabled
// (ROBOTS_ENFORCE=1). Default off: policy-driven, cached per host.
package robots

import (
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

var mu sync.Mutex
var cache = map[string][]string{}
var fetched = map[string]time.Time{}

func rulesFor(host string, client *http.Client) []string {
	mu.Lock()
	if time.Since(fetched[host]) < time.Hour {
		r := cache[host]
		mu.Unlock()
		return r
	}
	mu.Unlock()
	u := "http://" + host + "/robots.txt"
	resp, err := client.Get(u)
	var out []string
	if err == nil {
		defer resp.Body.Close()
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 100<<10))
		inScope := true
		for _, line := range strings.Split(string(b), "\n") {
			line = strings.TrimSpace(line)
			if strings.HasPrefix(strings.ToLower(line), "user-agent:") {
				ua := strings.TrimSpace(line[11:])
				inScope = ua == "*" || strings.Contains(strings.ToLower("webintel"), strings.ToLower(ua))
			} else if inScope && strings.HasPrefix(strings.ToLower(line), "disallow:") {
				p := strings.TrimSpace(line[9:])
				if p != "" {
					out = append(out, p)
				}
			}
		}
	}
	mu.Lock()
	cache[host] = out
	fetched[host] = time.Now()
	mu.Unlock()
	return out
}

// Allowed reports whether path may be fetched under robots policy.
func Allowed(rawURL string, client *http.Client) bool {
	u, err := url.Parse(rawURL)
	if err != nil || u.Host == "" {
		return false
	}
	for _, d := range rulesFor(u.Host, client) {
		if strings.HasPrefix(u.Path, d) {
			return false
		}
	}
	return true
}
