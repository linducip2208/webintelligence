// Queue over Redis (minimal RESP client, stdlib only) with in-memory fallback.
package queue

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"strconv"
	"sync"
	"time"
)

type Job map[string]any

type Queue struct {
	mu   sync.Mutex
	mem  []string
	conn net.Conn
	r    *bufio.Reader
	key  string
}

func New(addr, key string) *Queue {
	q := &Queue{key: key}
	c, err := net.DialTimeout("tcp", addr, 3*time.Second)
	if err != nil {
		return q
	}
	q.conn = c
	q.r = bufio.NewReader(c)
	return q
}

func (q *Queue) Push(j Job) error {
	b, _ := json.Marshal(j)
	if q.conn == nil {
		q.mu.Lock()
		q.mem = append(q.mem, string(b))
		q.mu.Unlock()
		return nil
	}
	return q.cmd("RPUSH", q.key, string(b))
}

func (q *Queue) Pop(timeoutSec int) (Job, bool) {
	if q.conn == nil {
		q.mu.Lock()
		defer q.mu.Unlock()
		if len(q.mem) == 0 {
			return nil, false
		}
		raw := q.mem[0]
		q.mem = q.mem[1:]
		var j Job
		_ = json.Unmarshal([]byte(raw), &j)
		return j, true
	}
	_ = q.conn.SetDeadline(time.Now().Add(time.Duration(timeoutSec+2) * time.Second))
	_ = q.cmdRaw("BLPOP", q.key, strconv.Itoa(timeoutSec))
	arr, err := q.readArray()
	if err != nil || len(arr) < 2 {
		return nil, false
	}
	var j Job
	if err := json.Unmarshal([]byte(arr[1]), &j); err != nil {
		return nil, false
	}
	return j, true
}

func (q *Queue) cmd(name string, args ...string) error {
	parts := append([]string{name}, args...)
	fmt.Fprintf(q.conn, "*%d\r\n", len(parts))
	for _, p := range parts {
		fmt.Fprintf(q.conn, "$%d\r\n%s\r\n", len(p), p)
	}
	line, err := q.r.ReadString('\n')
	if err != nil {
		return err
	}
	if len(line) > 0 && line[0] == '-' {
		return fmt.Errorf("redis: %s", line)
	}
	return nil
}

func (q *Queue) cmdRaw(name string, args ...string) error { return q.cmd(name, args...) }

func (q *Queue) readArray() ([]string, error) {
	line, err := q.r.ReadString('\n')
	if err != nil {
		return nil, err
	}
	if len(line) < 2 || line[0] != '*' {
		return nil, fmt.Errorf("expected array")
	}
	n, _ := strconv.Atoi(line[1 : len(line)-2])
	out := []string{}
	for i := 0; i < n; i++ {
		h, err := q.r.ReadString('\n')
		if err != nil {
			return nil, err
		}
		if len(h) < 2 || h[0] != '$' {
			return nil, fmt.Errorf("expected bulk")
		}
		ln, _ := strconv.Atoi(h[1 : len(h)-2])
		if ln < 0 {
			out = append(out, "")
			continue
		}
		buf := make([]byte, ln+2)
		total := 0
		for total < len(buf) {
			m, err := q.r.Read(buf[total:])
			if err != nil {
				return nil, err
			}
			total += m
		}
		out = append(out, string(buf[:ln]))
	}
	return out, nil
}
