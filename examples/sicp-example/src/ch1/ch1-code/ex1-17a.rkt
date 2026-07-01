#lang sicp

(define (double arg) (* arg 2))
(define (halve arg) (/ arg 2))
(define (times a b)
  (cond ((= b 0) 0)
        ((= (remainder b 2) 0) (times (double a) (halve b)))
        (else (+ a (times a (- b 1))))))

(times 32 1)
(times 1 32)
(times 32 0)
(times 0 32)
