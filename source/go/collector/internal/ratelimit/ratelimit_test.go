package ratelimit

import (
	"testing"
	"time"
)

func TestAllow(t *testing.T) {
	l := New(2, time.Minute)
	if !l.Allow("h") || !l.Allow("h") || l.Allow("h") {
		t.Fatal("bucket failed")
	}
}
