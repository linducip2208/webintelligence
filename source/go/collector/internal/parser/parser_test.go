package parser

import "testing"

func TestCheck(t *testing.T) {
	ok, c := Check("text/html", []byte("<html>price $10</html>"), []string{"price"})
	if !ok || c != 1.0 {
		t.Fatalf("got %v %v", ok, c)
	}
	ok2, _ := Check("application/octet-stream", []byte("x"), nil)
	if ok2 {
		t.Fatal("bad content-type must fail")
	}
}
