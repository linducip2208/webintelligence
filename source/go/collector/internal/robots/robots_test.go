package robots

import (
 "net/http"
 "net/http/httptest"
 "testing"
)

func TestDisallow(t *testing.T) {
 srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
  if r.URL.Path == "/robots.txt" {
   w.Write([]byte("User-agent: *\nDisallow: /private\n"))
   return
  }
  w.Write([]byte("ok"))
 }))
 defer srv.Close()
 if !Allowed(srv.URL+"/public", srv.Client()) {
  t.Fatal("public should be allowed")
 }
 if Allowed(srv.URL+"/private/x", srv.Client()) {
  t.Fatal("private should be disallowed")
 }
}
