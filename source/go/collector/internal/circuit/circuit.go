// Package circuit implements a per-host circuit breaker.
package circuit

import (
	"sync"
	"time"
)

type Breaker struct {
	mu        sync.Mutex
	threshold int
	cooldown  time.Duration
	fails     map[string]int
	openedAt  map[string]time.Time
}

func New(threshold int, cooldown time.Duration) *Breaker {
	return &Breaker{threshold: threshold, cooldown: cooldown, fails: map[string]int{}, openedAt: map[string]time.Time{}}
}

func (b *Breaker) Allow(host string) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.fails[host] >= b.threshold {
		if time.Since(b.openedAt[host]) < b.cooldown {
			return false
		}
		delete(b.fails, host)
	}
	return true
}

func (b *Breaker) Record(host string, ok bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if ok {
		delete(b.fails, host)
		return
	}
	b.fails[host]++
	if b.fails[host] >= b.threshold {
		b.openedAt[host] = time.Now()
	}
}
