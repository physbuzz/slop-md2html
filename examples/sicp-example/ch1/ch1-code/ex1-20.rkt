#lang sicp

(define (mod a b)
  (display "yep")
  (newline)
  (remainder a b))
(define (gcd a b)
  (if (= b 0)
      a
      (gcd b (mod a b))))

(gcd 206 40)


