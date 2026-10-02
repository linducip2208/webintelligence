// Package reporter POSTs result bundles back to the Python API
// (POST /api/v1/results, contracts/results/result.json). Stdlib only.
package reporter

import (
	"bytes"
	"encoding/json"
	"net/http"
	"time"

	"webintel-collector/pkg/protocol"
)

type Reporter struct {
	API   string
	Token string
	http  *http.Client
}

func New(api, token string) *Reporter {
	return &Reporter{API: api, Token: token, http: &http.Client{Timeout: 15 * time.Second}}
}

func (r *Reporter) Send(res protocol.Result) error {
	b, _ := json.Marshal(res)
	req, err := http.NewRequest("POST", r.API+"/api/v1/results", bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if r.Token != "" {
		req.Header.Set("Authorization", "Bearer "+r.Token)
	}
	resp, err := r.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return &httpError{resp.StatusCode}
	}
	return nil
}

type httpError struct{ code int }

func (e *httpError) Error() string { return "api status " + itoa(e.code) }

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	s := ""
	for n > 0 {
		s = string(rune('0'+n%10)) + s
		n /= 10
	}
	return s
}
