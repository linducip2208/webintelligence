package proxy

import "testing"

func TestOwnRotation(t *testing.T) {
	o := NewOwn([]string{"http://a:1", "http://b:2"})
	if o.GetProxy("") == "" {
		t.Fatal("expected proxy")
	}
	if !o.Healthy() {
		t.Fatal("expected healthy")
	}
}

func TestBrightNeedsCreds(t *testing.T) {
	b := &BrightData{}
	if b.Healthy() || b.GetProxy("") != "" {
		t.Fatal("unconfigured must be empty")
	}
}
