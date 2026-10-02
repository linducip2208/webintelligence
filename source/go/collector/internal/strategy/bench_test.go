package strategy

import "testing"

func BenchmarkDecide(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Decide(false, false, true, false, false, true, true, true, true,
			map[string]int{"DIRECT_HTTP": 9, "OWN_PROXY": 2})
	}
}
