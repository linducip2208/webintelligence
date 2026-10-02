package proxy

import "sync"

// Provider abstraction: future providers added without touching collection logic.
type Provider interface {
 GetProxy(region string) string
 ReleaseProxy(proxy string, ok bool)
 Healthy() bool
}

type OwnProxy struct {
 mu   sync.Mutex
 urls []string
 i    int
 used map[string]int
}

func NewOwn(urls []string) *OwnProxy { return &OwnProxy{urls: urls, used: map[string]int{}} }

func (o *OwnProxy) GetProxy(region string) string {
 o.mu.Lock()
 defer o.mu.Unlock()
 if len(o.urls) == 0 {
  return ""
 }
 u := o.urls[o.i%len(o.urls)]
 o.i++
 o.used[u]++
 return u
}

func (o *OwnProxy) ReleaseProxy(proxy string, ok bool) {}

func (o *OwnProxy) Healthy() bool { return len(o.urls) > 0 }

// BrightData adapter via super-proxy endpoint; creds from config only.
type BrightData struct {
 Key, Zone string
}

func (b *BrightData) GetProxy(region string) string {
 if b.Key == "" || b.Zone == "" {
  return ""
 }
 return "http://" + b.Zone + ":" + b.Key + "@proxy.brightdata.com:22225"
}

func (b *BrightData) ReleaseProxy(proxy string, ok bool) {}

func (b *BrightData) Healthy() bool { return b.Key != "" && b.Zone != "" }
