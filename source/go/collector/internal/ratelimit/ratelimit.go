package ratelimit

import (
 "sync"
 "time"
)

// Token bucket per host.
type Limiter struct {
 mu     sync.Mutex
 tokens map[string]int
 max    int
 window time.Duration
 reset  time.Time
}

func New(max int, window time.Duration) *Limiter {
 return &Limiter{tokens: map[string]int{}, max: max, window: window, reset: time.Now().Add(window)}
}

func (l *Limiter) Allow(host string) bool {
 l.mu.Lock()
 defer l.mu.Unlock()
 if time.Now().After(l.reset) {
  l.tokens = map[string]int{}
  l.reset = time.Now().Add(l.window)
 }
 if l.tokens[host] >= l.max {
  return false
 }
 l.tokens[host]++
 return true
}
