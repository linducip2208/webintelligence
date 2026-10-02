// Command collector: high-concurrency HTTP collection service.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"webintel-collector/internal/config"
	"webintel-collector/internal/crawler"
	"webintel-collector/internal/metrics"
	"webintel-collector/internal/queue"
	"webintel-collector/pkg/protocol"
)

func main() {
	cfg := config.Load()
	q := queue.New(cfg.RedisAddr, cfg.Queue)
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	out := make(chan protocol.Result, 1024)
	go func() {
		for r := range out {
			b, _ := json.Marshal(r)
			fmt.Println(string(b))
		}
	}()
	fmt.Fprintf(os.Stderr, "webintel-collector workers=%d queue=%s redis=%s\n", cfg.Workers, cfg.Queue, cfg.RedisAddr)
	crawler.Run(ctx, cfg, q, out)
	fmt.Fprintln(os.Stderr, "metrics:", metrics.Render())
}
