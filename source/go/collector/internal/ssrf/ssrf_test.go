package ssrf

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestBlocks(t *testing.T) {
	bad := []string{
		"http://localhost/x",
		"http://127.0.0.1/",
		"http://10.0.0.5/",
		"http://192.168.1.1/",
		"http://169.254.169.254/latest/",
		"ftp://example.com/x",
		"http://[::1]/",
	}
	for _, u := range bad {
		if err := ValidateURL(u, nil); err == nil {
			t.Fatalf("expected block for %s", u)
		}
	}
}

func TestTrustAllowlist(t *testing.T) {
	if err := ValidateURL("http://127.0.0.1:9/x", []string{"127.0.0.1/32"}); err != nil {
		t.Fatalf("allowlisted should pass: %v", err)
	}
}

func TestPublicOK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	}))
	defer srv.Close()
	// httptest binds 127.0.0.1 -> blocked unless trusted
	if err := ValidateURL(srv.URL, nil); err == nil {
		t.Fatal("loopback test server must be blocked without trust")
	}
	if err := ValidateURL(srv.URL, []string{"127.0.0.0/8"}); err != nil {
		t.Fatalf("trusted range should pass: %v", err)
	}
	if !strings.HasPrefix(srv.URL, "http") {
		t.Fatal("unexpected scheme")
	}
}
