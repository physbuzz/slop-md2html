#lang sicp

(define (double arg) (* arg 2))
(define (halve arg) (/ arg 2))
(define (times a b)
  (times-inner 0 a b))

(define (times-inner prod a b)
  (cond ((= b 0) prod)
        ((= (remainder b 2) 0) (times-inner prod (double a) (halve b)))
        (else (times-inner (+ a prod) a (- b 1)))))

(times 32 1)
(times 1 32)
(times 32 0)
(times 0 32)
