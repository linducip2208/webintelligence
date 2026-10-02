// Full chain test with REAL local HTTP: page server -> queue -> crawler ->
// reporter -> API server. No mocks of the units under test.
package crawler

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"webintel-collector/internal/config"
	"webintel-collector/internal/queue"
	"webintel-collector/pkg/protocol"
)

func TestFullChain(t *testing.T) {
	t.Setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.0/8")
	page := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/p" {
			w.Header().Set("Content-Type", "text/html")
			w.Header().Set("ETag", `"v1"`)
			w.Write([]byte("<html><body>price $29.99</body></html>"))
			return
		}
		w.WriteHeader(404)
	}))
	defer page.Close()

	var got protocol.Result
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/results" {
			w.WriteHeader(404)
			return
		}
		_ = json.NewDecoder(r.Body).Decode(&got)
		w.WriteHeader(200)
	}))
	defer api.Close()

	cfg := config.Load()
	cfg.Workers = 2
	cfg.APIBase = api.URL
	q := queue.New("127.0.0.1:9", cfg.Queue) // nothing here: in-memory fallback
	if err := q.Push(queue.Job{"schema_version": "1.0", "job_id": "e2e-1",
		"target_id": "1", "url": page.URL + "/p", "strategy": "DIRECT_HTTP",
		"timeout_ms": 10000}); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	out := make(chan protocol.Result, 8)
	done := make(chan struct{})
	go func() { Run(ctx, cfg, q, out); close(done) }()
	select {
	case r := <-out:
		if r.Status != "success" || r.HTTPStatus != 200 || r.ContentSize == 0 || r.ContentHash == "" {
			t.Fatalf("bad result %+v", r)
		}
		if r.ETag != `"v1"` {
			t.Fatalf("missing etag %+v", r)
		}
	case <-time.After(7 * time.Second):
		t.Fatal("no result consumed")
	}
	cancel()
	<-done
	if got.JobID != "e2e-1" || got.ContentHash == "" {
		t.Fatalf("reporter did not deliver %+v", got)
	}
}
