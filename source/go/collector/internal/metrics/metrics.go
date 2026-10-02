package metrics

import (
	"fmt"
	"sync"
)

var mu sync.Mutex
var reg = map[string]float64{}

func Inc(name string, v float64) {
	mu.Lock()
	reg[name] += v
	mu.Unlock()
}

func Render() string {
	mu.Lock()
	defer mu.Unlock()
	out := ""
	for k, v := range reg {
		out += fmt.Sprintf("# TYPE %s gauge\n%s %v\n", k, k, v)
	}
	return out
}
