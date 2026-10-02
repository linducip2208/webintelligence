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

func TestAdversarial(t *testing.T) {
	bad := []string{
		"http://2130706433/",         // decimal 127.0.0.1
		"http://0x7f000001/",         // hex
		"http://017700000001/",       // octal
		"http://0x7f.0.0.1/",         // dotted hex
		"http://[::ffff:127.0.0.1]/", // mapped v6
		"http://[::1]/",
		"http://0.0.0.0/",
		"http://100.100.100.200/", // alibaba metadata
		"http://example.com@127.0.0.1/",
		"http://127.1/",
	}
	for _, u := range bad {
		if err := ValidateURL(u, nil); err == nil {
			t.Fatalf("expected block for %s", u)
		}
	}
	if err := ValidateURL("http://nonexistent.invalid/", nil); err == nil {
		t.Fatal("expected dns failure")
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
