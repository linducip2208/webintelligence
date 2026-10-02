package strategy

import "testing"

func TestDecideEscalation(t *testing.T) {
 p := Decide(false, false, true, false, false, true, true, true, true, nil)
 if p[0] != "DIRECT_HTTP" {
  t.Fatal(p)
 }
 hasProxy, hasBD := false, false
 for _, s := range p {
  if s == "OWN_PROXY" {
   hasProxy = true
  }
  if s == "BRIGHT_DATA" {
   hasBD = true
  }
 }
 if !hasProxy || !hasBD {
  t.Fatalf("expected escalation, got %v", p)
 }
}

func TestValidate200NotAutoSuccess(t *testing.T) {
 ok, _ := Validate(200, "text/html", 100, true, 0.9)
 if !ok {
  t.Fatal("should pass")
 }
 ok2, _ := Validate(200, "text/html", 100, true, 0.1)
 if ok2 {
  t.Fatal("200 with incomplete data must fail")
 }
}
