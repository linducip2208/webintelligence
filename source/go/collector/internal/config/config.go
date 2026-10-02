package config

import "os"

type Config struct {
 RedisAddr   string
 Queue       string
 Workers     int
 TimeoutMs   int
 MaxBody     int64
 BrightKey   string
 BrightZone  string
 OwnProxies  []string
 APIBase     string
 APIToken    string
 UserAgent   string
}

func Load() Config {
 return Config{
  RedisAddr:  getenv("REDIS_ADDR", "127.0.0.1:6379"),
  Queue:      getenv("QUEUE", "webintel:queue:jobs"),
  Workers:    16,
  TimeoutMs:  30000,
  MaxBody:    10 << 20,
  BrightKey:  os.Getenv("BRIGHTDATA_API_KEY"),
  BrightZone: os.Getenv("BRIGHTDATA_ZONE"),
  OwnProxies: split(os.Getenv("OWN_PROXY_URLS")),
  APIBase:    getenv("API_BASE", "http://127.0.0.1:8000"),
  APIToken:   os.Getenv("API_TOKEN"),
  UserAgent:  getenv("COLLECTOR_UA", "Mozilla/5.0 WebIntel-Collector/1.0"),
 }
}

func getenv(k, d string) string {
 if v := os.Getenv(k); v != "" {
  return v
 }
 return d
}

func split(s string) []string {
 if s == "" {
  return nil
 }
 var out []string
 cur := ""
 for _, c := range s {
  if c == ',' {
   if cur != "" {
    out = append(out, cur)
   }
   cur = ""
  } else {
   cur += string(c)
  }
 }
 if cur != "" {
  out = append(out, cur)
 }
 return out
}
