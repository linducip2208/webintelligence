package parser

import "testing"

var benchBody = []byte("<html><head><title>T</title></head><body><p>price $19.99 only today</p></body></html>")

func BenchmarkCheck(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Check("text/html", benchBody, []string{"price"})
	}
}
