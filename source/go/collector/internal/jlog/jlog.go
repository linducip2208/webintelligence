// Package jlog emits structured JSON log lines with correlation fields.
package jlog

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

func Log(event string, fields map[string]any) {
	rec := map[string]any{"ts": time.Now().UTC().Format(time.RFC3339), "event": event}
	for k, v := range fields {
		rec[k] = v
	}
	b, _ := json.Marshal(rec)
	fmt.Fprintln(os.Stderr, string(b))
}
