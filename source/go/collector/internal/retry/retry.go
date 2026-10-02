package retry

import (
	"math/rand"
	"time"
)

func Backoff(attempt int, base time.Duration, cap time.Duration) time.Duration {
	d := base * time.Duration(1<<attempt)
	if d > cap {
		d = cap
	}
	return d + time.Duration(rand.Int63n(int64(base)))
}
