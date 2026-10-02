package circuit

import (
	"testing"
	"time"
)

func TestOpenClose(t *testing.T) {
	b := New(2, 50*time.Millisecond)
	if !b.Allow("h") {
		t.Fatal("should allow")
	}
	b.Record("h", false)
	b.Record("h", false)
	if b.Allow("h") {
		t.Fatal("should be open")
	}
	time.Sleep(60 * time.Millisecond)
	if !b.Allow("h") {
		t.Fatal("should half-open after cooldown")
	}
	b.Record("h", true)
	if !b.Allow("h") {
		t.Fatal("should be closed")
	}
}
