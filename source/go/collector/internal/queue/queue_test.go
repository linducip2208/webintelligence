package queue

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

// TestLiveInterop spins up the real MiniRedis (python stdlib RESP server)
// and verifies Push/Pop round-trip over actual TCP.
func TestLiveInterop(t *testing.T) {
	py, err := exec.LookPath("python")
	if err != nil {
		t.Skip("python not available")
	}
	srv := filepath.Join("..", "..", "..", "..", "..", "tests", "integration", "resp_server.py")
	if _, err := os.Stat(srv); err != nil {
		t.Skip("resp_server.py not found")
	}
	// start server inline via a small driver on an ephemeral port
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Skip("no loopback")
	}
	port := ln.Addr().(*net.TCPAddr).Port
	ln.Close()
	drv := fmt.Sprintf(
		"import sys,threading,time; sys.path.insert(0, %q); "+
			"from resp_server import MiniRedis; "+
			"s=MiniRedis(port=%d); threading.Thread(target=s.serve_forever,daemon=True).start(); "+
			"time.sleep(25)",
		filepath.Dir(srv), port)
	cmd := exec.Command(py, "-c", drv)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	if err := cmd.Start(); err != nil {
		t.Skip("cannot start server")
	}
	defer func() { _ = cmd.Process.Kill() }()
	time.Sleep(1500 * time.Millisecond)
	q := New(fmt.Sprintf("127.0.0.1:%d", port), "webintel:queue:jobs")
	if err := q.Push(Job{"job_id": "interop-1"}); err != nil {
		t.Fatalf("push: %v", err)
	}
	job, ok := q.Pop(5)
	if !ok || job["job_id"] != "interop-1" {
		t.Fatalf("pop failed: %v %+v", ok, job)
	}
}
