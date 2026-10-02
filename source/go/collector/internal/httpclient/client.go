package httpclient

import (
 "crypto/sha256"
 "encoding/hex"
 "io"
 "net/http"
 "net/url"
 "time"
)

type Response struct {
 Status     int
 FinalURL   string
 Size       int
 Hash       string
 Header     http.Header
 Body       []byte
 LatencyMs  float64
 NotModified bool
 ETag       string
 LastMod    string
}

type Client struct {
 http *http.Client
 Max  int64
 UA   string
}

func New(timeoutMs int, maxBody int64) *Client {
 return &Client{
  http: &http.Client{
   Timeout: time.Duration(timeoutMs) * time.Millisecond,
   CheckRedirect: func(req *http.Request, via []*http.Request) error {
    if len(via) > 5 {
     return http.ErrUseLastResponse
    }
    return nil
   },
  },
  Max: maxBody,
  UA:  "Mozilla/5.0 WebIntel-Collector/1.0",
 }
}

func (c *Client) Get(urlStr, proxyURL string) (*Response, error) {
 return c.GetWith(urlStr, proxyURL, map[string]string{})
}

// Plain exposes the underlying client for policy fetches (robots.txt).
func (c *Client) Plain() *http.Client { return c.http }

func (c *Client) GetWith(urlStr, proxyURL string, cond map[string]string) (*Response, error) {
 t0 := time.Now()
 req, err := http.NewRequest("GET", urlStr, nil)
 if err != nil {
  return nil, err
 }
 req.Header.Set("User-Agent", c.UA)
 for k, v := range cond {
  if v != "" {
   req.Header.Set(k, v)
  }
 }
 hc := c.http
 if proxyURL != "" {
  px, err := url.Parse(proxyURL)
  if err == nil {
   tr := &http.Transport{Proxy: http.ProxyURL(px)}
   hc = &http.Client{Timeout: c.http.Timeout, CheckRedirect: c.http.CheckRedirect, Transport: tr}
  }
 }
 resp, err := hc.Do(req)
 if err != nil {
  return nil, err
 }
 defer resp.Body.Close()
 if resp.StatusCode == http.StatusNotModified {
  return &Response{Status: 304, FinalURL: urlStr, NotModified: true,
   LatencyMs: float64(time.Since(t0).Milliseconds())}, nil
 }
 body, err := io.ReadAll(io.LimitReader(resp.Body, c.Max+1))
 if err != nil {
  return nil, err
 }
 h := sha256.Sum256(body)
 return &Response{
  Status:    resp.StatusCode,
  FinalURL:  resp.Request.URL.String(),
  Size:      len(body),
  Hash:      hex.EncodeToString(h[:]),
  Header:    resp.Header,
  Body:      body,
  LatencyMs: float64(time.Since(t0).Milliseconds()),
  ETag:      resp.Header.Get("ETag"),
  LastMod:   resp.Header.Get("Last-Modified"),
 }, nil
}
