package reporter

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"webintel-collector/pkg/protocol"
)

func TestSendOK(t *testing.T) {
	var got protocol.Result
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/results" {
			t.Errorf("bad path %s", r.URL.Path)
		}
		_ = json.NewDecoder(r.Body).Decode(&got)
		w.WriteHeader(200)
	}))
	defer srv.Close()
	rep := New(srv.URL, "")
	err := rep.Send(protocol.Result{SchemaVersion: "1.0", JobID: "j1", Status: "success"})
	if err != nil {
		t.Fatal(err)
	}
	if got.JobID != "j1" {
		t.Fatalf("got %+v", got)
	}
}

func TestSendFailStatus(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
	}))
	defer srv.Close()
	rep := New(srv.URL, "")
	if err := rep.Send(protocol.Result{JobID: "x"}); err == nil {
		t.Fatal("expected error on 404")
	}
}
