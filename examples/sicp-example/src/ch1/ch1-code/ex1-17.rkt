#lang sicp

(define (double arg) (* arg 2))
(define (halve arg) (/ arg 2))
(define (times a b)
  (display "evaluating times")
  (newline)
  (cond ((= b 0) 0)
        ((= (remainder b 2) 0) (times (double a) (halve b)))
        (else (+ a (times a (- b 1))))))

(times 232 168)
