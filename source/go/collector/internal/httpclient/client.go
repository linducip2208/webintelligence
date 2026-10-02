package httpclient

import (
 "crypto/sha256"
 "encoding/hex"
 "io"
 "net/http"
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
}

type Client struct {
 http *http.Client
 Max  int64
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
 }
}

func (c *Client) Get(url, proxyURL string) (*Response, error) {
 t0 := time.Now()
 req, err := http.NewRequest("GET", url, nil)
 if err != nil {
  return nil, err
 }
 req.Header.Set("User-Agent", "Mozilla/5.0 WebIntel-Collector/1.0")
 resp, err := c.http.Do(req)
 if err != nil {
  return nil, err
 }
 defer resp.Body.Close()
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
 }, nil
}
