// Package protocol defines versioned Go/Python contracts.
package protocol

// Job is the Redis queue payload (contracts/jobs/job.json).
type Job struct {
 SchemaVersion string `json:"schema_version"`
 JobID         string `json:"job_id"`
 TargetID      string `json:"target_id"`
 URL           string `json:"url"`
 Strategy      string `json:"strategy"`
 Region        string `json:"region"`
 TimeoutMs     int    `json:"timeout_ms"`
}

// Result is the completion payload (contracts/results/result.json).
type Result struct {
 SchemaVersion string `json:"schema_version"`
 JobID         string `json:"job_id"`
 Status        string `json:"status"`
 Strategy      string `json:"strategy"`
 HTTPStatus    int    `json:"http_status"`
 ContentHash   string `json:"content_hash"`
 ContentSize   int    `json:"content_size"`
 RetrievedAt   string `json:"retrieved_at"`
 ParseStatus   string `json:"parse_status"`
 Diagnostics   map[string]string `json:"diagnostics,omitempty"`
}